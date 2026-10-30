---
documento: Modelo de datos
proyecto: Hindama
version: 0.2
fecha: 2026-10-30
estado: propuesta para revisión
---

# Modelo de datos — Hindama v1.0

Este documento define las entidades que Hindama guarda en PostgreSQL 16, cómo se relacionan, los estados de las que los tienen y las reglas que **la base de datos** garantiza por sí misma. Es la base del esquema (migraciones de Alembic) y del contrato de la API ([`03-api/openapi.yaml`](../03-api/openapi.yaml)).

Los nombres de tablas, columnas y valores están en inglés ([ADR-017](../01-arquitectura/decisiones/ADR-017-identificadores-en-ingles.md)); la traducción de cada término está en el [glosario de identificadores](../03-api/glosario-identificadores.md). Las tablas van en plural.

Es un modelo **lógico**: nombra las columnas que importan para entender las reglas, no todas. Tipos exactos, longitudes, índices secundarios y valores por defecto se fijan en las migraciones (RNF-23). Si una migración contradice este documento, se corrige uno de los dos en el mismo pull request.

Los requerimientos citados (F, RF, RN, RNF) están en [`00-producto/requerimientos.md`](../00-producto/requerimientos.md); los casos de uso (CU), en [`00-producto/casos-de-uso.md`](../00-producto/casos-de-uso.md).

## 1. Decisiones de base

| Decisión | Resumen | Registro |
| --- | --- | --- |
| Identificadores | UUID v7 generados en la aplicación como llave primaria y en las URLs. Las ejecuciones llevan además un `number` consecutivo por proyecto para mostrarlo («Ejecución 3»). | [ADR-013](../01-arquitectura/decisiones/ADR-013-aislamiento-por-propietario-en-el-esquema.md) |
| Aislamiento por propietario | Llaves foráneas compuestas con `project_id` en cada tabla hija + Row-Level Security de PostgreSQL con el usuario de la petición fijado por transacción. | [ADR-013](../01-arquitectura/decisiones/ADR-013-aislamiento-por-propietario-en-el-esquema.md) |
| Seguimiento de hallazgos | Hallazgo lógico (único por huella) + ocurrencia por ejecución + evento por cambio de estado. Un hallazgo solo se resuelve si la ejecución volvió a evaluar exactamente su comprobación. | [ADR-014](../01-arquitectura/decisiones/ADR-014-seguimiento-de-hallazgos-por-huella-y-cobertura.md) |
| Borrado y retención | Borrado físico del proyecto y de la cuenta; borrado lógico de identidades; bitácora inmutable sin llaves foráneas y con el host en HMAC; métricas anónimas que sobreviven a cualquier borrado. | [ADR-015](../01-arquitectura/decisiones/ADR-015-borrado-retencion-y-anonimizacion.md) |
| Catálogos | Estados, módulos, severidades y demás listas cerradas como `text` + `CHECK`, no como `ENUM` de PostgreSQL: agregar un valor es una migración trivial. | — |
| Fechas | `timestamptz`, siempre en UTC. | — |
| Datos personales mínimos | La base de datos no guarda nombre ni correo del usuario: viven en Cognito. Solo guarda el `sub` de Cognito. | ADR-015 |

## 2. Diagrama entidad-relación

Las relaciones con `projects` se dibujan solo hacia las entidades principales; **todas** las tablas del bloque del proyecto llevan `project_id` (sección 5.1). `audit_log`, `finding_metrics` y `daily_metrics` no tienen llaves foráneas a propósito (sección 7).

