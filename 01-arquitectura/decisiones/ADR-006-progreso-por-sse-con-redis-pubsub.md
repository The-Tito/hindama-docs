# ADR-006: Progreso por SSE con Redis pub/sub retransmitido por Next.js

- **Estado:** aceptada (revisada el 2026-10-30: rutas anidadas bajo el proyecto por las convenciones de [ADR-016](ADR-016-contrato-primero-con-verificacion-automatica.md); la decisión no cambia). Implementada el 2026-11-17, con la cancelación por SAQ en lugar de la bandera (ver «Implementación»)
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
- La **cancelación** es una bandera en Redis (`cancel:{id}`) que el worker revisa antes de cada petición, así que se detiene en menos de 5 segundos (RF-52). *Al implementarla (tarea 3.3) se cambió por abortar el trabajo de SAQ; ver «Implementación».*

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

## Implementación (tarea 3.3, 2026-11-17)

Cómo quedó en el código y qué cambió respecto de la decisión original:

- **Cancelación: se aborta el trabajo de SAQ, sin bandera `cancel:{id}`.** La API guarda `cancel_requested_at` y llama a `abort` de SAQ. El temporizador `abort=1` del worker cancela la tarea de `asyncio` de la ejecución, incluida la petición HTTP en curso. Se eligió porque SAQ ya lo resolvía (PT-02 lo midió en ~1 s) y la bandera exigía código propio en cada petición del motor. **Resultado medido** con el laboratorio a 1 petición por segundo: la ejecución se detiene **0,9 s** después de pedirlo (tres corridas), con los resultados parciales conservados. RF-52 pide menos de 5 s.
- **Una ejecución en cola** se cancela en la misma transacción de la API (`cancelled` / `cancelled_by_user`). Si Redis no responde, se cancela igual, porque el motor descarta un trabajo cuya ejecución ya no está en cola. **Una en curso** necesita a Redis: sin él, la API responde 503 y revierte la transacción.
- **Carrera entre la API y el motor.** La API bloquea la fila (`FOR UPDATE`) hasta su commit, y el motor, al recibir la cancelación, lee `cancel_requested_at` con el mismo bloqueo. Así nunca ve la solicitud a medias. Solo una ejecución con `cancel_requested_at` termina `cancelled_by_user`. Cualquier otra cancelación (el worker que se detiene) la deja en `running`, para la reconciliación (tarea 3.4). El estado final se escribe en una tarea protegida (`asyncio.shield`), para que una segunda cancelación no lo deje a medias.
- **El canal `run:{id}` solo lleva el tipo de evento** (`progress` o `end`), nunca datos. En cada evento, el stream vuelve a leer la ejecución de PostgreSQL con la seguridad por filas del usuario (ADR-013). Así no pasa nada del proyecto por Redis (como en la cola, ADR-012), el contenido de `progress` y `end` se arma en un solo lugar y un mensaje perdido solo retrasa la siguiente lectura.
- **Frecuencia:** el motor publica como máximo un `progress` por segundo. El cambio que llega dentro del intervalo sale al cerrarse el intervalo, y el cambio de módulo sale de inmediato. `end` se publica después de guardar el estado final.
- **El stream se suscribe antes de leer el `snapshot`.** Si lo hiciera después, un `end` publicado en medio se perdería y el stream quedaría abierto. Solo envía `progress` si cambió algo. Cada 15 s, además del `: ping`, vuelve a leer la base, así que un `end` perdido (un motor que murió) se detecta a esa hora. No retiene una conexión a la base mientras espera.
- **Sin Redis,** el stream lee la base cada segundo: sigue dentro de los 2 s de RNF-03, solo es más caro.
- **Vida máxima de 15 minutos:** el servidor cierra el stream y el navegador reconecta con `snapshot`. Así ninguna conexión queda abierta indefinidamente. Los `id:` siguen desde `Last-Event-ID`.
- **`StreamingResponse` propio,** sin `sse-starlette`, sobre `redis.asyncio`, que ya llega con SAQ.
- **Pendiente:** registrar la cancelación en la bitácora (RF-81, tarea 4.3) y limpiar los recursos creados (RN-06). Hoy ningún módulo crea recursos, así que todavía no hay nada que limpiar.

Incidencias encontradas por las pruebas:

- `PubSub.get_message` de `redis-py` devuelve `None` **de inmediato** cuando lo que leyó es la confirmación de la suscripción, sin esperar el `timeout`. La primera versión tomaba ese `None` como «no hubo eventos». La prueba con Redis real lo detectó, y ahora se sigue esperando hasta el plazo.
- `str.isdecimal()` acepta dígitos no ASCII (por ejemplo, `٣`). Un `Last-Event-ID` así se habría tomado como número. Se restringió a ASCII.
- La prueba del orden `snapshot` → `progress` → `end` falló una vez bajo la carga de la cobertura. El motor terminó antes de que el stream leyera la base, y el stream pasó de `snapshot` a `end`. Ese comportamiento es correcto. La prueba suponía que siempre habría un `progress` y ahora le da al stream tiempo de leer cada uno.
