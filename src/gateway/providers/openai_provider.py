"""Proveedor OpenAI (chat completions)."""
from __future__ import annotations

from src.gateway.providers.base import ChatRequest, ChatResult, Provider, ProviderError


class OpenAIProvider(Provider):
    name = "openai"

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1") -> None:
        super().__init__()
        self.api_key = api_key
        self.base_url = base_url

    async def chat(self, req: ChatRequest) -> ChatResult:
        resp = await self.client.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": req.model,
                "messages": req.messages,
                "temperature": req.temperature,
                "max_tokens": req.max_tokens,
                "tools": req.tools,
            },
        )
        if resp.status_code >= 400:
            raise ProviderError(f"openai {resp.status_code}: {resp.text[:200]}")
        data = resp.json()
        choice = data["choices"][0]
        usage = data.get("usage", {})
        return ChatResult(
            provider=self.name,
            model=req.model,
            content=choice["message"]["content"] or "",
            latency_ms=int(resp.elapsed.total_seconds() * 1000),
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            raw=data,
        )