```mermaid
erDiagram
    users ||--o{ projects : "es propietario de"
    projects ||--o{ contract_versions : "tiene versiones"
    projects ||--o{ operations : "declara"
    contract_versions ||--o{ operation_versions : "contiene"
    operations ||--o{ operation_versions : "aparece en"
    projects ||--|{ identities : "prueba como"
    identities ||--o{ resources : "es dueña de"
    operations |o--o{ identities : "es login de"
    projects ||--o{ runs : "ejecuta"
    contract_versions ||--o{ runs : "usada en"
    runs |o--o{ runs : "repite a"
    runs ||--o{ results : "evalúa"
    runs ||--o{ created_resources : "crea"
    operations |o--o{ results : "en"
    identities ||--o{ results : "como"
    projects ||--o{ findings : "acumula"
    operations |o--o{ findings : "afecta"
    identities ||--o{ findings : "detectado como"
    findings ||--|{ finding_occurrences : "detectado en"
    runs ||--o{ finding_occurrences : "detecta"
    findings ||--|{ finding_events : "historial"
    findings }o--|| finding_metrics : "alimenta"

    users {
        uuid id PK
        text cognito_sub UK
        timestamptz terms_accepted_at
        text terms_version
    }
    projects {
        uuid id PK
        uuid owner_id FK
        text name
        text base_url
        text host
        text verification_code UK
        text verification_status
        text verified_host
    }
    contract_versions {
        uuid id PK
        uuid project_id FK
        int number
        bytea document
        text sha256
        jsonb warnings
    }
    operations {
        uuid id PK
        uuid project_id FK
        text method
        text normalized_path
        text suggested_policy
        text policy
        text owner_field
        jsonb resource_parameters
        timestamptz retired_at
    }
    operation_versions {
        uuid contract_version_id FK
        uuid operation_id FK
        text path
        jsonb parameters
        jsonb security
        jsonb schemas
    }
    identities {
        uuid id PK
        uuid project_id FK
        text name
        text role
        text auth_type
        bytea encrypted_credential
        text credential_suffix
        text status
        timestamptz deleted_at
    }
    resources {
        uuid id PK
        uuid project_id FK
        uuid identity_id FK
        text resource_type
        text value
        text source
    }
    runs {
        uuid id PK
        uuid project_id FK
        int number
        text status
        text end_reason
        jsonb config
        timestamptz heartbeat_at
    }
    results {
        uuid run_id FK
        text module
        uuid operation_id FK
        uuid identity_id FK
        text expected
        text observed
        text verdict
    }
    created_resources {
        uuid id PK
        uuid run_id FK
        text location
        text status
        int attempts
    }
    findings {
        uuid id PK
        uuid project_id FK
        text module
        text finding_type
        uuid operation_id FK
        uuid identity_id FK
        text severity
        text status
        text dismissal_reason
    }
    finding_occurrences {
        uuid finding_id FK
        uuid run_id FK
        text severity
        jsonb evidence
    }
    finding_events {
        uuid id PK
        uuid finding_id FK
        text from_status
        text to_status
        text reason
        text justification
    }
    audit_log {
        bigint id PK
        timestamptz occurred_at
        uuid user_id
        text action
        uuid project_id
        bytea host_hmac
        inet source_ip
        jsonb details
    }
    finding_metrics {
        uuid id PK
        date week
        text module
        text owasp_category
        text cwe
        text severity
        int days_to_resolve
    }
    daily_metrics {
        date date PK
        text metric PK
        int value
    }
```

## 3. Entidades

### 3.1 Cuentas

**`users`** — Analista o administrador que entró al menos una vez. FastAPI lo da de alta en su primer acceso (`INSERT … ON CONFLICT (cognito_sub) DO NOTHING`, arquitectura 4.1).

| Campo | Notas |
| --- | --- |
| `id` | Identificador interno. Todo lo demás apunta a él, no al `sub`: si Cognito se recrea en la cuenta de respaldo, los datos se vuelven a ligar actualizando una columna. |
| `cognito_sub` | Único. |
| `terms_accepted_at`, `terms_version` | RF-16, RN-12. Nulos hasta que acepta. |

No se guarda el **rol**: sale del claim `cognito:groups` en cada petición (RN-04). Una copia en la base de datos sería una segunda fuente de verdad que puede quedar vieja. Tampoco se guardan nombre ni correo (datos mínimos, sección 7.2): `/me` obtiene el nombre de Cognito.

### 3.2 Proyecto y configuración

**`projects`** — Una API del analista (F-02).

| Campo | Notas |
| --- | --- |
| `owner_id` | → `users`. Base del aislamiento (sección 5.1). |
| `name`, `description` | RF-10: 100 y 500 caracteres; `CHECK` de longitud. |
| `base_url`, `host` | `host` lo extrae la aplicación de `base_url` (minúsculas, IDNA) y lo guarda aparte para que la base de datos pueda compararlo. |
| `verification_code` | RF-17. Aleatorio y único. No es secreto: el analista lo publica. |
| `verification_status` | `pending` / `verified` (sección 4.1). |
| `verification_method`, `verified_at`, `verified_host` | Se llenan al verificar. `verified_host` es el host exacto que la guardia SSRF permite (ADR-008). |

El estado **concluido** y el número de hallazgos abiertos **no se guardan**: se calculan (sección 4.4).

**`contract_versions`** — Cada importación del contrato OpenAPI (RF-26). Es inmutable.

| Campo | Notas |
| --- | --- |
| `number` | Consecutivo por proyecto; único `(project_id, number)`. |
| `document` | El archivo original tal como llegó (máx. 5 MB, RF-22), para reproducir una ejecución. |
| `source`, `source_url`, `format`, `openapi_version`, `sha256` | De dónde vino y qué es. |
| `warnings` | Lo que no se pudo interpretar y las referencias externas no seguidas (RF-23, RF-25, RF-27). |

