# ADR-0001 — API de LLM unificada (OpenAI-compatible)

- **Estado:** Aceptado
- **Fecha:** 2026-02

## Contexto

Cada equipo integraba proveedores de modelos directamente; cambiar de proveedor
reescribía capas de la app y los costos eran invisibles.

## Decisión

El gateway expone **una sola API** (`/v1/chat/completions`, compatible con
OpenAI) y traduce internamente a Azure, Bedrock, Anthropic, etc. Las apps no
conocen ni el proveedor ni el modelo concreto salvo por el id del catálogo.

## Consecuencias

- ✅ Portabilidad total: rotar proveedor = cambiar una línea de `models.yaml`.
- ✅ Un solo punto de gobierno: auth, límites, costo, telemetría.
- ⚠️ Se sacrifica acceso a features exclusivas (luego se liberan vía `/v1/messages` y campos opt-in).

## Alternativas consideradas

- **Orientarse al proveedor "más rico":** rechazado (acopla el contrato público).
- **Dos APIs paralelas (OpenAI + Anthropic):** implementado como complemento
  sin duplicar negocio (mismos middleware).