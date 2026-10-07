# Contributing

- Estilo: usa [`ruff`](https://docs.astral.sh/ruff/) (`ruff check src tests`).
- Tests: `pytest -q` debe pasar en local y en CI.
- Nuevo proveedor = nuevo adaptador en `src/gateway/providers/` + registro
  en `_build_router()` + entrada en `config/models.yaml`.
- Cambios de contrato público (endpoints) → ADR en `docs/`.