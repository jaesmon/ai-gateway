"""AI Gateway — API unificada OpenAI-compatible."""
from __future__ import annotations

import os

import yaml
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from src.gateway.core.router import Router, RouterConfig
from src.gateway.middleware.auth import ApiKeyAuth
from src.gateway.middleware.cache import ResponseCache
from src.gateway.middleware.cost import CostLedger
from src.gateway.middleware.rate_limit import RateLimiter
from src.gateway.providers.anthropic_provider import AnthropicProvider
from src.gateway.providers.aws_bedrock_provider import BedrockProvider
from src.gateway.providers.azure_provider import AzureOpenAIProvider
from src.gateway.providers.base import ChatRequest, ProviderError
from src.gateway.providers.kiro_provider import KiroProvider
from src.gateway.providers.openai_provider import OpenAIProvider

app = FastAPI(title="AI Gateway", version="1.0.0")


class ChatCompletionRequest(BaseModel):
    model: str = Field(..., description="Modelo del catálogo config/models.yaml")
    messages: list[dict]
    temperature: float = 0.7
    max_tokens: int | None = None
    tools: list[dict] | None = None


def _load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _build_router() -> Router:
    cfg = _load_config("config/gateway.yaml")
    models = _load_config("config/models.yaml")["models"]
    gateway = cfg["gateway"]
    router = Router(RouterConfig(
        strategy=gateway.get("default_strategy", "cost_quality"),
        max_attempts=gateway.get("max_attempts", 3),
    ))

    providers = cfg["providers"]
    routing = cfg.get("routing", {})

    by_name = {
        "azure": AzureOpenAIProvider(
            endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-10-21"),
        ),
        "aws_bedrock": BedrockProvider(region=os.environ.get("AWS_REGION", "us-east-1")),
        "openai": OpenAIProvider(api_key=os.environ["OPENAI_API_KEY"]),
        "anthropic": AnthropicProvider(api_key=os.environ["ANTHROPIC_API_KEY"]),
        "kiro": KiroProvider(),
    }
    for name, p in by_name.items():
        if providers.get(name, {}).get("enabled", False):
            router.register(
                p,
                weight=providers[name].get("weight", 1),
                cost_in=providers[name].get("cost_per_1k_input", 0.0),
                cost_out=providers[name].get("cost_per_1k_output", 0.0),
            )

    for m in models:
        router.set_fallbacks(m["id"], m["providers"])
    return router


router = _build_router()
rate_limiter = RateLimiter(per_minute=60)
cache = ResponseCache()
ledger = CostLedger()
auth = ApiKeyAuth()


@app.post("/v1/chat/completions")
async def chat_completions(
    body: ChatCompletionRequest,
    client: dict = Depends(auth),
):
    await rate_limiter.check(client["client"])

    cached = await cache.get(body.model, body.messages)
    if cached:
        return _openai_response(cached)

    try:
        result = await router.chat(ChatRequest(
            model=body.model,
            messages=body.messages,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
            tools=body.tools,
        ))
    except ProviderError as e:
        raise HTTPException(502, f"Sin proveedores disponibles: {e}") from e

    ledger.record(client["client"], body.model, result)
    await cache.set(body.model, body.messages, result)
    return _openai_response(result)


@app.get("/v1/models")
async def list_models():
    return {"object": "list", "data": [{"id": m["id"]} for m in _load_config("config/models.yaml")["models"]]}


@app.get("/admin/costs")
async def costs(client: dict = Depends(auth)):
    return ledger.snapshot()


def _openai_response(r):
    return {
        "id": f"chatcmpl-{r.provider}",
        "object": "chat.completion",
        "model": r.model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": r.content}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": r.input_tokens, "completion_tokens": r.output_tokens},
        "_gateway": {"provider": r.provider, "latency_ms": r.latency_ms, "cost_usd": r.cost_usd},
    }