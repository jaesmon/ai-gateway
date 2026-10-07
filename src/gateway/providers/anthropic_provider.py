"""Proveedor Anthropic (messages API)."""
from __future__ import annotations

from src.gateway.providers.base import ChatRequest, ChatResult, Provider, ProviderError


class AnthropicProvider(Provider):
    name = "anthropic"

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com/v1") -> None:
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url

    async def chat(self, req: ChatRequest) -> ChatResult:
        resp = await self.client.post(
            f"{self.base_url}/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": req.model,
                "messages": req.messages,
                "max_tokens": req.max_tokens or 1024,
                "temperature": req.temperature,
                "tools": req.tools,
            },
        )
        if resp.status_code >= 400:
            raise ProviderError(f"anthropic {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        text = "".join(b.get("text", "") for b in data.get("content", []) if b["type"] == "text")
        usage = data.get("usage", {})
        return ChatResult(
            provider=self.name,
            model=req.model,
            content=text,
            latency_ms=int(resp.elapsed.total_seconds() * 1000),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            raw=data,
        )