"""Rate limit con ventana deslizante sobre Redis (fallback en memoria)."""
from __future__ import annotations

import time


class RateLimiter:
    def __init__(self, per_minute: int = 60, redis=None) -> None:
        self.per_minute = per_minute
        self.redis = redis
        self._mem: dict[str, list[float]] = {}

    async def _count(self, key: str) -> bool:
        """Devuelve True si el cliente excede el límite."""
        if self.redis:
            n = await self.redis.incr(key)
            if n == 1:
                await self.redis.expire(key, 60)
            return n > self.per_minute
        now = time.monotonic()
        bucket = [t for t in self._mem.get(key, []) if now - t < 60]
        bucket.append(now)
        self._mem[key] = bucket
        return len(bucket) > self.per_minute

    async def check(self, client: str) -> None:
        if await self._count(f"rl:{client}"):
            from fastapi import HTTPException
            raise HTTPException(429, "Límite de peticiones excedido")