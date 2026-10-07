"""Proveedor Kiro (labs internos / experimentación).

Kiro expone modelos (Claude, DeepSeek, Qwen...) que este gateway normaliza
bajo una API estándar. Proyecto de experimentación interna: verifica siempre
los términos de servicio antes de exponerlo fuera del entorno controlado.
"""
from __future__ import annotations

import os

from src.gateway.providers.anthropic_provider import AnthropicProvider


class KiroProvider(AnthropicProvider):
    """Implementación de referencia para gateways de laboratorio.

    Kiro habla una variante del protocolo Anthropic; reutilizamos el adaptador
    Anthropic parametrizando el endpoint. El token se refresca/automatiza por
    debajo (recomendado: kiro-cli en modo ACP, conforme a ToS).
    """

    name = "kiro"

    def __init__(self, base_url: str = "", api_key: str = "") -> None:
        base_url = base_url or os.getenv("KIRO_BASE_URL", "http://localhost:8086")
        api_key = api_key or os.getenv("KIRO_REFRESH_TOKEN", "local-lab")
        super().__init__(api_key=api_key, base_url=base_url)