# ADR-006: Progreso por SSE con Redis pub/sub retransmitido por Next.js

- **Estado:** aceptada (revisada el 2026-10-30: rutas anidadas bajo el proyecto por las convenciones de [ADR-016](ADR-016-contrato-primero-con-verificacion-automatica.md); la decisión no cambia)
- **Fecha:** 2026-10-30
- **Relacionado con:** RF-51, RF-52, RNF-03, RNF-18

## Contexto

La interfaz muestra el progreso de una ejecución en tiempo real, con un retraso máximo de 2 segundos (RNF-03). La ejecución corre en un proceso worker distinto de FastAPI. El navegador solo puede hablar con Next.js.

## Decisión

- El **worker publica** eventos de progreso en el canal Redis `run:{id}`: estado, módulo, peticiones, porcentaje, hallazgos y fin.
- **FastAPI expone** `GET /projects/{pid}/runs/{id}/events` como `text/event-stream`:
  1. Valida el JWT y la propiedad de la ejecución.
  2. Envía primero la foto actual leída de PostgreSQL.
  3. Se suscribe al canal.
  4. Emite un `: ping` cada 15 segundos.
- **Next.js retransmite** el stream en un route handler (`/api/projects/{pid}/runs/{id}/progress`), sin guardarlo ni transformarlo y agregando el Bearer de la sesión. Caddy no almacena en búfer las respuestas `text/event-stream`.
- Cada evento lleva `id:`. Al reconectar con `Last-Event-ID`, FastAPI vuelve a enviar la foto actual.
- La **cancelación** es una bandera en Redis (`cancel:{id}`) que el worker revisa antes de cada petición, así que se detiene en menos de 5 segundos (RF-52).

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| WebSockets | Bidireccionales sin necesidad, con más complejidad en Caddy y en Next.js. El requerimiento ya fija SSE (sección 9.4). |
| Sondeo periódico desde el navegador | Más carga sobre FastAPI y el rate limit (RNF-09), y difícil de mantener bajo 2 s. |
| El navegador conectado directo a FastAPI | FastAPI no es pública (RNF-07). |
| Redis Streams en lugar de pub/sub | Permitiría repetir eventos perdidos, pero la foto en PostgreSQL ya cubre la reconexión. Pub/sub es más simple. |

## Consecuencias

- **Positivas:**
  - La latencia es baja.
  - Si Redis pierde mensajes, la interfaz se recupera con la foto de la base de datos.
  - El rate limit por usuario no aplica a cada evento, solo a la apertura del stream.
- **Negativas:**
  - Cada stream abierto ocupa una conexión en Next.js y en FastAPI. Con 50 usuarios (RNF-04) es manejable.
  - La retransmisión en Next.js debe propagar el cierre del navegador para liberar la suscripción en FastAPI.
