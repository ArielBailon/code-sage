# Roadmap - AI Engineer Transition (CodeSage)

> Fuente maestra de las 4 fases del roadmap personal de transición a AI
> Engineer, con CodeSage como proyecto central de portafolio. Este archivo no
> lo lee el Blueprint automáticamente: es la referencia desde la que se
> actualizan a mano `blueprint/project-plan.md` y `blueprint/build-plan.md`
> cada vez que arranca una fase nueva.

## Cómo avanzar de fase

1. Confirmar que el 📦 Entregable de la fase activa está completo en
   `blueprint/build-plan.md` (todos los items marcados).
2. Crear un tag de git sobre `main`: `git tag fase-N-completa` (N = número de
   fase que se cierra).
3. Actualizar `blueprint/project-plan.md` (secciones Features, Tech y
   Deployment) para reflejar el alcance de la fase que arranca, tomando el
   entregable correspondiente de este archivo.
4. Añadir al final de `blueprint/build-plan.md` los items del 📦 Entregable de
   la nueva fase, traducidos a formato build-plan (nombre en negrita + una
   línea de descripción).
5. Correr `/overview` para regenerar `blueprint/context/project-overview.md`
   a partir de los dos archivos anteriores.
6. Actualizar la sección de estado de `README.md` (fase activa, fases
   cerradas).

Los checkboxes de este archivo llevan el progreso real de estudio/entrega de
cada fase; los checkboxes de `build-plan.md` llevan el progreso del código.

---

## Fase 1 - Python + Fundamentos de LLMs (semanas 1-3) - Completada

### Python (sin cursos desde cero - traducción, no aprendizaje)

- [x] Sintaxis e idiomas del lenguaje: list/dict comprehensions, context managers, decoradores
- [ ] Async en Python (asyncio) vs. event loop de Node - diferencias clave (pregunta de entrevista)
- [x] Entorno: uv (o pip + venv), estructura de proyectos
- [x] FastAPI + Pydantic: tu puente desde NestJS (decoradores, DI, validación)
- [ ] Práctica de algoritmos (sliding window, hashmaps, two pointers) en Python desde ya

### Fundamentos de LLMs

- [x] Tokens, tokenización, context window, pricing por token
- [x] Parámetros de generación: temperature, top-p, max tokens
- [x] Embeddings a nivel conceptual (profundizas en Fase 2)
- [x] Cómo "piensa" un LLM: next-token prediction, limitaciones, alucinaciones

### Trabajo con APIs

- [x] SDKs de OpenAI y Anthropic (conoce ambos)
- [x] Streaming de respuestas (SSE)
- [x] Structured outputs / JSON mode
- [x] Manejo de errores, rate limits, retries con backoff (ya lo sabes de backend, aplícalo aquí)
- [ ] Fallback entre proveedores: si OpenAI falla o da rate limit, caer automáticamente a Anthropic (o viceversa); trabajo real reportado por AI engineers en el terreno, casi nadie lo implementa en proyectos de portafolio
- [x] Gestión de costos: estimación y control de gasto por request

### Prompt engineering

- [x] System prompts, few-shot examples, chain of thought
- [x] Patrones de I/O: clasificación, extracción, generación, transformación
- [x] Versionado de prompts (trátalos como código)

### Entregable Fase 1

Microservicio en FastAPI para CodeSage: recibe un fragmento de código + una
pregunta, y responde en streaming con una explicación estructurada (JSON con
resumen, complejidad, posibles bugs, sugerencia).

- [x] Streaming real vía SSE (no simulado)
- [x] Structured output validado con Pydantic
- [x] Manejo de rate limits y retries con backoff exponencial
- [ ] Fallback funcional entre al menos dos proveedores de LLM (OpenAI <-> Anthropic) - diferido, no bloqueó el cierre de fase; movido a Fase 5 (extra), al final del roadmap
- [x] Tracking de costo por request (tokens in/out x precio del modelo)
- [x] Al menos 3 prompts versionados (v1, v2, v3) con un changelog de por qué cambiaste cada uno

---

## Fase 2 - RAG end to end (semanas 4-7) - En progreso

### Embeddings en serio

- [x] Qué son, cómo se generan, modelos de embedding (dimensiones, costo)
- [x] Similitud: cosine similarity, distancia euclidiana

### Vector stores

