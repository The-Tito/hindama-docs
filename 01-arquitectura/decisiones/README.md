# Decisiones de arquitectura (ADR)

Un archivo por decisión: `ADR-NNN-titulo-corto.md`, con contexto, decisión, alternativas consideradas y consecuencias. Las decisiones no se borran: si cambian, se crea una nueva que sustituye a la anterior.

## Índice

| ADR | Decisión | Estado |
| --- | --- | --- |
| [ADR-001](ADR-001-despliegue-en-dos-cuentas-aws.md) | Despliegue repartido en dos cuentas de AWS (frontend y backend) con VPC peering | Sustituida por ADR-010 |
| [ADR-002](ADR-002-ec2-con-docker-compose.md) | Dos EC2 con Docker Compose y Caddy, sin ALB | Aceptada (revisada) |
| [ADR-003](ADR-003-rds-redis-en-compose-y-respaldos-fuera-de-aws.md) | PostgreSQL en RDS, Redis en Compose y respaldos cifrados fuera de AWS | Aceptada |
| [ADR-004](ADR-004-red-del-backend-sin-nat.md) | Backend en subred pública con SG cerrado e IP elástica, sin NAT | Aceptada |
| [ADR-005](ADR-005-sesion-bff-con-cookie-cifrada.md) | Sesión BFF: tokens de Cognito en cookie cifrada HttpOnly | Aceptada |
| [ADR-006](ADR-006-progreso-por-sse-con-redis-pubsub.md) | Progreso por SSE con Redis pub/sub retransmitido por Next.js | Aceptada |
| [ADR-007](ADR-007-cifrado-de-credenciales-aes-gcm.md) | Credenciales cifradas con AES-256-GCM y clave en SSM Parameter Store | Aceptada |
| [ADR-008](ADR-008-guardia-ssrf-con-ip-fijada.md) | Guardia SSRF única con resolución previa e IP fijada | Aceptada |
| [ADR-009](ADR-009-infraestructura-como-codigo-terraform.md) | Infraestructura como código con Terraform, desplegable en una o dos cuentas | Sustituida por ADR-011 |
| [ADR-010](ADR-010-una-sola-cuenta-aws.md) | Una sola cuenta de AWS; la segunda queda como respaldo | Aceptada |
| [ADR-011](ADR-011-despliegue-con-compose-y-procedimiento.md) | Despliegue con Docker Compose y procedimiento escrito; Terraform diferido | Aceptada |
| [ADR-012](ADR-012-motor-asincrono.md) | Motor de pruebas asíncrono con varias ejecuciones por proceso | Aceptada |
| [ADR-013](ADR-013-aislamiento-por-propietario-en-el-esquema.md) | Aislamiento por propietario en el esquema: UUID, FK compuestas y Row-Level Security | Aceptada |
| [ADR-014](ADR-014-seguimiento-de-hallazgos-por-huella-y-cobertura.md) | Seguimiento de hallazgos por huella y cobertura | Aceptada |
| [ADR-015](ADR-015-borrado-retencion-y-anonimizacion.md) | Borrado, retención y anonimización de datos | Aceptada |
| [ADR-016](ADR-016-contrato-primero-con-verificacion-automatica.md) | Contrato de la API escrito primero y verificado automáticamente | Aceptada |
| [ADR-017](ADR-017-identificadores-en-ingles.md) | Identificadores técnicos en inglés; documentos y textos para el usuario en español | Aceptada |
