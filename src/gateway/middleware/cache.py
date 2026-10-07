"""Caché de respuestas por hash de (modelo + mensajes). Evita costo duplicado."""
from __future__ import annotations

import hashlib
import json

from src.gateway.providers.base import ChatResult


class ResponseCache:
    def __init__(self, redis=None, ttl: int = 300) -> None:
        self.redis = redis
        self.ttl = ttl
        self._mem: dict[str, tuple[float, ChatResult]] = {}

    @staticmethod
    def key(model: str, messages: list[dict]) -> str:
        payload = json.dumps([model, messages], sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(payload.encode()).hexdigest()

    async def get(self, model: str, messages: list[dict]) -> ChatResult | None:
        k = self.key(model, messages)
        if self.redis:
            raw = await self.redis.get(k)
            return ChatResult(**json.loads(raw)) if raw else None
        hit = self._mem.get(k)
        if hit:
            ts, result = hit
            if time.monotonic() - ts < self.ttl:
                return result
        return None

    async def set(self, model: str, messages: list[dict], result: ChatResult) -> None:
        k = self.key(model, messages)
        if self.redis:
            await self.redis.set(k, json.dumps(result.__dict__), ex=self.ttl)
        else:
            self._mem[k] = (time.monotonic(), result)