# Build Plan

- [x] 1. **Streaming SSE real** - endpoint /explain conectado al LLM real,
      streameando la respuesta por SSE (aún sin estructura validada, solo
      demostrar que el mecanismo de streaming funciona end to end)
- [x] 2. **Structured output con Pydantic** - la respuesta se emite como
      eventos por campo y se valida contra el esquema ExplainResponse
      (resumen, complejidad, posibles_bugs, sugerencia) al cerrar el stream
- [x] 3. **Rate limiting y retries con backoff exponencial** - manejo de
      errores 429/5xx del proveedor LLM con reintentos automáticos
- [x] 4. **Tracking de costo por request** - cálculo de tokens in/out ×
      precio del modelo, expuesto en la respuesta o en logs
- [x] 5. **Prompts versionados (v1-v3) con changelog** - tres iteraciones
      del prompt base con CHANGELOG.md explicando el motivo de cada cambio