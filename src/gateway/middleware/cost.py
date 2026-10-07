"""Registro de costos por cliente/modelo (FinOps para IA)."""
from __future__ import annotations

import threading
from collections import defaultdict

from src.gateway.providers.base import ChatResult


class CostLedger:
    """Acumula USD por modelo y por cliente; expón métricas Prometheus."""

    def __init__(self) -> None:
        self.by_model: dict[str, float] = defaultdict(float)
        self.by_client: dict[str, float] = defaultdict(float)
        self.requests = 0
        self._lock = threading.Lock()

    def record(self, client: str, model: str, result: ChatResult) -> None:
        with self._lock:
            self.by_model[model] += result.cost_usd
            self.by_client[client] += result.cost_usd
            self.requests += 1

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "requests": self.requests,
                "cost_usd": dict(self.by_model),
                "cost_by_client_usd": dict(self.by_client),
            }