"""Pruebas del router: estrategia, cuarentena y fallback."""
import pytest

from src.gateway.core.router import Router, RouterConfig
from src.gateway.providers.base import ChatRequest, ChatResult, Provider, ProviderError


class OkProvider(Provider):
    name = "ok"

    async def chat(self, req):
        return ChatResult(provider=self.name, model=req.model, content="pong ok",
                          latency_ms=10, input_tokens=5, output_tokens=5)


class FlakyProvider(Provider):
    name = "flaky"
    fail_first: bool = True

    async def chat(self, req):
        if self.fail_first:
            self.fail_first = False
            raise ProviderError("boom")
        return ChatResult(provider=self.name, model=req.model, content="pong flaky",
                          latency_ms=10, input_tokens=5, output_tokens=5)


@pytest.mark.asyncio
async def test_fallback_cuando_no_falla_el_primero():
    flaky = FlakyProvider()
    ok = OkProvider()
    r = Router(RouterConfig(strategy="fallback", max_attempts=3, quarantine_seconds=0))
    r.register(flaky)
    r.register(ok)
    r.set_fallbacks("m1", ["flaky", "ok"])

    res = await r.chat(ChatRequest(model="m1", messages=[{"role": "user", "content": "hi"}]))
    assert res.provider == "ok" or res.content == "pong ok"


@pytest.mark.asyncio
async def test_cuarentena_salta_proveedor_fallido():
    flaky = FlakyProvider()
    ok = OkProvider()
    r = Router(RouterConfig(strategy="cost_quality", max_attempts=2, quarantine_seconds=0))
    r.register(flaky, cost_in=0.1)
    r.register(ok, cost_in=0.01)
    r.set_fallbacks("m1", ["flaky", "ok"])

    res = await r.chat(ChatRequest(model="m1", messages=[]))
    assert res.provider == "ok"


@pytest.mark.asyncio
async def test_router_calcula_costo_finops():
    ok = OkProvider()
    r = Router(RouterConfig(strategy="fallback", max_attempts=1))
    r.register(ok, cost_in=0.001, cost_out=0.002)
    res = await r.chat(ChatRequest(model="m1", messages=[]))
    assert res.cost_usd == pytest.approx(5 / 1000 * 0.001 + 5 / 1000 * 0.002)