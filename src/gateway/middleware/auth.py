"""autenticación simple vía API key + límites por cliente."""
from __future__ import annotations

import os

from fastapi import Header, HTTPException


class ApiKeyAuth:
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GW_API_KEY", "change-me")

    async def __call__(self, authorization: str | None = Header(default=None)) -> dict:
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "Falta el header Authorization")
        token = authorization.removeprefix("Bearer ")
        if token != self.api_key:
            raise HTTPException(401, "API key inválida")
        return {"client": "internal"}