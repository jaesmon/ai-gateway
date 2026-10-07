"""Router: elige proveedor por estrategia y ejecuta fallbacks."""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from src.gateway.providers.base import ChatRequest, ChatResult, Provider, ProviderError


@dataclass
class RouterConfig:
    strategy: str = "cost_quality"       # cost_quality | latency | fallback | round_robin
    max_attempts: int = 3
    quarantine_seconds: int = 60


@dataclass
class ProviderRef:
    provider: Provider
    weight: float = 1.0
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    fallback_until: float = 0.0


class Router:
    """Pick del proveedor primario + cadena de fallback con cuarentena."""

    def __init__(self, cfg: RouterConfig) -> None:
        self.cfg = cfg
        self.refs: dict[str, ProviderRef] = {}
        self.fallbacks: dict[str, list[str]] = {}
        self.rr_index: dict[str, int] = {}

    def register(self, provider: Provider, weight: float = 1.0,
                 cost_in: float = 0.0, cost_out: float = 0.0) -> None:
        self.refs[provider.name] = ProviderRef(provider, weight, cost_in, cost_out)

    def set_fallbacks(self, model: str, order: list[str]) -> None:
        self.fallbacks[model] = order

    def plan(self, model: str) -> list[ProviderRef]:
        order = self.fallbacks.get(model, list(self.refs.keys()))
        now = time.monotonic()
        refs = [self.refs[p] for p in order if p in self.refs]
        refs = [r for r in refs if r.fallback_until <= now]
        if not refs:
            raise ProviderError(f"Todos los proveedores de {model!r} están en cuarentena")
        return refs

    def _pick_primary(self, refs: list[ProviderRef]) -> list[ProviderRef]:
        if self.cfg.strategy == "cost_quality":
            refs = sorted(refs, key=lambda r: r.cost_per_1k_input)  # más barato primero
        elif self.cfg.strategy == "latency":
            refs = sorted(refs, key=lambda r: r.provider.name)  # proxy real: metricas de latencia
        return refs

    async def chat(self, req: ChatRequest) -> ChatResult:
        plan = self._pick_primary(self.plan(req.model))
        last_err: Exception | None = None

        for ref in plan[: self.cfg.max_attempts]:
            try:
                result = await ref.provider.chat(req)
                # Estimar costo (FinOps): input+output → USD
                ref.cost_per_1k_input = max(ref.cost_per_1k_input, 1e-9)
                result.cost_usd = (
                    result.input_tokens / 1000 * ref.cost_per_1k_input
                    + result.output_tokens / 1000 * ref.cost_per_1k_output
                )
                return result
            except ProviderError as e:
                last_err = e
                ref.fallback_until = time.monotonic() + self.cfg.quarantine_seconds
                continue
        raise ProviderError(f"Fallaron todos los intentos: {last_err}")