# AI Gateway

> Gateway empresarial de LLMs: una API **única y estable** (OpenAI/Anthropic-compatible) sobre múltiples proveedores (Azure, AWS Bedrock, OpenAI, Anthropic, y labs locales como Kiro). Ruteo inteligente, fallbacks, rate limiting, caché y control de costos.

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB)](https://python.org)

## ¿Por qué un gateway de IA?

Las apps que llaman modelos directamente se atan a un proveedor y pierden viento de cola:

- **Cambiar de proveedor** = reescribir integraciones.
- **Sin fallback**: una caída de un proveedor tumba la app.
- **Sin gobierno**: costos sin control, sin límites, sin trazabilidad.
- **Sin portabilidad**: cada equipo reinventa la rueda.

Un gateway centraliza **autenticación, ruteo, resiliencia, observabilidad y FinOps** del consumo de modelos.

## Arquitectura

```mermaid
flowchart LR
    Client[Apps / Agentes / SDKs] -->|OpenAI-compatible| GW[AI Gateway]
    GW --> MID[Middleware<br/>Auth · Router · Rate Limit · Cache · Cost]
    MID --> P1[Azure OpenAI]
    MID --> P2[AWS Bedrock]
    MID --> P3[OpenAI]
    MID --> P4[Anthropic]
    MID --> P5[Kiro / labs locales]
    GW --> REDIS[(Redis<br/>rate-limit, cache)]
    GW --> OBS[(OpenTelemetry<br/>GenAI semconv)]
```

## Estructura

```
ai-gateway/
├── config/
│   ├── gateway.yaml          # políticas de ruteo y límites
│   └── models.yaml           # catálogo de modelos y sus proveedores
├── src/gateway/
│   ├── main.py               # app FastAPI (endpoints /v1)
│   ├── core/
│   │   └── router.py         # selección de proveedor + fallback
│   ├── providers/            # adaptadores por proveedor
│   │   ├── base.py
│   │   ├── openai_provider.py
│   │   ├── anthropic_provider.py
│   │   ├── azure_provider.py
│   │   ├── aws_bedrock_provider.py
│   │   └── kiro_provider.py
│   └── middleware/           # auth, rate-limit, cache, cost
├── tests/
├── docker-compose.yml        # gateway + redis
├── .env.example
└── requirements.txt
```

## Quickstart

```bash
cp .env.example .env      # agrega tus API keys
pip install -r requirements.txt
uvicorn src.gateway.main:app --port 8000

curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $GW_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "model": "claude-sonnet-4.5", "messages": [{"role":"user","content":"Hola"}] }'
```

La app ignora lógica de proveedor; solo se configura (ver [docs/routing-strategies.md](docs/routing-strategies.md)).

## Decisiones clave (ADR)

| ADR | Decisión |
|-----|----------|
| [ADR-0001](docs/ADR-0001-unified-llm-api.md) | API unificada para desacoplar apps del proveedor |

## Licencia

MIT — ver [LICENSE](LICENSE).