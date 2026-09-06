# Project Plan

> CodeSage se construye en 4 fases (roadmap completo en `blueprint/roadmap.md`).
> Este documento describe el alcance de la fase activa: **Fase 2 - RAG end to
> end**. Fase 1 (streaming, structured output, retries, costos, prompts
> versionados) está completa y archivada en `blueprint/history/features/`.

## 1. Problem - What problem are we solving?
Falta una forma rápida y explicable de entender un fragmento de código ajeno:
qué hace, qué tan complejo es, dónde puede fallar, y cómo mejorarlo. CodeSage
resuelve esto exponiendo esa explicación como un servicio, en streaming, con
salida estructurada verificable (no texto libre).

## 2. Users - Who is this for?
Uso propio como pieza central del portafolio de transición a AI Engineer, y
como demo técnica para entrevistas: demuestra manejo de streaming real,
structured output, resiliencia ante fallos de API, control de costos y
versionado de prompts en un entorno productivo.

## 3. Features - What does the MVP need?

**Fase 1 (completa):**
- Endpoint que recibe un fragmento de código + una pregunta
- Respuesta en streaming real vía SSE (Server-Sent Events), no simulada
- El streaming se estructura como eventos por campo (`event: resumen`,
  `event: complejidad`, `event: posibles_bugs`, `event: sugerencia`), cada
  uno validable individualmente; el objeto completo se valida con Pydantic
  al cerrar el stream
- Manejo de rate limits del proveedor LLM con reintentos y backoff exponencial
- Cálculo de costo por request a partir de tokens de entrada/salida x precio
  del modelo usado
- Al menos 3 versiones de prompt (v1, v2, v3) con un changelog que explique
  el motivo de cada cambio

**Fase 2 (activa) - RAG sobre un repositorio real:**
- Fallback funcional entre al menos dos proveedores de LLM (OpenAI <-> Anthropic)
  ante fallos o rate limits; heredado de Fase 1, primer item de esta fase
- Ingesta de un repositorio open source (5k+ líneas de código + documentación)
- Chunking especializado: por función/clase para código, semántico para
  documentación, con la diferencia de estrategia documentada
- Hybrid search: retrieval semántico (pgvector) combinado con búsqueda por
  keyword (nombre de función, nombre de archivo)
- Re-ranking de resultados antes de pasarlos al LLM para generación
- Citación de fuente exacta (archivo + línea) en cada respuesta generada
- Caso documentado de un fallo de RAG (retrieval irrelevante, chunk malo o
  contexto desbordado), su diagnóstico y la corrección aplicada

## 4. Data - What are we storing?
No hay persistencia de usuarios en esta fase. Fase 1 registra en logs (o en
la respuesta misma) el costo por request y la versión de prompt usada. Fase 2
añade persistencia real: embeddings y metadata (archivo, línea, tipo de
chunk) de los chunks ingeridos del repositorio, en Postgres con pgvector.

## 5. Tech - What stack are we using?
Python, FastAPI, Pydantic para validación de esquemas, httpx o el SDK oficial
del proveedor LLM para las llamadas, tenacity (o lógica manual) para
retries/backoff, pytest para pruebas. Fase 2 añade Postgres + pgvector como
vector store, un modelo de embeddings, y lógica de chunking/hybrid
search/re-ranking sobre el pipeline de RAG.

## 6. Monetize - How will this make money?
No es un producto comercial en esta fase. Su valor es como pieza de
portafolio (CodeSage) y como práctica aplicada del roadmap de AI Engineer.

## 7. UI/UX - How should this look and feel?
No aplica interfaz visual: es un microservicio backend. La "experiencia" a
optimizar es la del consumidor de la API — respuesta rápida en el primer
byte (streaming), errores claros, y contrato JSON estable y predecible.

## 8. Deployment - Where and how will this ship?
Fuera de alcance hasta Fase 4. Fase 1 y Fase 2 se validan localmente
(`uvicorn` + Postgres/pgvector local + pruebas manuales y automatizadas). El
entregable de Fase 2 incluye una demo desplegada del pipeline de RAG (no
producción); el deployment formal en AWS con CI/CD es el entregable de
Fase 4 (ver `blueprint/roadmap.md`).