**`operations`** — Una operación de la API **a nivel proyecto**, identificada de forma estable por `(method, normalized_path)`. Sobrevive a nuevas versiones del contrato, y por eso aquí viven la política y los parámetros de recurso.

| Campo | Notas |
| --- | --- |
| `method`, `normalized_path` | Único `(project_id, method, normalized_path)`. La ruta se normaliza sustituyendo el nombre de cada parámetro por `{}`: `/users/{id}` y `/users/{userId}` son la misma operación. |
| `suggested_policy` | Lo que sugiere el sistema (RF-40). |
| `policy`, `confirmed_at`, `modified_at`, `modified_by` | La política confirmada (RF-39, RF-43). Nula hasta que el analista confirma: el motor solo usa operaciones con `policy` no nula (RN-08). |
| `owner_field` | Obligatorio si la plantilla es `owner_only` o `owner_or_admin` (RF-41): `CHECK`. |
| `resource_parameters` | Qué parámetros de ruta identifican un recurso y de qué tipo (RF-35), con la corrección del analista. |
| `retired_at` | Se llena cuando una importación ya no la incluye; se limpia si reaparece. Una operación retirada con política es una «regla huérfana» que la interfaz señala. |

Las cinco plantillas (RF-39): `public`, `authenticated`, `owner_only`, `owner_or_admin`, `admin_only`.

**`operation_versions`** — El detalle de una operación tal como aparece en una versión concreta: ruta original, parámetros, esquemas de petición y respuesta, y seguridad declarada (RF-24). Llave `(contract_version_id, operation_id)`. Las diferencias entre versiones (RF-26) se calculan comparando estas filas.

**`identities`** — Cuenta de prueba en la API del analista (F-05).

| Campo | Notas |
| --- | --- |
| `name` | «Usuario A». |
| `role`, `role_label` | `role`: `admin` / `user` / `other` (lo usan los módulos de autorización, RF-57); `role_label`: texto libre (RF-28). |
| `auth_type` | `none` / `login` / `bearer` / `cookie` / `header` (RF-29). |
| `encrypted_credential`, `key_version` | AES-256-GCM con el `id` de la identidad como dato asociado (ADR-007). En `login` contiene usuario y contraseña juntos. |
| `credential_suffix` | Los últimos 4 caracteres, lo único que se muestra (RF-31). |
| `field_name` | Nombre de la cookie o de la cabecera. No es secreto. |
| `login_operation_id` | → `operations`. Endpoint de login para `login` automático (RF-30). |
| `status`, `last_tested_at`, `last_test_status_code` | `status`: `active` / `expired_credential` (RF-33). La prueba guarda solo el código de estado (RF-32). |
| `deleted_at` | Borrado lógico (sección 7.1). |

**La identidad anónima** (RF-34) es una fila real con `auth_type = none`, creada junto con el proyecto. Tener una fila real hace uniformes la huella, la matriz y las llaves foráneas. Reglas: a lo sumo una por proyecto (índice único parcial), sin credencial (`CHECK`), y no se puede eliminar (`CHECK deleted_at IS NULL` cuando `auth_type = none`).

**`resources`** — Un objeto de la API del analista que pertenece a una identidad (F-06).

| Campo | Notas |
| --- | --- |
| `identity_id` | Dueña del recurso. |
| `resource_type`, `value` | «pedido», «101». Único `(project_id, resource_type, value)`: un objeto tiene un solo dueño. |
| `source`, `confirmed` | `discovered` / `manual` (RF-36, RF-37). |

### 3.3 Ejecución y resultados

**`runs`** — Una corrida de uno o varios módulos (F-08).

| Campo | Notas |
| --- | --- |
| `number` | Consecutivo por proyecto; único `(project_id, number)`. |
| `contract_version_id` | La versión con la que se generaron las pruebas (RNF-19). |
| `source_run_id` | → `runs`. Lleno cuando es un «volver a probar» (RF-71). |
| `status`, `end_reason` | Sección 4.2. |
| `config` | Módulos, límites y confirmaciones de riesgo, tal como se validaron (RF-44, RF-46, RF-47). Repetir una ejecución es copiar este campo. |
| `created_at`, `started_at`, `finished_at`, `heartbeat_at`, `job_id` | `heartbeat_at` y `job_id` los usa la reconciliación (CU-23). |
| `requests_sent`, `current_module` | Foto del progreso para el SSE al reconectar (ADR-006). |

**`results`** — Una celda evaluada: `(run, module, operation, identity)`. Es a la vez la matriz identidad × operación (RF-64) y el registro de **qué se evaluó** que necesita la asignación de estados (sección 6).

