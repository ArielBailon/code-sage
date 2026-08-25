# Project Plan

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
- Endpoint que recibe un fragmento de código + una pregunta
- Respuesta en streaming real vía SSE (Server-Sent Events), no simulada
- El streaming se estructura como eventos por campo (`event: resumen`,
  `event: complejidad`, `event: posibles_bugs`, `event: sugerencia`), cada
  uno validable individualmente; el objeto completo se valida con Pydantic
  al cerrar el stream
- Manejo de rate limits del proveedor LLM con reintentos y backoff exponencial
- Cálculo de costo por request a partir de tokens de entrada/salida × precio
  del modelo usado
- Al menos 3 versiones de prompt (v1, v2, v3) con un changelog que explique
  el motivo de cada cambio

## 4. Data - What are we storing?
No hay persistencia de usuarios ni historial en esta fase. Se registra en
logs (o en la respuesta misma) el costo por request y la versión de prompt
usada, para poder comparar versiones más adelante.

## 5. Tech - What stack are we using?
Python, FastAPI, Pydantic para validación de esquemas, httpx o el SDK oficial
del proveedor LLM para las llamadas, tenacity (o lógica manual) para
retries/backoff, pytest para pruebas.

## 6. Monetize - How will this make money?
No es un producto comercial en esta fase. Su valor es como pieza de
portafolio (CodeSage) y como práctica aplicada del roadmap de AI Engineer.

## 7. UI/UX - How should this look and feel?
No aplica interfaz visual: es un microservicio backend. La "experiencia" a
optimizar es la del consumidor de la API — respuesta rápida en el primer
byte (streaming), errores claros, y contrato JSON estable y predecible.

## 8. Deployment - Where and how will this ship?
Fuera de alcance para la Fase 1. El entregable se valida localmente
(`uvicorn` + pruebas manuales y automatizadas). Deployment se planifica como
fase posterior una vez cerrado este build plan.