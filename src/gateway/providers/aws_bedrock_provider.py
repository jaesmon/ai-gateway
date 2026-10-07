"""Proveedor AWS Bedrock (Converse API). Requiere credenciales AWS y boto3."""
from __future__ import annotations

import boto3

from src.gateway.providers.base import ChatRequest, ChatResult, Provider, ProviderError


class BedrockProvider(Provider):
    name = "aws_bedrock"

    def __init__(self, region: str) -> None:
        super().__init__()
        self.client = boto3.client("bedrock-runtime", region_name=region)

    async def chat(self, req: ChatRequest) -> ChatResult:
        messages = [
            {"role": m["role"], "content": [{"text": m.get("content", "")}]}
            for m in req.messages
        ]
        try:
            resp = self.client.converse(
                modelId=req.model,
                messages=messages,
                inferenceConfig={
                    "maxTokens": req.max_tokens or 1024,
                    "temperature": req.temperature,
                },
            )
        except Exception as e:  # noqa: BLE001 — traducir errores AWS al dominio del gateway
            raise ProviderError(f"bedrock: {e}") from e

        out = resp.get("output", {})
        usage = resp.get("usage", {})
        return ChatResult(
            provider=self.name,
            model=req.model,
            content=(out.get("message") or {}).get("content", [{}])[0].get("text", ""),
            latency_ms=-1,
            input_tokens=usage.get("inputTokens", 0),
            output_tokens=usage.get("outputTokens", 0),
            raw=resp,
        )