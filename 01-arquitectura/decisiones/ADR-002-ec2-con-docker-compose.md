# ADR-002: Dos EC2 con Docker Compose y Caddy, sin ALB

- **Estado:** aceptada (revisada el 2026-10-30 tras [ADR-010](ADR-010-una-sola-cuenta-aws.md) y [ADR-012](ADR-012-motor-asincrono.md))
- **Fecha:** 2026-10-30
- **Relacionado con:** RNF-01, RNF-04, RNF-16, RNF-20, sección 11 de requerimientos (despliegue con Docker Compose)

## Contexto

Los componentes de Hindama corren en contenedores Docker. Los requerimientos piden que todo el sistema se levante con Docker Compose en el equipo de cualquier integrante. Los créditos son limitados y la plataforma vive en una sola cuenta ([ADR-010](ADR-010-una-sola-cuenta-aws.md)).

## Decisión

- Dos EC2 Graviton con Amazon Linux 2023 y Docker Compose, en la misma cuenta:
  - **Frontend:** t4g.micro (2 vCPU, 1 GB) con `caddy` + `next`.
  - **Backend:** t4g.small (2 vCPU, 2 GB) con `caddy` + `api` + `motor` ([ADR-012](ADR-012-motor-asincrono.md)) + `redis` + `respaldo`, y 2 GB de swap.
- Cada contenedor tiene un **límite de memoria** en Compose (sección 2.3 de la arquitectura), para que el motor nunca deje sin memoria a la API.
- El TLS público lo termina **Caddy** con certificados de Let's Encrypt en la EC2 del frontend, en lugar de un ALB.
- Las imágenes se construyen para `linux/arm64` en GitHub Actions y se publican en GitHub Container Registry.
- La administración se hace con SSM Session Manager, sin puerto SSH abierto.
- Para la disponibilidad se activa EC2 auto-recovery y se usa `restart: unless-stopped` en cada contenedor.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| ECS Fargate | Sin capa gratuita: unos 25–35 USD al mes solo de cómputo, más ALB y NAT. No cabe en los créditos. |
| Lightsail containers | El control de red es limitado: cuesta más mantener FastAPI realmente privada. |
| ALB + ACM | Unos 16–20 USD al mes, más IPs públicas. Caddy hace lo mismo para una sola instancia sin costo. |
| Una sola EC2 para todo | Mezcla el borde expuesto a Internet con el núcleo y sus secretos ([ADR-010](ADR-010-una-sola-cuenta-aws.md)). |
| EC2 x86 (t3) | Más caras que las Graviton equivalentes. |

## Consecuencias

- **Positivas:**
  - Producción y local usan los mismos archivos de Compose.
  - El sistema se reinicia en menos de 5 minutos (RNF-20).
- **Negativas:**
  - Cada componente tiene un único punto de falla. El 99 % mensual (RNF-16, unas 7 h de caída permitida) se cumple con auto-recovery, pero no hay redundancia.
  - Los parches del sistema operativo quedan a cargo del equipo (`dnf-automatic`).
  - La capacidad de 2 GB del backend es un supuesto que se valida con la prueba de carga de la semana 3. Si no alcanza, se baja la concurrencia del motor o se pasa a t4g.medium (≈ 24 USD al mes).
  - Las imágenes deben compilarse para ARM64.
