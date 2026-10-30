# ADR-003: PostgreSQL en RDS, Redis en Compose y respaldos cifrados fuera de AWS

- **Estado:** aceptada (revisada el 2026-10-30: Redis con AOF y respaldo externo con permiso mínimo)
- **Fecha:** 2026-10-30
- **Relacionado con:** RNF-06, RNF-17, RNF-18, sección 11 de requerimientos (borrado en 30 días incluidos respaldos)

## Contexto

PostgreSQL es la fuente de verdad del sistema. Redis guarda la cola de ejecuciones, el progreso, las banderas de cancelación y el rate limit. RNF-17 pide respaldo diario con 7 días de retención. El equipo pidió además que los respaldos queden fuera de AWS, para no perder datos si la cuenta se pierde.

## Decisión

- **PostgreSQL 16 en Amazon RDS:**
  - db.t4g.micro, Single-AZ, 20 GB.
  - Subredes privadas, `publicly_accessible = false`.
  - Cifrado en reposo y `rds.force_ssl = 1`.
  - Respaldos automáticos con retención de 7 días.
  - Usuarios separados por componente con privilegios mínimos (sección 5.2 de la arquitectura).
- **Redis en el Docker Compose del backend:**
  - Sin puerto publicado y con `requirepass`.
  - Con persistencia **AOF** (`appendfsync everysec`), para no perder la cola en un reinicio normal.
  - Si aun así se pierde la cola, la limpieza de arranque del motor reconcilia el estado con PostgreSQL: vuelve a encolar o marca como «Fallida» cada ejecución pendiente (sección 4.3 de la arquitectura).
- **Respaldo externo diario:**
  - Un contenedor `respaldo` ejecuta `pg_dump`, cifra el volcado con `age` usando una llave pública y lo sube a un almacenamiento fuera de AWS.
  - Propuesta: una cuenta de Google Drive **dedicada al proyecto**, vía `rclone` con el permiso `drive.file` (solo puede ver y modificar los archivos que él mismo crea) y con versiones activadas, para que un atacante en el backend no pueda borrar copias anteriores sin dejar rastro.
  - Se conservan 7 copias. Cada semana un integrante descarga una copia a su computadora.
  - La llave privada se guarda fuera de línea en dos lugares.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| ElastiCache para Redis | Unos 12 USD al mes de créditos sin beneficio real a esta escala. |
| Redis sin persistencia | Un reinicio perdería la cola; la limpieza lo recupera, pero AOF lo evita casi sin costo. |
| PostgreSQL en contenedor | Ahorra unos 14 USD al mes, pero pierde los respaldos administrados, el cifrado administrado y la restauración a un punto en el tiempo. Queda como mitigación si se agotan los créditos. |
| Respaldos en S3 de la misma cuenta | Quedarían dentro de la cuenta que podría perderse. |
| Google Drive personal de un integrante | El token de `rclone` daría acceso a todo su Drive si comprometen el backend. |

## Consecuencias

- **Positivas:**
  - Hay dos capas de respaldo: RDS cubre fallas operativas y la copia externa cubre la pérdida de la cuenta.
  - Retener 7 copias cumple el borrado definitivo en menos de 30 días.
- **Negativas:**
  - RDS es el mayor costo de la cuenta (≈ 14 USD al mes).
  - La restauración desde la copia externa debe probarse antes de la entrega (sección 6 de la arquitectura).
  - La llave privada de `age` es un secreto crítico: si se pierde, las copias externas son inservibles.