| Campo | Notas |
| --- | --- |
| `operation_id` | Nulo en las comprobaciones de toda la API (por ejemplo, CORS en Configuración). |
| `expected`, `observed` | Lo que la política espera y lo que respondió la API (código y resumen). |
| `verdict` | `pass` / `fail` / `skipped` / `error`. Solo `pass` y `fail` cuentan como evaluada. `skipped` cubre la credencial vencida (RF-33) y los requisitos faltantes. |

Único `(run_id, module, operation_id, identity_id) NULLS NOT DISTINCT`. El motor escribe la celda **al terminar** de evaluarla: si existe, se evaluó completa. Una celda a medias por cancelación o caída no deja fila.

Las peticiones individuales **no** se guardan; solo las que respaldan un hallazgo, como evidencia de su ocurrencia.

**`created_resources`** — Lo que la plataforma creó en la API del analista y debe borrar (RN-06, RF-48). El motor anota la fila **antes** de crear el recurso (arquitectura 4.3).

| Campo | Notas |
| --- | --- |
| `operation_id`, `location` | Con qué operación se creó y la ruta para borrarlo. Sin credenciales. |
| `status`, `attempts`, `last_error` | `pending` / `deleted` / `failed`. Tras 3 intentos queda `failed` y se informa al analista (CU-23 E1). |

### 3.4 Seguimiento de hallazgos

**`findings`** — Una falla **lógica** del proyecto, que vive a lo largo de las ejecuciones (F-11).

| Campo | Notas |
| --- | --- |
| `module`, `finding_type`, `operation_id`, `identity_id` | La **huella** (RF-68). Único `(project_id, module, finding_type, operation_id, identity_id) NULLS NOT DISTINCT`. `finding_type` es un código del catálogo del módulo que incluye su calificador cuando hace falta distinguir (por ejemplo, `configuration.missing_header.hsts` o `sql_injection.parameter.q`). |
| `severity`, `owasp_category`, `cwe`, `title`, `recommendation` | De la ocurrencia más reciente (RF-62). |
| `status` | Sección 4.3. |
| `dismissal_reason`, `justification` | Solo en `accepted_risk`: `accepted_risk` / `false_positive` y su justificación obligatoria (RF-70, RN-09). `CHECK` de ambos. |
| `resolution_reason` | En `resolved`: `not_detected` / `identity_deleted` / `operation_retired`. |
| `detected_at`, `resolved_at`, `first_run_id`, `last_run_id` | Para el historial y la lista. |
| `metric_id` | → `finding_metrics` (sección 7.3). |

**`finding_occurrences`** — Una detección de un hallazgo en una ejecución, con su evidencia. Llave `(finding_id, run_id)`.

| Campo | Notas |
| --- | --- |
| `severity`, `explanation` | Como se evaluó en esa ejecución. |
| `evidence` | Petición y respuesta **ya enmascaradas y truncadas** por el motor antes de insertar (RF-66, RF-67, RN-11): cuerpo de respuesta ≤ 10 KB. |

**`finding_events`** — Cada cambio de estado (RF-72). Solo se inserta, nunca se modifica.

| Campo | Notas |
| --- | --- |
| `from_status`, `to_status`, `reason` | `reason`: `detected`, `not_detected`, `regression`, `accepted`, `false_positive`, `reverted`, `identity_deleted`, `operation_retired`. |
| `run_id`, `user_id` | Quién lo causó: una ejecución (cambio automático) o el analista (aceptar o revertir). |
| `justification` | Copia de la justificación en aceptaciones. |

### 3.5 Auditoría y métricas

**`audit_log`** — Acciones sensibles (F-14, RF-81, RF-82).

| Campo | Notas |
| --- | --- |
| `id` | `bigint` secuencial: nunca se expone a analistas y el orden importa. |
| `occurred_at`, `action`, `source_ip` | `action` del catálogo de RF-81, ampliado con `account_deleted`. |
| `user_id`, `project_id` | UUID **sin llave foránea**: deben sobrevivir al borrado de lo que señalan (sección 7). |
| `host_hmac`, `hmac_version` | HMAC-SHA256 del host del proyecto, en las acciones de verificación, ejecución y bloqueo. Sirve para investigar un abuso sin mostrar el host al administrador (ADR-015). |
| `details` | Módulos y límites de una ejecución, motivo de un bloqueo, etc. Nunca credenciales, justificaciones ni texto libre del analista. |

**`finding_metrics`** — Un hecho anónimo por hallazgo, para el panel del administrador (RF-78). Sin proyecto, usuario, host ni operación.

| Campo | Notas |
| --- | --- |
| `week` | Lunes de la semana en que se detectó. La semana, no la fecha, para dificultar cruzarlo con la bitácora. |
| `module`, `owasp_category`, `cwe`, `severity` | «Fallas más frecuentes». |
| `days_to_resolve`, `regressions` | «Tiempo promedio de detección a resolución». Nulo mientras no se resuelva. |

