# hindama-docs

Fuente única de verdad del proyecto **Hindama** (en estonio, «evaluar»): una plataforma web para verificar la seguridad de APIs REST a partir de su contrato OpenAPI 3 y dar seguimiento a cada hallazgo hasta su corrección.

Los repositorios `hindama-backend` y `hindama-frontend` se clonan junto a este, en la misma carpeta madre, y lo referencian con rutas relativas (`../hindama-docs/...`).

## Índice

| Ruta | Contenido | Estado |
| --- | --- | --- |
| `00-producto/requerimientos.md` | Requerimientos de software v1.0: F-01 a F-15, RF-01 a RF-87, RN-01 a RN-12, RNF-01 a RNF-24 | Cerrado (2026-10-30) |
| `00-producto/casos-de-uso.md` | Casos de uso | Pendiente |
| `01-arquitectura/arquitectura.md` | Componentes, servicios de AWS, flujos clave, límites de confianza, supuestos | Cerrado v0.2 (2026-10-30) |
| `01-arquitectura/amenazas.md` | Modelo de amenazas (STRIDE) de la plataforma | Pendiente |
| `01-arquitectura/decisiones/` | Un archivo por decisión de arquitectura (ADR-NNN) | ADR-001 a ADR-012 (001 y 009 sustituidas) |
| `02-datos/modelo.md` | Modelo de datos (ER en Mermaid y tablas) | Pendiente |
| `03-api/openapi.yaml` | Contrato de la API de la plataforma: lo leen frontend y backend | Pendiente |
| `04-ui/flujos.md` | Flujos de pantalla y wireframes | Pendiente |
| `05-pruebas/catalogo-laboratorio.md` | Fallas esperadas en VAmPI y la mini API | Pendiente |
| `indice/` | Artefactos generados (trazabilidad, grafo). No se editan a mano | — |
| `entregables/` | Versiones .docx y .pdf para la escuela | — |

## Convenciones

- El Markdown es la fuente; los .docx en `entregables/` son exportaciones.
- Los identificadores son estables y no se reutilizan: `F-nn` (funcionalidad), `RF-nn` (requerimiento funcional), `RN-nn` (regla de negocio), `RNF-nn` (no funcional), `ADR-nnn` (decisión). Úsalos en commits, issues, código y pruebas para mantener la trazabilidad.
- Si una decisión afecta a frontend y backend, va aquí. Si solo afecta a un repo, va en la carpeta de documentos de ese repo (en el backend: `Context/documentos/`).

## Decisiones tomadas

| Fecha | Decisión |
| --- | --- |
| 2026-10-29 | Se prueban APIs reales de los usuarios, con verificación de propiedad (archivo `/.well-known/hindama-verificacion.txt` o registro DNS TXT) |
| 2026-10-29 | Siete módulos: Autenticación (API2), Configuración (API8), Acceso a objetos (API1), Acceso a funciones (API5), Propiedades (API3), Consumo de recursos (API4), Inyección SQL (CWE-89) |
| 2026-10-29 | Login de la plataforma con Amazon Cognito; 2FA TOTP en la fase final |
| 2026-10-30 | IA (Gemini de pago, Groq de respaldo) y proyecto de demostración quedan para versiones futuras |
| 2026-10-30 | Nombre definitivo: Hindama (antes AuthzCheck / API-Tester) |
| 2026-10-30 | Despliegue completo (frontend y backend) en AWS |
| 2026-10-30 | Frontend en Next.js con servidor (BFF): sesión en cookie HttpOnly, sin lógica de negocio; FastAPI solo accesible desde Next.js |
| 2026-10-30 | VAmPI y mini API: laboratorio interno de desarrollo, no disponible para usuarios |
| 2026-10-30 | Alcance confirmado con el profesor |
| 2026-10-30 | Tres repositorios: `hindama-docs` (contexto compartido), `hindama-backend` (base de datos y API) y `hindama-frontend` |
| 2026-10-30 | Una sola cuenta de AWS (`us-east-1`) con dos EC2 (frontend y backend) y RDS; la segunda cuenta queda como respaldo (ADR-010, sustituye a ADR-001) |
| 2026-10-30 | Dos EC2 con Docker Compose y Caddy (frontend t4g.micro, backend t4g.small); Redis en Compose con AOF; PostgreSQL en RDS; respaldos cifrados fuera de AWS (ADR-002, ADR-003) |
| 2026-10-30 | Backend sin NAT: subred pública, SG sin entrada de Internet e IP elástica de salida fija (ADR-004) |
| 2026-10-30 | Despliegue con Docker Compose y procedimiento escrito; Terraform diferido (ADR-011, sustituye a ADR-009) |
| 2026-10-30 | Motor de pruebas asíncrono con varias ejecuciones por proceso; la biblioteca de cola (`arq` o `SAQ`) se elige en la semana 1 (ADR-012) |
| 2026-10-30 | La app usa un subdominio de uno de los dos dominios del equipo |
| 2026-10-30 | Entrega a finales de noviembre de 2026 |

## Stack

Next.js (React + TypeScript) · Python 3.12 + FastAPI + httpx · Redis + cola asíncrona (`arq` o `SAQ`) · PostgreSQL 16 + SQLAlchemy + Alembic · Amazon Cognito · Docker · AWS.

## Siguientes pasos

1. Acordar el núcleo entregable para finales de noviembre y el plan de 4 semanas.
2. Modelo de datos.
3. En paralelo: interfaces (frontend) y contrato OpenAPI de la plataforma (backend).
4. Pruebas técnicas de la semana 1: cola asíncrona (ADR-012), guardia SSRF con IP fijada (ADR-008) y formulario propio con Cognito (ADR-005).
5. Laboratorio y catálogo de fallas (puede empezar ya).
6. Modelo de amenazas (STRIDE), a partir de la sección 5 de la arquitectura.
