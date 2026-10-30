# hindama-docs

Fuente única de verdad del proyecto **Hindama** (en estonio, «evaluar»): una plataforma web para verificar la seguridad de APIs REST a partir de su contrato OpenAPI 3 y dar seguimiento a cada hallazgo hasta su corrección.

Los repositorios `hindama-backend` y `hindama-frontend` se clonan junto a este, en la misma carpeta madre, y lo referencian con rutas relativas (`../hindama-docs/...`).

## Índice

| Ruta | Contenido | Estado |
| --- | --- | --- |
| `00-producto/requerimientos.md` | Requerimientos de software v1.0: F-01 a F-15, RF-01 a RF-87, RN-01 a RN-12, RNF-01 a RNF-24 | Cerrado (2026-10-30) |
| `00-producto/casos-de-uso.md` | Casos de uso | Pendiente |
| `01-arquitectura/arquitectura.md` | Componentes, servicios de AWS, flujos clave | Siguiente |
| `01-arquitectura/amenazas.md` | Modelo de amenazas (STRIDE) de la plataforma | Pendiente |
| `01-arquitectura/decisiones/` | Un archivo por decisión de arquitectura (ADR-NNN) | Pendiente |
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

## Stack

Next.js (React + TypeScript) · Python 3.12 + FastAPI + httpx · Redis + RQ · PostgreSQL 16 + SQLAlchemy + Alembic · Amazon Cognito · Docker · AWS.

## Siguientes pasos

1. Documento de arquitectura: componentes, servicios concretos de AWS, flujos clave y modelo de amenazas (STRIDE).
2. Modelo de datos.
3. En paralelo: interfaces (frontend) y contrato OpenAPI de la plataforma (backend).
4. Laboratorio y catálogo de fallas (puede empezar ya).
5. Plan de trabajo con fechas (falta la fecha de entrega).