**`daily_metrics`** — Contadores agregados: `(date, metric) → value`. Indicadores: `new_users`, `deleted_accounts`, `projects_created`, `runs_started`. Se incrementan en la misma transacción que la acción.

## 4. Estados

### 4.1 Verificación del proyecto

```mermaid
stateDiagram-v2
    [*] --> Pendiente: Se crea el proyecto (CU-05)
    Pendiente --> Verificado: Código encontrado en el host (CU-07)
    Verificado --> Pendiente: Cambia el host de la URL base (RF-13)
    Verificado --> Pendiente: El código ya no está publicado al iniciar una ejecución (RF-20)

    Pendiente: Pendiente de verificación
```

Garantía en la base de datos: `CHECK (verification_status <> 'verified' OR (verified_host = host AND verified_at IS NOT NULL))`. Si la aplicación cambia la URL base a otro host y olvida volver el proyecto a `pending`, la actualización falla.

### 4.2 Ejecución

```mermaid
stateDiagram-v2
    [*] --> EnCola: El analista ejecuta (CU-12)
    EnCola --> EnCurso: El motor toma el trabajo
    EnCola --> Cancelada: El analista cancela
    EnCola --> Fallida: Perdida en la cola más de 10 min (CU-23)
    EnCurso --> Completada: Terminó o alcanzó un límite
    EnCurso --> Cancelada: El analista cancela o la verificación ya no es válida
    EnCurso --> Fallida: Latido vencido o error del motor
    Completada --> [*]
    Cancelada --> [*]
    Fallida --> [*]

    EnCola: en_cola
    EnCurso: en_curso
    Completada: completada
    Cancelada: cancelada
    Fallida: fallida
```

| Estado final | `end_reason` posibles |
| --- | --- |
| `completed` | `normal`, `limit_reached` (RF-47, CU-12 E5) |
| `cancelled` | `cancelled_by_user` (RF-52), `verification_invalid` (RF-20) |
| `failed` | `heartbeat_expired`, `lost_in_queue` (CU-23), `error` |

Garantías: índice único parcial `(project_id) WHERE status IN ('queued', 'running')` (RN-07); `CHECK` de que `end_reason` es nulo en los estados activos y no nulo en los finales, y de que corresponde al estado.

### 4.3 Hallazgo

```mermaid
stateDiagram-v2
    [*] --> Nuevo: Se detecta por primera vez
    Nuevo --> Persistente: Se detecta de nuevo
    Persistente --> Persistente: Se detecta de nuevo
    Regresion --> Persistente: Se detecta de nuevo
    Nuevo --> Resuelto: Se evaluó y no se detectó
    Persistente --> Resuelto: Se evaluó y no se detectó
    Regresion --> Resuelto: Se evaluó y no se detectó
    Resuelto --> Regresion: Se detecta otra vez
    Nuevo --> RiesgoAceptado: El analista lo acepta (CU-16)
    Persistente --> RiesgoAceptado: El analista lo acepta (CU-16)
    Regresion --> RiesgoAceptado: El analista lo acepta (CU-16)
    RiesgoAceptado --> Persistente: El analista revierte (CU-16)

    Regresion: Regresión
    RiesgoAceptado: Riesgo aceptado / falso positivo
```

- **Abiertos:** `new`, `persistent`, `regression`. **Cerrados:** `resolved`, `accepted_risk`.
- «Se evaluó» significa que la ejecución tiene una fila en `results` con veredicto `pass` o `fail` para la misma `(module, operation, identity)` (sección 6). Lo que no se evaluó conserva su estado.
- `Resuelto` también se alcanza, sin ejecución, si se elimina la identidad o se retira la operación (`resolution_reason`, sección 7.1).
- Un hallazgo en `accepted_risk` que se vuelve a detectar **sigue** aceptado; solo cambia su última ocurrencia.

### 4.4 Proyecto concluido (calculado)

Un proyecto está **concluido** si tiene al menos una ejecución `completed` y ningún hallazgo abierto (RN-10, RF-73). Se calcula con una consulta sobre índices; no se guarda, así que nunca queda desincronizado ni depende de que el motor lo actualice. Es independiente de la verificación: un proyecto puede estar concluido y pendiente de verificación a la vez.

## 5. Reglas que garantiza la base de datos

### 5.1 Aislamiento por propietario (RN-02, RNF-05)

Tres capas, de afuera hacia adentro:

1. **Repositorio de FastAPI:** toda consulta parte del proyecto del usuario; lo ajeno responde 404. Es la capa principal y tiene pruebas de acceso cruzado por endpoint.
2. **Row-Level Security:** aunque una consulta olvide el filtro, PostgreSQL no devuelve ni acepta filas ajenas.
3. **Llaves foráneas compuestas:** impiden que una fila de un proyecto apunte a una fila de otro. PostgreSQL revisa las FK **sin** aplicar RLS, así que esta capa es la que cierra las referencias cruzadas.

