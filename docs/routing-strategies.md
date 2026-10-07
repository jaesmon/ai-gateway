# Estrategias de ruteo

## `fallback`

Orden estático por modelo. Se usa para disponibilidad: si el primario falla, se
prueba el siguiente. Indicado para apps críticas.

```yaml
routing:
  fallbacks:
    claude-sonnet-4.5:
      - anthropic
      - aws_bedrock
```

## `cost_quality` (recomendada)

Se ordenan los proveedores disponibles por **costo por 1k tokens de entrada**;
el más barato que cumpla la calidad esperada responde primero. Ideal para
páginas de LLM con mucha repetición de patrones.

## `latency`

Prioriza el proveedor con menor latencia observada (métricas del ledger → Prometheus).

## `round_robin`

Distribuye carga para quemar cuotas/slots equilibradamente (útil en labs con
cuentas de experimentación, p. ej. Kiro).

## Cuarentena (resiliencia)

Un proveedor que falla entra en `quarantine_seconds` y se salta en las siguientes
peticiones. Si el fallo es global (500/429 sostenido), el router no lo vuelve a
intentar hasta que el período expire.

## Economía (FinOps para IA)

Cada resultado reporta `cost_usd` (input+output) calculado con el catálogo de
`config/models.yaml`. El endpoint `/admin/costs` expone el **ledger por modelo y
por cliente** — base para presupuestos por célula de desarrollo y alarms de gasto.

## Caché semántica / exacta

La caché exacta (hash de mensajes) elimina repeticiones. Para consultas de
soporte/documentación, 300s de TTL reduce el gasto hasta ~40% sin degradar UX.