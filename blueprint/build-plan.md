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

- [ ] 6. **Ingesta y chunking especializado** - clona un repositorio open
      source real (5k+ líneas de código + documentación) e implementa
      chunking por función/clase para código vs. chunking semántico para
      documentación, documentando la diferencia de estrategia
- [ ] 7. **Hybrid search con pgvector** - retrieval que combina búsqueda
      semántica (pgvector) con búsqueda por keyword (nombre de función,
      nombre de archivo)
- [ ] 8. **Re-ranking de resultados** - reordena los resultados de retrieval
      antes de pasarlos al LLM para generación
- [ ] 9. **Citación de fuente exacta** - cada respuesta generada cita el
      archivo y la línea de donde proviene la información
- [ ] 10. **Caso documentado de "RAG que falló"** - un fallo real de
      retrieval o generación, su diagnóstico y la corrección aplicada
- [ ] 11. **Demo y post de cierre de Fase 2** - demo desplegada del pipeline
      de RAG y post explicando las decisiones de chunking (código vs.
      documentación)

<!-- Fase 5 (extra) - Fallback multi-proveedor de LLM (ver blueprint/roadmap.md) -->

- [ ] 12. **Cliente OpenAI con streaming y retries** - módulo que replica la
      interfaz del cliente Anthropic existente (stream + reporte de usage),
      con el mismo manejo de retries/backoff en 429/5xx; incluye el pricing
      de modelos OpenAI en el cálculo de costo
- [ ] 13. **Fallback automático entre proveedores** - si el proveedor
      primario agota reintentos sin haber emitido ningún chunk todavía, cae
      automáticamente al proveedor secundario (OpenAI <-> Anthropic) para
      ese mismo request, con selección de proveedor por variables de entorno