**Mecanismo de RLS** (detalle en [ADR-013](../01-arquitectura/decisiones/ADR-013-aislamiento-por-propietario-en-el-esquema.md)):

- Al abrir la transacción de cada petición, FastAPI ejecuta `set_config('app.cognito_sub', …, true)`, `set_config('app.user_id', …, true)` y `set_config('app.role', …, true)`. El tercer argumento `true` los limita a la transacción: al devolver la conexión al pool no queda ningún usuario fijado.
- Políticas para `hindama_api`:
  - `users`: `cognito_sub = current_setting('app.cognito_sub', true)`.
  - `projects`: `owner_id = NULLIF(current_setting('app.user_id', true), '')::uuid`.
  - Tablas hijas: `EXISTS (SELECT 1 FROM projects p WHERE p.id = project_id)`, que a su vez está filtrada por la política de `projects`.
  - `audit_log`: `INSERT` siempre; `SELECT` solo si `app.role = 'admin'`.
  - En todas, `USING` y `WITH CHECK` iguales: tampoco se puede **escribir** en un proyecto ajeno.
- **Falla cerrada:** sin la variable, `current_setting(…, true)` devuelve nulo y la política no deja ver nada.
- `hindama_scanner` tiene políticas permisivas (`USING (true)`): procesa ejecuciones de todos los analistas y no recibe entradas del usuario para elegir proyecto. Sus escrituras quedan limitadas por los privilegios de la sección 5.3 y por las FK compuestas.
- El **administrador** no es propietario de ningún proyecto, así que RLS le devuelve vacío cualquier tabla de proyecto aunque un endpoint fallara. Es una segunda barrera para RN-03 y RF-80, que FastAPI ya responde con 403. El panel de administración lee solo `metric_*` y `audit_log`.
- Las tablas pertenecen a `hindama_migrations`, que no se usa en tiempo de ejecución; por eso no hace falta `FORCE ROW LEVEL SECURITY`.

**Llaves foráneas compuestas:** cada tabla hija tiene `UNIQUE (project_id, id)` y sus referencias a otra tabla del proyecto son `(project_id, x_id) → x(project_id, id)`. Por ejemplo, `resources(project_id, identity_id) → identities(project_id, id)`. Todas las FK internas del proyecto usan `NO ACTION` (que se revisa al final de la sentencia), no `RESTRICT`, para que el borrado en cascada desde `projects` funcione en cualquier orden.

### 5.2 Tabla de reglas

| Regla | Mecanismo en la base de datos | Requerimiento |
| --- | --- | --- |
| Solo el dueño ve y modifica su proyecto | RLS + FK compuestas (5.1) | RN-02, RNF-05 |
| El administrador no ve contenido de proyectos | RLS: no es propietario de nada | RN-03, RF-80 |
| Una ejecución activa por proyecto | Índice único parcial en `runs` | RN-07, RF-53 |
| Verificado implica host verificado igual al actual | `CHECK` en `projects` (4.1) | RN-01, RF-13 |
| Un hallazgo por huella | Único `NULLS NOT DISTINCT` en `findings` | RF-68 |
| Una celda por ejecución, módulo, operación e identidad | Único en `results` | RF-64 |
| Aceptar un riesgo exige motivo y justificación | `CHECK` en `findings` | RF-70, RN-09 |
| Plantilla de propiedad exige campo de propietario | `CHECK` en `operations` | RF-41 |
| Una sola identidad anónima, sin credencial y que no se borra | Índice único parcial + `CHECK` en `identities` | RF-34 |
| Credencial presente si y solo si `auth_type <> 'none'` | `CHECK` en `identities` | RF-29 |
| Longitudes de nombre y descripción | `CHECK` en `projects` | RF-10 |
| `end_reason` coherente con el estado | `CHECK` en `runs` | RF-20, RF-47, RF-52 |
| Borrar un proyecto borra todo su contenido | `ON DELETE CASCADE` desde `projects` | RF-14 |
| La bitácora no se modifica | Sin `UPDATE`/`DELETE` para los roles de la aplicación + trigger que rechaza `UPDATE`, `TRUNCATE` y `DELETE` de filas dentro del plazo de retención | RF-83 |
| El historial de hallazgos no se modifica | `finding_events`: solo `INSERT` y `SELECT` para los roles de la aplicación | RF-72 |

### 5.3 Privilegios por usuario de base de datos

Ajusta la sección 5.2 de la arquitectura.

