# ADR-012: Motor de pruebas asíncrono con varias ejecuciones por proceso

- **Estado:** aceptada (biblioteca de cola elegida por la prueba técnica PT-02 el 2026-11-05: SAQ)
- **Fecha:** 2026-10-30
- **Relacionado con:** RF-47, RF-51, RF-52, RNF-01, RNF-04, RNF-18, sección 6 de requerimientos

## Contexto

El requerimiento pide 10 ejecuciones simultáneas (RNF-04) en una EC2 de 2 GB que también corre la API, Redis y Caddy. La versión 0.1 de la arquitectura proponía RQ, que procesa un trabajo por proceso y crea un proceso hijo para cada trabajo. Diez procesos de Python con SQLAlchemy, httpx, Pydantic y la librería de OpenAPI ocupan más de 1 GB por sí solos, y llevarían la máquina al swap, con lo que la API incumpliría RNF-01.

Además, la cancelación debe ocurrir en menos de 5 segundos (RF-52). Si el motor solo revisa la bandera de cancelación entre peticiones, una petición en curso puede tardar hasta 15 segundos (su tiempo de espera de lectura).

El trabajo del motor es casi todo espera de red: enviar una petición y esperar la respuesta.

## Decisión

- El motor es un **proceso asíncrono** (`asyncio`) que atiende **varias ejecuciones a la vez**, cada una como una tarea independiente. Usa el cliente asíncrono de httpx a través de la guardia SSRF ([ADR-008](ADR-008-guardia-ssrf-con-ip-fijada.md)).
- La concurrencia es configurable (supuesto inicial: 10 ejecuciones por proceso, 1–2 procesos). Las ejecuciones que excedan el límite esperan en la cola.
- La **cola** vive en Redis y la gestiona una biblioteca de colas asíncrona: **`arq` o `SAQ`**, que se elige en la prueba técnica de la semana 1. Criterios: cancelación de trabajos en curso, tiempo máximo por trabajo, reintentos y mantenimiento activo.
- **Cancelación:** la señal llega por Redis y el motor cancela la tarea de esa ejecución, lo que interrumpe también la petición HTTP en curso. Después corre la limpieza de recursos creados (RN-06).
- **Aislamiento entre ejecuciones:** cada tarea tiene su propio limitador de velocidad, sus credenciales en memoria y su cliente HTTP. Una excepción en una ejecución la marca como «Fallida» sin afectar a las demás.
- El contenedor del motor tiene un **límite de memoria** en Compose, para que nunca deje sin memoria a la API.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| RQ con un proceso por ejecución | No cabe en 2 GB con 10 ejecuciones, y la cancelación entre peticiones no cumple RF-52. |
| RQ con pocos procesos y `asyncio` dentro de cada trabajo | Sigue siendo una ejecución por proceso; la concurrencia real queda limitada al número de procesos. |
| Celery | Más pesado y orientado a procesos; su soporte de `asyncio` es limitado. |
| Consumidor propio sobre Redis | Viable, pero hay que construir reintentos, tiempos máximos y cancelación. Queda como plan B si ninguna biblioteca cumple. |

## Consecuencias

- **Positivas:**
  - Mucho menos memoria por ejecución: las ejecuciones comparten un proceso.
  - La cancelación es inmediata.
  - Cada ejecución está aislada en su propia tarea.
- **Negativas:**
  - Todo el código del motor debe ser asíncrono: una llamada bloqueante (por ejemplo, un driver de base de datos síncrono) detiene todas las ejecuciones del proceso. Se usa SQLAlchemy en modo asíncrono con `asyncpg`.
  - Los requerimientos mencionaban RQ (sección 6 y 9.3); se actualizan a «cola asíncrona sobre Redis».
  - Un error de memoria en el proceso afecta a todas sus ejecuciones a la vez. La limpieza de arranque las marca como «Fallida» (RNF-18).

## Resultado de la prueba técnica (2026-11-05)

Detalle completo en [pruebas técnicas, PT-02](../pruebas-tecnicas.md#3-pt-02-cola-asíncrona-arq-contra-saq-adr-012).

- **Se elige SAQ.** arq y SAQ cumplen las dos 10 trabajos por proceso (~33 MB) y la cancelación con limpieza asíncrona en menos de 1 s (RF-52).
- La diferencia está en la recuperación tras una caída. Con `SIGKILL` al worker, arq tardó **310 s** en declarar fallido el trabajo huérfano: espera el tiempo máximo más largo de cualquier función más 10 s. SAQ lo detectó en **10 s** con latido y barrido.
- arq está oficialmente en modo solo mantenimiento y no admite redis-py 6 ni 7.
- Configuración inicial: `concurrency=10`, ejecuciones sin reintento (`retries=1`), `heartbeat` de 15–30 s actualizado con el progreso, barrido cada 10–15 s y `cancellation_hard_deadline_s` suficiente para la limpieza de RN-06.

## Implementación (tarea 3.1, 2026-11-16)

Cómo quedó la cola en el código, y las decisiones que se tomaron al implementarla:

- **Encolar antes del commit.** La API inserta la ejecución, la encola y después confirma la transacción. Si Redis no responde, la transacción se revierte y la API responde 503, así que nunca queda una ejecución `queued` sin trabajo que bloquee el proyecto (RN-07). La consecuencia es que el motor puede recibir el trabajo antes de que la fila sea visible: espera hasta 5 s a que aparezca y, si no aparece, lo descarta (la API la revirtió). Hay una prueba que reproduce esa carrera con una transacción abierta.
- **El trabajo solo lleva el id de la ejecución.** Módulos, límites y credenciales se leen de PostgreSQL; por Redis no pasa nada sensible.
- **Clave del trabajo `run:{id}`.** Encolar dos veces la misma ejecución deja un solo trabajo.
- **Nueva verificación de propiedad (RF-20).** Si el código ya no está publicado (`file_not_found`, `content_mismatch`, `txt_missing`) o el host apunta a un destino prohibido, la ejecución termina `cancelled` con `verification_invalid` y el proyecto vuelve a «Pendiente de verificación». Un error de conexión **no** prueba que se perdió la propiedad: la ejecución termina `failed` con `error` y la verificación se conserva.
- **Latido:** el motor toca el trabajo de SAQ y `runs.heartbeat_at` cada 10 s; SAQ lo da por muerto a los 30 s sin latido y el barrido corre cada 10 s.
- **Redis en Compose:** contraseña, AOF, `noeviction` (perder un trabajo dejaría una ejecución en cola), 128 MB y sin puerto hacia la red.
- **Incidencia.** El primer arranque de Redis falló con «Permission denied» al crear el directorio del AOF. La causa fue nuestra: el contenedor corría como root con `cap_drop: [ALL]`, que le quita a root el permiso de escribir en `/data` (propiedad del usuario `redis`). Se corrigió corriendo el contenedor como `redis`, sin ninguna capacidad, en lugar de devolverle capacidades a root.
- **En CI,** Redis corre sin contraseña: los servicios de GitHub Actions no permiten cambiar el comando del contenedor, y esa instancia solo vive durante el job. Las pruebas usan la base 1 y la vacían al terminar.
