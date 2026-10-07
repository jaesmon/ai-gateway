"""Proveedor Azure OpenAI: misma API de OpenAI con endpoint gestionado."""
from __future__ import annotations

from src.gateway.providers.openai_provider import OpenAIProvider


class AzureOpenAIProvider(OpenAIProvider):
    name = "azure"

    def __init__(self, endpoint: str, api_key: str, api_version: str) -> None:
        self.api_key = api_key
        self.api_version = api_version
        # Azure usa paths por deployment: /openai/deployments/{model}/chat/completions
        self.deployment_base = f"{endpoint}/openai/deployments"

    async def chat(self, req):
        from src.gateway.providers.base import ChatResult
        url = f"{self.deployment_base}/{req.model}/chat/completions?api-version={self.api_version}"
        resp = await self.client.post(
            url,
            headers={"api-key": self.api_key},
            json={
                "messages": req.messages,
                "temperature": req.temperature,
                "max_tokens": req.max_tokens,
                "tools": req.tools,
            },
        )
        data = resp.json()
        if resp.status_code >= 400:
            raise RuntimeError(f"azure {resp.status_code}: {data}")
        usage = data.get("usage", {})
        return ChatResult(
            provider=self.name,
            model=req.model,
            content=data["choices"][0]["message"]["content"] or "",
            latency_ms=int(resp.elapsed.total_seconds() * 1000),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            raw=data,
        )