| Usuario | Privilegios |
| --- | --- |
| `hindama_migrations` | Dueño del esquema. Solo durante el despliegue. |
| `hindama_api` | Lectura y escritura en las tablas de la aplicación, con RLS. `audit_log` y `finding_events`: solo `INSERT` y `SELECT`. `metric_*`: `INSERT`, `UPDATE` y `SELECT`. |
| `hindama_scanner` | Lectura de la configuración del proyecto. Escritura en `runs`, `results`, `created_resources`, `findings`, `finding_occurrences`, `finding_events`, `metric_*` y `audit_log` (solo `INSERT`). `UPDATE` **solo** de las columnas de verificación de `projects` (RF-20) y de `status` de `identities` (RF-33). `EXECUTE` de `purge_audit_log()` (7.4). |
| `hindama_backup` | Solo lectura, con `BYPASSRLS` o como dueño de solo lectura, para que `pg_dump` vea todo. Se confirma en RDS al configurar. |

## 6. Asignación de estados al cerrar una ejecución

El motor lo hace en una sola transacción, después de borrar los recursos creados ([ADR-014](../01-arquitectura/decisiones/ADR-014-seguimiento-de-hallazgos-por-huella-y-cobertura.md)):

1. Por cada falla detectada en la ejecución, busca el hallazgo por huella:
   - No existe → lo crea en `new` y crea su `finding_metrics`.
   - Está en `new`, `persistent` o `regression` → pasa a `persistent`.
   - Está en `resolved` → pasa a `regression` y suma una regresión a su métrica.
   - Está en `accepted_risk` → no cambia.
   
   En todos los casos agrega una `finding_occurrences`.
2. Por cada hallazgo **abierto** del proyecto que no se detectó en esta ejecución: si existe un `results` con veredicto `pass` o `fail` para su `(module, operation, identity)`, pasa a `resolved` (`not_detected`) y se registra `days_to_resolve` en su métrica. Si no existe, no cambia.
3. Cada cambio inserta un `finding_events` con la ejecución como causa.

Esto vale también para ejecuciones canceladas o fallidas: lo que se alcanzó a evaluar completo cuenta (RF-52 conserva los resultados parciales). Como `results` solo existe para celdas completas, una cancelación a mitad de una celda no resuelve nada.

## 7. Borrado, baja de cuenta y retención

Detalle y justificación legal en [ADR-015](../01-arquitectura/decisiones/ADR-015-borrado-retencion-y-anonimizacion.md).

### 7.1 Qué se borra y qué se conserva

| Dato | Al eliminarlo | Por qué |
| --- | --- | --- |
| Proyecto | Borrado físico en cascada de todo su contenido (RF-14). Su `finding_metrics` queda, ya sin ningún vínculo. | El contenido incluye URLs, contratos y evidencias con datos que no se pueden anonimizar de forma fiable. |
| Identidad | Borrado **lógico**: en la misma transacción se borran `encrypted_credential` y `credential_suffix`, se llena `deleted_at` y sus hallazgos abiertos pasan a `resolved` con `identity_deleted`. Sus recursos se borran. | Los hallazgos, ocurrencias y resultados la referencian. Sin el cambio de estado, el proyecto nunca podría concluir. |
| Operación retirada del contrato | No se borra; se llena `retired_at` y sus hallazgos abiertos pasan a `resolved` con `operation_retired`. | Igual que la identidad. |
| Recurso, política de una operación | Borrado o cambio físico. | Configuración sin historial requerido. |
| Versión de contrato | No se borra mientras exista el proyecto. | RF-26. |
| Cuenta | Sección 7.2. | — |
| Bitácora | Se conserva 6 meses y luego se purga (7.4). | Investigación de incidentes y abusos. |
| Métricas | Se conservan sin límite. | Son anónimas: no son datos personales. |

### 7.2 Baja de cuenta y anonimización (ARCO)

El objetivo es **borrar a la persona y conservar las métricas**. La forma más segura de lograrlo es **anonimizar desde el diseño**, no en el momento de la baja:

- Las métricas del panel **nunca** apuntan a una persona: `finding_metrics` y `daily_metrics` no tienen usuario ni proyecto, usan semanas en lugar de fechas exactas y se escriben en el momento en que ocurre el hecho. La única liga es `findings.metric_id`, que va del hallazgo a la métrica: al borrarse el hallazgo, la liga desaparece con él.
- Por lo tanto, la baja **no necesita un proceso de anonimización**: basta con borrar. No hay un paso que pueda fallar a medias y dejar datos semianonimizados, y las métricas son idénticas antes y después de la baja.

Anonimizar en el momento de la baja (conservar los proyectos y borrar el `owner_id`) se descartó porque **no anonimiza**: una URL base, un contrato o una evidencia identifican a su dueño aunque se borre la columna del usuario, y pueden contener datos de terceros.

**Proceso de baja** (CU-25, RF-88):

