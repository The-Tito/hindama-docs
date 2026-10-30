# ADR-012: Motor de pruebas asíncrono con varias ejecuciones por proceso

- **Estado:** aceptada
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