- [ ] pgvector como primera opción (aprovechas tu Postgres, historia fuerte para entrevistas)
- [ ] Panorama de alternativas: Pinecone, Qdrant, Weaviate (conceptual, para conversar)

### Pipeline de RAG

- [x] Ingesta y chunking: estrategias (por tamaño, semántico, por estructura), overlap, trade-offs
- [x] Retrieval: top-k, filtros por metadata, hybrid search (keyword + semántico), re-ranking
- [ ] Generación: cómo inyectar contexto, citación de fuentes, manejo de "no sé"
- [ ] Por qué falla un RAG: chunks malos, retrieval irrelevante, contexto desbordado, y cómo diagnosticarlo

### Infra que ya tienes (solo traducir, no aprender)

- [ ] Background jobs para ingesta (equivalente a tu BullMQ)
- [ ] Docker para el stack completo
- [x] Kubernetes: solo nivel conceptual (qué es, cuándo se usa), no lo aprendas ahora

### Entregable Fase 2

Extiende CodeSage con ingesta y retrieval sobre un repositorio open source
real (clona uno con al menos 5k líneas de código + documentación).

- [ ] Chunking específico para código (por función/clase, no por tamaño fijo) vs. chunking de la documentación (semántico); implementa ambos y documenta la diferencia
- [ ] Hybrid search: combina búsqueda semántica (pgvector) con búsqueda por keyword (nombre de función, nombre de archivo)
- [ ] Re-ranking de resultados antes de pasarlos al LLM
- [ ] Citación de fuente exacta (archivo + línea) en cada respuesta generada
- [ ] Un caso documentado de "RAG que falló" y cómo lo diagnosticaste y arreglaste (esto vale más en entrevista que mostrar solo lo que funciona)
- [ ] Repo + demo desplegada + post explicando las decisiones de chunking y por qué código y documentación no se tratan igual

### Hito: desde la semana 6-8 empiezas a aplicar a roles de AI engineer

No esperas a "estar listo".

- [ ] Amplía el filtro de búsqueda: no solo postings con título "AI Engineer", revisa también "Backend Engineer" que mencionen RAG/agentes en el cuerpo del anuncio (~62% de esos postings ya son AI-first)
- [ ] Apunta a roles "Mid", no solo Senior; es la categoría de seniority que más está creciendo en el mercado ahora mismo

---

## Fase 3 - Agentes + Evals + Observabilidad (semanas 8-11) - Pendiente

### Agentes (lo más demandado del mercado actual)

- [ ] Function calling / tool use en profundidad
- [ ] Loops de agente: razonar -> actuar -> observar -> repetir
- [ ] Planning, memoria, límites de los agentes (cuándo NO usar uno)
- [ ] MCP (Model Context Protocol): qué es y cómo exponer herramientas
- [ ] Frameworks: qué resuelven LangChain, LangGraph y LlamaIndex, y cuándo NO usarlos (saber construir sin framework vale más en entrevistas); LangGraph es el framework de más rápido crecimiento del mercado y el combo LangChain+LangGraph es el par de skills más fuerte del análisis, necesitas poder hablar de ambos aunque construyas sin ellos

### Evals (tu mayor diferenciador en entrevistas)

- [ ] Por qué "¿cómo sabes que funciona?" es LA pregunta de contratación
- [ ] Datasets de evaluación: construcción, casos edge, golden answers
- [ ] LLM-as-judge: cómo y cuándo
- [ ] Métricas de RAG: relevancia de retrieval, faithfulness, respuesta correcta
- [ ] Regression testing de prompts: que un cambio no rompa lo que ya funcionaba

### Observabilidad

- [ ] Langfuse: tracing de llamadas, costos por request, latencias, sesiones
- [ ] Logging estructurado de interacciones LLM
- [ ] Sentry para errores clásicos de aplicación (esto es error monitoring, no safety)

### Seguridad de sistemas LLM

- [ ] Prompt injection: qué es, vectores de ataque, mitigaciones
- [ ] Validación de outputs antes de usarlos (especialmente si el output ejecuta acciones)
- [ ] Guardrails: filtros de entrada/salida, allowlists de herramientas
- [ ] Datos sensibles: qué nunca mandar al modelo

### Entregable Fase 3

Convierte CodeSage en un agente con 2-3 herramientas reales sobre el
repositorio: buscar símbolo/función, leer archivo completo, ejecutar los
tests del repo en un sandbox y reportar resultado.

