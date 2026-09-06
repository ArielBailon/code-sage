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

<!-- Fase 2 - RAG end to end (ver blueprint/roadmap.md) -->

- [ ] 6. **Fallback entre proveedores de LLM** - si el proveedor activo falla
      o da rate limit (429/5xx no recuperable con retries), cae
      automáticamente al otro proveedor (OpenAI <-> Anthropic); heredado del
      entregable de Fase 1, primer item de Fase 2
- [ ] 7. **Ingesta y chunking especializado** - clona un repositorio open
      source real (5k+ líneas de código + documentación) e implementa
      chunking por función/clase para código vs. chunking semántico para
      documentación, documentando la diferencia de estrategia
- [ ] 8. **Hybrid search con pgvector** - retrieval que combina búsqueda
      semántica (pgvector) con búsqueda por keyword (nombre de función,
      nombre de archivo)
- [ ] 9. **Re-ranking de resultados** - reordena los resultados de retrieval
      antes de pasarlos al LLM para generación
- [ ] 10. **Citación de fuente exacta** - cada respuesta generada cita el
      archivo y la línea de donde proviene la información
- [ ] 11. **Caso documentado de "RAG que falló"** - un fallo real de
      retrieval o generación, su diagnóstico y la corrección aplicada
- [ ] 12. **Demo y post de cierre de Fase 2** - demo desplegada del pipeline
      de RAG y post explicando las decisiones de chunking (código vs.
      documentación)