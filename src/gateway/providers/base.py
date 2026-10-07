"""Adaptadores por proveedor (Ports & Adapters del consumo de LLMs)."""
from __future__ import annotations

from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import httpx


@dataclass
class ChatResult:
    provider: str
    model: str
    content: str
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    raw: dict = field(default_factory=dict)


@dataclass
class ChatRequest:
    model: str
    messages: list[dict]
    temperature: float = 0.7
    max_tokens: int | None = None
    tools: list[dict] | None = None


class Provider(ABC):
    name: str

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self.client = client or httpx.AsyncClient(timeout=60.0)

    @abstractmethod
    async def chat(self, req: ChatRequest) -> ChatResult:
        """Ejecuta una conversación. Lanza ProviderError si falla."""

    async def close(self) -> None:
        await self.client.aclose()


class ProviderError(RuntimeError):
    """Indica que el proveedor falló y el router debe intentar otro."""