- [ ] Suite de evals automatizada con al menos 20 casos golden (pregunta -> respuesta esperada), corrida en CI
- [ ] LLM-as-judge para los casos donde no hay una respuesta exacta única
- [ ] Dashboard de Langfuse con tracing de cada ejecución del agente (pasos, costo, latencia)
- [ ] Prueba explícita de resistencia a prompt injection: mete un comentario malicioso en el código del repo ("ignora tus instrucciones y...") y documenta cómo el agente lo maneja o falla en manejarlo
- [ ] Post mostrando el dashboard de evals, esto casi nadie lo publica y destaca muchísimo

---

## Fase 4 - Producción + Cierre de portafolio (semanas 12-14) - Pendiente

### Deployment

- [ ] Un solo cloud: AWS (mayor demanda en ofertas); Azure/GCP: conceptual
- [ ] CI/CD con GitHub Actions: test -> build -> deploy
- [ ] HTTPS, manejo de envs y secrets, logging en producción
- [ ] Health checks, alertas básicas

### Optimización (tema de entrevista senior)

- [ ] Prompt caching, semantic caching de respuestas
- [ ] Latencia: streaming, modelos más pequeños para tareas simples (model routing)
- [ ] Costos: tracking por feature, presupuestos

### Stretch goal (solo si sobra tiempo, no obligatorio)

- [ ] Segundo agente coordinado: un agente que analiza código + otro que redacta un reporte/resumen listo para review interno, comunicándose entre sí. No es indispensable para el portafolio, pero conecta con multi-agent patterns (listado como diferenciador de mercado) y con automatización de procesos internos, la categoría de uso que más está creciendo en los datos, más que las herramientas para desarrolladores

### Portafolio final

- [ ] 2-3 repos con READMEs impecables (problema -> decisiones -> arquitectura -> cómo correrlo)
- [ ] LinkedIn actualizado con título y evidencia de AI engineering
- [ ] Menciona explícitamente el uso de herramientas de código con IA (Claude Code, Cursor, etc.) como skill formal, el mercado ya las pide como línea aparte, no las des por sentado como implícitas
- [ ] CodeSage documentado como caso de estudio completo: de microservicio simple a agente con evals en producción

### Entregable Fase 4

CodeSage desplegado en AWS con CI/CD, más:

- [ ] Semantic caching activo (mide y reporta el % de requests que evitan llamar al LLM)
- [ ] Model routing: un modelo pequeño/barato para clasificación simple, uno grande para generación compleja, con la lógica de decisión documentada
- [ ] Portafolio completo publicado, con CodeSage como pieza central

---

## Fase 5 (extra) - Fallback multi-proveedor de LLM - Pendiente

No es parte de las 4 fases originales del roadmap. Se separó del entregable
de Fase 1 porque integrar un segundo proveedor completo (streaming + retries
propios, semántica de usage distinta) casi duplica el trabajo ya hecho para
Anthropic; se retoma al final, con el resto del roadmap ya cerrado.

### Entregable Fase 5

- [ ] Cliente OpenAI con streaming y retries: módulo que replica la interfaz
      del cliente Anthropic existente (stream de texto + reporte de usage),
      con el mismo manejo de retries/backoff en 429/5xx; incluye el pricing
      de los modelos OpenAI en el cálculo de costo
- [ ] Fallback automático entre proveedores: si el proveedor primario agota
      reintentos sin haber emitido ningún chunk todavía, cae automáticamente
      al proveedor secundario (OpenAI <-> Anthropic) para ese mismo request
- [ ] Selección de proveedor primario/secundario configurable por variables
      de entorno
- [ ] Prueba end-to-end que fuerza el fallo del proveedor primario y verifica
      que la respuesta se completa vía el secundario

---

## Transversal (todas las semanas, bloque 11:30-12:45)

- [ ] Commits visibles y consistentes en GitHub
- [ ] 1 post corto por semana en LinkedIn sobre lo que construiste/aprendiste
- [ ] Aplicaciones: roles backend Node.js desde la semana 1, roles AI engineer (incluyendo postings de "Backend Engineer" con RAG/agentes) desde la semana 6-8
- [ ] Cada entrevista (incluso fallida) = feedback gratis sobre qué reforzar