1. El analista la solicita desde su perfil y confirma escribiendo su correo. Si tiene una ejecución activa, debe cancelarla primero.
2. En una sola transacción, FastAPI:
   - borra el `users`, y con él en cascada sus proyectos y todo su contenido;
   - incrementa `daily_metrics.deleted_accounts`;
   - registra `account_deleted` en la bitácora.
3. FastAPI borra la cuenta en Cognito con `DeleteUser` usando el access token del propio usuario (no requiere permisos IAM nuevos). Next.js elimina la cookie.

**Cómo se cumple cada derecho y el bloqueo** (ley vigente desde el 21 de marzo de 2025):

| Dato | Bloqueo (conservado, inaccesible para el uso normal) | Supresión |
| --- | --- | --- |
| Proyectos y su contenido | Solo en las copias de respaldo cifradas | A los 7 días, al rotar los respaldos (RNF-17); dentro de los 30 días de la sección 11 de requerimientos |
| Cuenta en Cognito | — | Inmediata |
| Bitácora (UUID opaco, IP, HMAC del host) | Solo la consulta el administrador para investigar incidentes y abusos | A los 6 meses del evento |
| Métricas | No aplica: no son datos personales | — |

Acceso, rectificación y oposición se atienden por el correo del equipo, como indique el aviso de privacidad. El analista ya ve y modifica sus propios datos en la plataforma, y su nombre y correo se rectifican en Cognito.

### 7.3 Cómo se alimentan las métricas

- **Hallazgo nuevo** → se inserta su `finding_metrics` (semana, módulo, OWASP, CWE, severidad).
- **Hallazgo resuelto** → se llena `days_to_resolve`, la primera vez que se resuelve.
- **Regresión** → se suma a `regressions`.
- **Alta de usuario, proyecto creado, ejecución lanzada o cuenta eliminada** → se incrementa el indicador del día en `daily_metrics`.

RF-78 se responde solo con estas tablas: usuarios, proyectos y ejecuciones por periodo; fallas frecuentes por módulo y OWASP; promedio de `days_to_resolve`.

### 7.4 Retención de la bitácora

- La función `purge_audit_log()` (`SECURITY DEFINER`, dueña `hindama_migrations`) borra las filas con más de 6 meses. La ejecuta la tarea periódica del motor (CU-23).
- El trigger de inmutabilidad permite `DELETE` solo de filas fuera del plazo, y rechaza siempre `UPDATE` y `TRUNCATE`. Ni siquiera un error de la aplicación puede borrar un evento reciente.

## 8. Lo que la base de datos no puede garantizar

Estas reglas dependen de la aplicación y deben tener pruebas propias:

- **Enmascarado de la evidencia** (RN-11, RF-66): el motor enmascara antes de insertar. La base de datos no sabe qué es una credencial.
- **Cifrado de credenciales** (RNF-06): la base de datos solo ve `bytea`.
- **Que `host` sea el host real de `base_url`:** lo calcula la aplicación. El `CHECK` de la sección 4.1 depende de que sea correcto.
- **Fijar las variables de RLS en cada transacción:** si FastAPI no las fija, la política devuelve vacío (falla cerrada), pero conviene una prueba que lo detecte en lugar de descubrirlo como una lista vacía.
- **Consistencia entre `config` y lo ejecutado:** `config` es `jsonb`; su esquema lo valida Pydantic.
- **La exactitud del catálogo `finding_type`:** si un módulo cambia el código de una falla entre versiones, la huella cambia y el hallazgo aparece como nuevo (RNF-24).

## 9. Supuestos

| Supuesto | Si falla |
| --- | --- |
| UUID v7 se genera en Python; PostgreSQL 16 no lo trae nativo. | Usar UUID v4: se pierde la localidad del índice, sin efecto a esta escala. |
| RLS con `set_config(…, true)` funciona con SQLAlchemy asíncrono y asyncpg sin pool externo. | Se valida en la semana 1 junto con las pruebas técnicas. Si hubiera fugas entre transacciones, fijar las variables en un evento `begin` de la sesión. |
| El volumen cabe holgado: en el peor caso, unas 17,500 filas de `results` por ejecución (500 operaciones × 5 identidades × 7 módulos). | Guardar en `results` solo los módulos de autorización y agregar una tabla de cobertura por módulo. |
| `hindama_backup` puede obtener `BYPASSRLS` en RDS. | Hacer el respaldo con el usuario dueño del esquema. |
| El nombre del usuario para `/me` se obtiene de Cognito con `GetUser` y el access token. | Copiar el nombre a `users` en el primer acceso y borrarlo en la baja. |
| 6 meses de bitácora alcanzan para investigar un reporte de abuso. | Ampliar el plazo y declararlo en el aviso de privacidad. |
