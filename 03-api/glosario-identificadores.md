---
documento: Glosario de identificadores
proyecto: Hindama
version: 0.1
fecha: 2026-10-30
estado: vigente
---

# Glosario de identificadores

Todo identificador técnico de Hindama está **en inglés**: rutas y campos de la API, tablas, columnas y valores de catálogo de la base de datos, y carpetas, archivos, clases, funciones y variables del código ([ADR-017](../01-arquitectura/decisiones/ADR-017-identificadores-en-ingles.md)). Los documentos, los comentarios y los textos que ve el usuario siguen en español.

Esta tabla es la única fuente de las traducciones. Si un término nuevo no está aquí, se agrega en el mismo pull request que lo usa por primera vez.

## Entidades

| Término (documentos) | Tabla | Modelo / esquema | Ruta de la API |
| --- | --- | --- | --- |
| Usuario | `users` | `User` | `/me` |
| Proyecto | `projects` | `Project` | `/projects` |
| Versión del contrato | `contract_versions` | `ContractVersion` | `/projects/{project_id}/contracts` |
| Operación | `operations` | `Operation` | `/projects/{project_id}/operations` |
| Operación en una versión | `operation_versions` | `OperationVersion` | — |
| Identidad | `identities` | `Identity` | `/projects/{project_id}/identities` |
| Recurso | `resources` | `Resource` | `/projects/{project_id}/resources` |
| Ejecución | `runs` | `Run` | `/projects/{project_id}/runs` |
| Resultado (celda evaluada) | `results` | `Result` | — |
| Recurso creado por la plataforma | `created_resources` | `CreatedResource` | — |
| Hallazgo | `findings` | `Finding` | `/projects/{project_id}/findings` |
| Ocurrencia de un hallazgo | `finding_occurrences` | `FindingOccurrence` | — |
| Evento de un hallazgo | `finding_events` | `FindingEvent` | — |
| Bitácora | `audit_log` | `AuditLogEntry` | `/admin/audit-log` |
| Métrica de hallazgo | `finding_metrics` | `FindingMetric` | — |
| Métrica diaria | `daily_metrics` | `DailyMetric` | — |
| Motor de pruebas | — | paquete `scanner` | — |
| Guardia SSRF | — | paquete `safe_http` | — |

Las tablas van en plural (`user` es palabra reservada de PostgreSQL); los modelos y esquemas, en singular.

## Catálogos

| Concepto | Valores (documentos → identificador) |
| --- | --- |
| Rol de la plataforma | analista → `analyst`, administrador → `admin` |
| Estado de verificación | pendiente → `pending`, verificado → `verified` |
| Método de verificación | archivo → `file`, DNS → `dns` |
| Módulo | Autenticación → `authentication`, Configuración → `configuration`, Acceso a objetos → `object_access`, Acceso a funciones → `function_access`, Propiedades → `property_access`, Consumo de recursos → `resource_consumption`, Inyección SQL → `sql_injection` |
| Riesgo del módulo | bajo → `low`, medio → `medium`, alto → `high` |
| Plantilla de política | pública → `public`, cualquier autenticado → `authenticated`, solo propietario → `owner_only`, propietario o administrador → `owner_or_admin`, solo administrador → `admin_only` |
| Rol de una identidad | administrador → `admin`, usuario → `user`, otro → `other` |
| Forma de autenticación | ninguna (anónima) → `none`, login automático → `login`, token Bearer → `bearer`, cookie → `cookie`, cabecera personalizada → `header` |
| Estado de una identidad | activa → `active`, credencial vencida → `expired_credential` |
| Origen de un recurso | descubierto → `discovered`, manual → `manual` |
| Origen del contrato | archivo → `file`, URL → `url` |
| Estado de una ejecución | en cola → `queued`, en curso → `running`, completada → `completed`, cancelada → `cancelled`, fallida → `failed` |
| Motivo de fin | normal → `normal`, límite alcanzado → `limit_reached`, cancelada por el usuario → `cancelled_by_user`, verificación inválida → `verification_invalid`, latido vencido → `heartbeat_expired`, perdida en la cola → `lost_in_queue`, error → `error` |
| Veredicto de un resultado | ok → `pass`, falla → `fail`, omitido → `skipped`, error → `error` |
| Estado de un recurso creado | pendiente → `pending`, eliminado → `deleted`, fallido → `failed` |
| Severidad | crítica → `critical`, alta → `high`, media → `medium`, baja → `low`, informativa → `info` |
| Estado de un hallazgo | nuevo → `new`, persistente → `persistent`, resuelto → `resolved`, regresión → `regression`, riesgo aceptado → `accepted_risk` |
| Motivo de descarte | riesgo aceptado → `accepted_risk`, falso positivo → `false_positive` |
| Motivo de resolución | no detectado → `not_detected`, identidad eliminada → `identity_deleted`, operación retirada → `operation_retired` |
| Motivo de un evento de hallazgo | `detected`, `not_detected`, `regression`, `accepted`, `false_positive`, `reverted`, `identity_deleted`, `operation_retired` |
| Indicador de métrica diaria | usuarios nuevos → `new_users`, cuentas eliminadas → `deleted_accounts`, proyectos creados → `projects_created`, ejecuciones lanzadas → `runs_started` |

## Términos que se repiten en campos

| Término | Identificador |
| --- | --- |
| propietario | `owner` (`owner_id`) |
| creado / actualizado en | `created_at` / `updated_at` |
| URL base | `base_url` |
| concluido | `concluded` |
| vigente | `current` / `is_current` |
| retirada | `retired_at` |
| eliminada (borrado lógico) | `deleted_at` |
| huella | `fingerprint` (módulo, `finding_type`, operación, identidad) |
| tipo de falla | `finding_type` |
| justificación | `justification` |
| advertencias | `warnings` |
| código (de error o advertencia) | `code` |
| página / tamaño | `page` / `page_size` |
| elementos | `items` |

## Base de datos y procesos

| Concepto | Identificador |
| --- | --- |
| Rol de BD dueño del esquema | `hindama_migrations` |
| Rol de BD de la API | `hindama_api` |
| Rol de BD del motor | `hindama_scanner` |
| Rol de BD del respaldo | `hindama_backup` |
| Variables de RLS | `app.user_id`, `app.cognito_sub`, `app.role` |
| Función de purga de la bitácora | `purge_audit_log()` |
| Canales de Redis | `run:{id}` (progreso), `cancel:{id}` (cancelación) |
| Cabeceras propias | `X-Request-Id`, `X-Hindama-Client-IP` |
