# Arquitectura del AI Gateway

## Contexto (C4)

```mermaid
flowchart LR
    A[Apps · Agentes · Asistentes] -->|POST /v1/chat/completions| GW
    GW[[AI Gateway]] -->|API estándar| P1[Azure OpenAI]
    GW -->|Bedrock| P2[AWS Bedrock]
    GW -->|Chat Completions| P3[OpenAI]
    GW -->|Messages| P4[Anthropic]
    GW -->|Lab interno| P5[Kiro]
    GW --> R[(Redis)]
    GW --> OTL[OpenTelemetry]
```

## Flujo de una petición

```mermaid
sequenceDiagram
    participant App as Aplicación
    participant GW as Gateway
    participant R as Router
    participant AZ as Azure OpenAI
    participant AN as Anthropic

    App->>GW: POST /v1/chat/completions (model=claude-sonnet-4.5)
    GW->>GW: Auth (API key) → Rate limit → Cache lookup
    Note over R: estrategia cost_quality → orden: [anthropic, aws_bedrock]
    GW->>R: plan(model)
    R->>AN: intento 1 (anthropic)
    AN-->>R: ok (latency, tokens)
    R-->>GW: resultado + costo USD
    GW-->>App: 200 OpenAI-compatible
```

## Componentes (C3)

| Componente | Responsabilidad |
|------------|-----------------|
| `main.py` | Contrato HTTP único / modelo de transporte |
| `core/router.py` | Estrategia de ruteo, fallback y cuarentena |
| `providers/*` | Adaptadores (Ports & Adapters sobre el consumo de LLMs) |
| `middleware/rate_limit` | Ventana deslizante Redis |
| `middleware/cache` | Deduplicación de costo por petición |
| `middleware/cost` | Ledger FinOps (USD por modelo/cliente) |
| `middleware/auth` | API keys y (futuro) OAuth2 / Entra ID |

## Características transversales

- **Trazabilidad**: OpenTelemetry con [semconv GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/) (span por provider, tokens, costo).
- **Seguridad**: nunca se exponen las claves de proveedores; el gateway es el único puerto.
- **Gobernanza**: el catálogo de modelos está en `config/models.yaml` (versionado, revisado en PR).