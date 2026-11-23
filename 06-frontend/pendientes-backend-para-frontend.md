---
documento: Pendientes del backend para conectar todo el frontend
proyecto: Hindama
version: 1.6
fecha: 2026-11-23
estado: vigente; verificado punto por punto contra el contrato 0.10.0 (hindama-docs 0f50296), el backend develop (f50ad22, reconstruido con Docker) y el frontend dev (fases 0 a 8, más el trabajo de la fase 9 en revisión)
---

# Pendientes del backend para conectar todo el frontend

Qué le falta al backend (y al contrato) para que **todas** las vistas del frontend dejen de usar datos fijos o simulados, y qué hace el frontend cuando llegue cada cosa. Está escrito para quien implemente el backend: cada pendiente trae la vista que lo necesita, el requerimiento, la evidencia en el código y una propuesta de cambio al contrato.

Las propuestas de contrato son **propuestas**: se acuerdan en un pull request a `hindama-docs` (ADR-016) antes de implementarse.

## 1. Estado de partida

- El backend implementa las **39 operaciones** del contrato 0.7.0 (CHANGELOG 0.1.0, «39 de 39»): las `operationId` de `src/hindama/api/*.py` coinciden con las de `03-api/openapi.yaml`. La 39.ª es `listAuditLog`, la bitácora del administrador.
- El frontend conecta por el BFF todas las vistas con contrato: V-23 (PR #14) y V-34 (PR #15) ya están en `dev`, y V-33 con el contrato 0.10.0 queda en los PR de la fase 9. Ver [inventario](inventario-endpoints-vistas-observaciones.md), secciones 1 y 10 a 19.
- Lo que sigue **simulado o fijo** en el frontend es lo que el contrato 0.7.0 no cubre. Eso es este documento.
- El separador de roles ya existe: el rol sale del grupo `administradores` de Cognito (`config.py:81`, `core/auth.py:121`), `GET /me` lo devuelve y las rutas de proyectos usan el guardia `Analyst` (403 `role.forbidden` para un administrador, RF-80). El guardia `Admin` (`api/dependencies.py:72`) existe, pero **ninguna ruta lo usa**.

### Qué cambió en la versión 1.5 (23/11/2026): verificación contra el contrato y el código

Se comprobó cada pendiente de este documento contra `03-api/openapi.yaml` 0.10.0, el código de `hindama-backend` (`develop`, `f50ad22`) y la API en marcha (`docker compose up -d --build --wait`: `GET /openapi.json` responde `info.version: 0.10.0`, 40 operaciones, con `/admin/stats`; sin token responde 401). Las 40 `operationId` de `src/hindama/api/*.py` son exactamente las del contrato.

| Pendiente | ¿Resuelto? | Evidencia |
| --- | --- | --- |
| A1 · estadísticas del administrador (V-33) | **Sí** | `getAdminStats` en el contrato 0.9.0 y en `api/admin.py`, con el guardia `Admin` (ya lo usan las dos rutas de `/admin`); servicio `services/stats.py` y pruebas `tests/integration/test_admin_stats.py`. **Frontend: conectado en la fase 9** (ruta BFF `/api/admin/stats`, vista V-33) |
| A2 · bitácora (V-34) | **Sí** | `listAuditLog`. Conectada en la fase 8 (PR #15 del frontend) |
| B20 · módulos sin implementar | **Sí** | Los siete módulos existen en `scanner/modules/`; `IMPLEMENTED_MODULES` los tiene todos, así que `not_implemented` ya no sale en `modules[].missing`. El frontend ya acepta el valor (E7) |
| B12 (parte) · recursos sin borrar | **En parte** | `created_resources.failed_items` (`operation_id`, `location`, `last_error`) está en el contrato y en `api/runs.py`. Siguen sin existir `Run.modules_result[]` y `Run.comparison` |
| D1 · `deleteIdentity` | **Sí** | Contrato 0.8.0. El texto del frontend ya lo dice (E7) |
| D2 · respuestas cerradas | **En documentación** | `convenciones.md` v0.9. El frontend valida con los mismos enums del contrato fijado; tratar un valor desconocido como genérico en tiempo de ejecución queda sin hacer (ver el inventario, sección 18) |
| E1 a E3 y E5 | **Sí** | Descubrir recursos (PR #14), bitácora (PR #15), celda de la matriz y evidencia del reporte (PR #16) |
| E4 · cambiar contraseña y MFA desde el BFF | **No** | Sin pantalla ni rutas `/api/auth/password/change` ni `/api/auth/mfa/*`; A5 además espera la configuración del pool en AWS |
| E6 a E9 | **Sí, en revisión** | Contrato 0.10.0, `not_implemented`, `failed_items`, claves nuevas de `context` y V-33: PR [#17](https://github.com/lsprz2773/Hindama-Front/pull/17) y [#18](https://github.com/lsprz2773/Hindama-Front/pull/18) del frontend |
| A3 · baja de cuenta | **No** | El contrato no tiene `DELETE /me`; `account_deleted` sigue reservada y `deleted_accounts` vale 0 |
| A4 · exportar a Excel | **No** | Ninguna ruta de exportación en el contrato |
| A5 · segundo factor (V-05, V-10, V-11) | **No** | Sin cambios en el contrato ni en el backend; falta configurar MFA en el pool de Cognito (AWS) |
| A6 · acceso de administradores (V-35) | **No** | El backend valida un solo pool (`config.py`: `cognito_user_pool_id`). La decisión del 06/11/2026 es un segundo pool con MFA obligatorio: falta crearlo en AWS y que el backend acepte dos emisores. No hay contrato que conectar |
| A7 · cambiar contraseña, A8 · versión pública de los términos | **No** | A7 es Cognito desde el BFF y espera decisión de producto; A8 no tiene operación pública |
| B1 a B11, B13 a B19 y B21 | **No** | Ninguno de los campos, filtros u operaciones propuestos está en el contrato (`mfa_enabled`, `active_run`, `counts`, `identities/test`, `confirmed`, `identity_ids`, `modules_result`, `comparison`, `retest`, `expected_policy`, `open_findings_at_end`, `runs_total`… no aparecen) |

Con lo anterior, **todas las vistas que tienen contrato quedan conectadas** una vez que se mezclen los PR #17 y #18 del frontend. Siguen simuladas solo las que dependen de A3, A5, A6 y A7: V-05, V-10, V-11, V-35, C-14 y C-17.

### Qué cambió en la versión 1.4 (23/11/2026): los siete módulos

| Pendiente | Qué se hizo | Dónde | Qué toca en el frontend |
| --- | --- | --- | --- |
| B20 · módulos sin implementar | Ya existen los tres: propiedades (API3), consumo de recursos (API4) e inyección SQL. `not_implemented` ya no aparece en `modules[].missing` | Backend; catálogo del laboratorio 1.5; guía §5.2 | Nada obligatorio: deja el texto de `not_implemented` para un módulo futuro |
| B12 (parte) · recursos sin borrar | `created_resources.failed_items`: ruta, operación y motivo de cada recurso que el analista debe borrar a mano | `openapi.yaml` 0.10.0; guía §5.8 | E9 |
| Evidencia nueva | `request.body` (asignación masiva y límite de cuerpo) y claves nuevas de `context` | `openapi.yaml` 0.10.0; guía §5.9 | E9 |

**Cambia el hash del contrato** (0.9.0 → 0.10.0). E9 incluye a E7 y E8 si todavía no se hicieron.

### Qué cambió en la versión 1.3 (23/11/2026): estadísticas del administrador

| Pendiente | Qué se hizo | Dónde | Qué toca en el frontend |
| --- | --- | --- | --- |
| A1 · panel de estadísticas (V-33) | `GET /admin/stats` (`getAdminStats`), solo para el administrador. Trae los seis indicadores de la vista, la actividad por día o semana y los hallazgos por módulo, categoría OWASP, severidad y semana, todo de métricas anónimas | `openapi.yaml` 0.9.0; guía v0.12, §5.11; backend | E8 |

**Cambia el hash del contrato** (0.8.0 → 0.9.0). Si todavía no hiciste E7, sáltatelo y haz directamente E8, que lo incluye.

### Qué cambió en la versión 1.2 (23/11/2026): correcciones para la conexión

Respuesta del backend a la versión 1.1. Todo está en `hindama-docs` (rama `docs/correcciones-conexion`) y en `hindama-backend` (rama `feature/RF-45-conexion-frontend`), con el contrato **0.8.0**:

| Pendiente | Qué se hizo | Dónde | Qué toca en el frontend |
| --- | --- | --- | --- |
| 9.1 · generador del `.env` | El script cambia **cada** `cambia-esto-por-32-bytes-en-base64` por una llave propia, así que la de credenciales y la de la bitácora salen distintas (probado contra `.env.example`). Para un `.env` viejo, un bloque que agrega `HINDAMA_AUDIT_HMAC_KEYS` y `HINDAMA_AUDIT_HMAC_KEY_VERSION` sin regenerarlo | `entorno-local.md` v1.1, §4 | Si tu `.env` es anterior al 23/11, agrega las dos variables con ese bloque y reconstruye |
| 9.1 · `entorno-local.md` desfasado | Encabezado al día; §8.1 ya no repite el estado por vista y remite al inventario y a este documento | `entorno-local.md` v1.1 | Nada |
| 9.1 · versiones del README | Guía v0.11, convenciones v0.9, entorno v1.1, modelo v0.5, contrato 0.8.0 | `README.md` | Nada |
| 9.1 · inventario | Lo resolvió tu PR #40 (fase 8) | `inventario-…md` | Nada |
| D1 · `deleteIdentity` | Manda el backend (RF-69): el contrato ya dice que los hallazgos **se conservan, pero los abiertos pasan a resueltos con `identity_deleted`** | `openapi.yaml` 0.8.0 | Cambiar el texto de `es.json` (`item2`, `deleteNote`): «Sus hallazgos abiertos se marcarán como resueltos» |
| D2 · respuestas cerradas | Aclarado: `additionalProperties: false` obliga al backend (su CI); el cliente ignora campos que no conoce **y trata un valor de enum desconocido como genérico** | `convenciones.md` v0.9, §1 y §2 | Que ningún `z.enum` de respuesta rompa con un valor nuevo |
| B20 · módulos sin implementar | `modules[].missing` gana `not_implemented` para `property_access`, `resource_consumption` y `sql_injection`; lanzarlos responde 422 `run.module_unavailable` | `openapi.yaml` 0.8.0; guía §5.2; backend | Agregar `not_implemented` al esquema y al texto de V-16 y V-25: «Disponible en una versión próxima» (ver E7) |
| C2 · métricas diarias | Se cuentan `runs_started` (lanzar o repetir), y dos nuevas: `runs_cancelled` y `runs_failed` (en la API, el motor y la reconciliación). Queda `deleted_accounts`, que llega con A3 | `modelo.md` v0.5 §7.3; backend, migración `7c4e1a2b9d30` | Nada todavía: las usará A1 |

**Cambia el hash del contrato** (0.7.0 → 0.8.0): ver E7.

### Qué cambió en la versión 1.1 (23/11/2026)

Llegaron el contrato 0.7.0 (`hindama-docs` b1c1993) y el backend 0.1.0 (`hindama-backend` c1866dd):

| Antes (v1.0) | Ahora | Efecto |
| --- | --- | --- |
| A2: bitácora sin contrato ni ruta | `GET /admin/audit-log` (`listAuditLog`), contrato 0.7.0, implementada | Solo falta el frontend (E5) |
| C1: nada escribía en `audit_log` | Se registran 12 de las 13 acciones del catálogo (`account_deleted` está reservada) | Resuelto, salvo la baja de cuenta (A3) |
| C3: el backend no leía `X-Hindama-Client-IP` | La lee y la guarda si es una IP válida | Resuelto |
| C4: índices y retención | Migración `30d24d99dab2` del catálogo de acciones; la purga de 6 meses ya corría | Resuelto |
| D3: `convenciones.md` y la guía no coincidían sobre la IP | Convenciones v0.8 y guía v0.10 dicen lo mismo | Resuelto |
| C2: faltan métricas diarias | Igual: solo se incrementan `new_users` y `projects_created` | Sigue abierto |
| A1, A3, A4, A5 | El CHANGELOG 0.1.0 los deja en «Fuera de esta versión»: estadísticas (CU-20), baja de cuenta (CU-25), reportes y Excel (CU-18, CU-19) y 2FA TOTP (CU-22) | Siguen abiertos |

## 2. Resumen

| Grupo | Qué es | Pendientes |
| --- | --- | --- |
| A | Funciones sin contrato (rutas u operaciones nuevas) | A3 a A8 (A1 y A2 ya tienen contrato y backend) |
| B | Campos, filtros y operaciones que se agregan a lo ya existente | B1 a B19 y B21 (B20 resuelto; de B12, la lista de recursos sin borrar ya está en 0.10.0) |
| C | Trabajo interno del backend que ya tiene requerimiento | C2 parcial: falta `deleted_accounts`, con A3 (C1, C3 y C4 resueltos) |
| D | Contradicciones entre contrato, guía y código | Ninguna (D1, D2 y D3 resueltos) |
| E | Lo que el frontend puede hacer ya, sin esperar al backend | E1 a E11 |

Prioridad sugerida (a la entrega de finales de noviembre): en el frontend, E8 (contrato 0.9.0 y V-33); en el backend, A3, A4 y A5 en el contrato 0.10.0; B según el tiempo. Orden en la sección 7.

## 3. Grupo A · Funciones sin contrato

### A1 · Panel de estadísticas del administrador (V-33, F-13) · contrato y backend listos

- **Requerimientos:** RF-78, RF-79, RF-89. Prioridad baja.
- **Estado:** resuelto en el contrato 0.9.0 y en el backend: `GET /admin/stats` (`getAdminStats`), solo para el administrador (403 `role.forbidden` al analista). Guía §5.11. Falta conectar la vista (E8).
- **Cómo cubre lo que pinta la vista hoy** (`stats-view.tsx`, `STATS`):
  - **El periodo:** `date_from`, `date_to` y `group` (`day` o `week`) en lugar de `period`. Para «7, 30 o 90 días», envía solo `date_from` (hoy menos 6, 29 u 89 días).
  - **Los seis indicadores:** `users.total` y `users.new`; `projects.created`; `runs.started` con `cancelled` y `failed`; `findings.average_days_to_resolve` (puede ser `null`); `users.deleted` (vale 0 hasta A3); y `findings.regressions`.
  - **La serie de hallazgos** es `findings.weekly` y **siempre va por semana**: la API no guarda la fecha exacta de un hallazgo (RF-89). La vista hoy usa `unit: "day"` para 7 días; con 7 días habrá una o dos semanas. La serie diaria que sí existe es `activity`, con usuarios, proyectos y ejecuciones.
  - **Por módulo y por OWASP:** `findings.by_module` y `findings.by_owasp_category`, de más a menos frecuente. Además trae `findings.by_severity`.
- **Usuarios totales (decidido):** son las altas menos las bajas desde el inicio de la plataforma, hasta `date_to`. Salen de `daily_metrics`, sin consultar la tabla de usuarios.

### A2 · Bitácora de auditoría (V-34, F-14) · contrato y backend listos

- **Requerimientos:** RF-81 a RF-84, RF-90. Prioridad media.
- **Estado:** **resuelto en el backend y el contrato.** `GET /admin/audit-log` (`listAuditLog`, contrato 0.7.0; `api/admin.py:55`, `services/audit.py`), solo para el administrador (403 `role.forbidden` al analista). Guía §5.10. Falta conectar la vista (E5).
- **Lo que trae.** Cada registro: `id` (entero), `occurred_at`, `action`, `user_id`, `project_id`, `source_ip` (puede ser `null`) y `details`. Filtros: `occurred_from` y `occurred_to` (RFC 3339 con zona), `action` (repetible), `user_id` (UUID exacto), `host` (el servidor calcula el HMAC y nunca lo devuelve), `page` y `page_size` (20 por defecto, hasta 100).
- **Acciones que se emiten (12 de 13).** `account_created`, `project_created`, `project_deleted`, `project_verified`, `project_verification_lost`, `identity_created`, `identity_deleted`, `run_launched`, `run_cancelled`, `finding_dismissed`, `finding_dismissal_reverted` y `destination_blocked`. **`account_deleted` está reservada y todavía no se emite** (depende de A3).
- **Decisiones que resolvió el contrato:**
  - «Usuario eliminado»: la API **no** lo informa. `user_id` es opaco y la API no guarda nombres ni correos; la vista muestra el identificador (la guía propone que un clic en él lo use como filtro).
  - Los detalles de cada acción son un objeto tipado (`AuditDetails`: `run_id`, `source_run_id`, `modules`, `limits`, `verification_method`, `identity_id`, `finding_id`, `dismissal_reason`, `stage`, `block_reason`), nunca texto libre ni justificaciones (RF-83).
  - La llave del HMAC del host vive en SSM (`/hindama/backend/audit-hmac-keys`), versionada (`HINDAMA_AUDIT_HMAC_KEYS`).
- **Lo que ya no cuadra entre la vista y la API** (para conectar V-34, ver E5): el catálogo de acciones (la vista tiene 11; la API, 13), el filtro por usuario (la vista acepta correo o un fragmento; la API solo el UUID completo), el filtro de fechas (la vista usa días; la API pide inicio y fin con zona), la huella del host (la API no la devuelve), la bandera «eliminado» y el correo del usuario (la API no los trae) y la paginación (la vista pagina en el navegador).

### A3 · Baja de cuenta (C-14, RF-88)

- **Frontend hoy:** no hay pantalla ni diálogo.
- **Backend hoy:** el contrato no tiene `DELETE /me` y CU-25 está en «Fuera de esta versión». La acción `account_deleted` de la bitácora ya está en el catálogo, pero «todavía no se emite».
- **Propuesta:** `DELETE /me` con confirmación escrita del correo (como `deleteProject` con `confirmation`). Debe: rechazar con 409 si hay ejecuciones activas, borrar la cuenta en Cognito, el registro de usuario y todos sus proyectos con su contenido (ADR-015), conservar métricas anónimas y bitácora, sumar `deleted_accounts` (C2) y registrar `account_deleted` (C1). Requiere permiso de la API para borrar usuarios del pool (AWS: lo configura el equipo de backend; no lo hice).
- **Frontend cuando llegue:** diálogo en el perfil (C-07, eliminación con confirmación escrita), ruta BFF, borrar la cookie de sesión y llevar a V-01 con el aviso «cuenta eliminada».

### A4 · Exportar hallazgos a Excel (RF-77)

- **Frontend hoy:** se quitó el botón «Exportar a Excel» de V-27, V-29 y V-32 (comentarios `TODO(api)` en `findings-view.tsx:343` y `report-view.tsx:353`).
- **Backend hoy:** no existe (CU-18 y CU-19, reportes y exportación a Excel, están en «Fuera de esta versión» del CHANGELOG 0.1.0).
- **Propuesta:** `GET /projects/{project_id}/findings/export` con los mismos filtros de `listFindings`, que responde `.xlsx` (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`). Evidencia enmascarada (RN-11). Hay que definir qué columnas lleva y un tope de filas.
- **Frontend cuando llegue:** el BFF debe relevar un cuerpo binario (hoy `apiRoute` maneja JSON), y un botón con descarga y espera.

### A5 · Segundo factor TOTP (V-05, V-10, V-11, F-15)

- **Requerimientos:** RF-85, RF-86, RF-87. Prioridad baja, «fase final».
- **Frontend hoy:** simulado en `account/service.ts` (`confirmTwoFactor`, `disableTwoFactor`, `verifyLoginTwoFactor`; clave `TOTP_SECRET_STUB` y QR de relleno).
- **Backend hoy:** el MFA está **desactivado** en el pool de Cognito (guía §2.2). CU-22 (2FA TOTP) está en «Fuera de esta versión» del CHANGELOG 0.1.0. No hay nada en FastAPI.
- **Cómo encaja:** el MFA lo maneja Cognito y el BFF habla con Cognito, igual que el registro y el inicio de sesión (`/api/auth/*`). Por eso **no necesita rutas nuevas en FastAPI**, salvo lo de abajo. El BFF usaría `AssociateSoftwareToken`, `VerifySoftwareToken`, `SetUserMFAPreference` y `RespondToAuthChallenge` (`SOFTWARE_TOKEN_MFA`).
- **Necesita, en AWS (lo hace el equipo de backend):** activar MFA opcional con TOTP en `hindama-dev` y en producción.
- **Necesita, en el backend o el contrato (opcional):** un campo `mfa_enabled` en `Me` si no se quiere leerlo de Cognito desde el BFF.
- **Decisión abierta (RF-86):** exigir el segundo factor a los administradores. Cognito no lo obliga por grupo, así que hay que decidir dónde se aplica: en el BFF (rechazar una sesión de administrador sin MFA) o en la API (rechazar el token sin el factor).
- **Frontend cuando llegue:** rutas `src/app/api/auth/mfa/*`, quitar `TOTP_SECRET_STUB` y el QR de relleno (generarlo del `otpauth://` real) y atender el reto en `sign-in-form.tsx` (hoy el BFF responde `auth.failed` si Cognito lo pide).

### A6 · Acceso de administradores (V-35, V-11)

- **Frontend hoy:** `adminSignIn` espera 500 ms y deja pasar.
- **Backend hoy:** valida un solo pool de Cognito. El pool de administradores es solo una propuesta en `arquitectura.md`.
- **Decisión que falta:** pool aparte o el mismo pool con el grupo `administradores`. Con el mismo pool, `/admin/sign-in` puede usar el mismo flujo del BFF (`/api/auth/sign-in`) y comprobar el rol con `getMe`, sin cambios en FastAPI; el problema que queda es A5 (MFA obligatorio).
- **Si es un pool aparte:** hay que crearlo en AWS, configurar su cliente y que el backend valide dos emisores.

### A7 · Cambiar contraseña (C-17)

- **Frontend hoy:** no hay pantalla.
- **Backend hoy:** no hay endpoint, y **no hace falta uno en FastAPI**: es Cognito `ChangePassword` desde el BFF con el access token de la sesión (requiere decisión de producto, el inventario dice «Decidir»).
- **Frontend cuando llegue:** `change-password-dialog.tsx`, ruta `src/app/api/auth/password/change`, mismas reglas de contraseña que el registro (RF-03).

### A8 · Versión pública de los términos (V-07)

- **Frontend hoy:** sin sesión muestra una versión fija: `PUBLISHED_TERMS_VERSION = "2026-10-30"` (`legal/terms-version.tsx`). Con sesión usa `terms.current_version` de `getMe`.
- **Backend hoy:** solo `getMe` informa la versión y exige sesión.
- **Propuesta (opcional):** una operación pública con la versión vigente, o mantener el acuerdo manual de la guía §5.1 (cada cambio de versión se avisa al frontend).

## 4. Grupo B · Campos, filtros y operaciones sobre lo existente

Todo esto es un **cambio compatible** (MINOR, `0.7.0`): se agregan campos y parámetros opcionales y el frontend ignora lo que no conoce. Las vistas funcionan sin ellos, con la función quitada o parcial.

| ID | Vista | Qué falta hoy | Propuesta | Req. |
| --- | --- | --- | --- | --- |
| B1 | V-09, V-10 | `Me` trae `id, name, email, role, terms`: no hay «Miembro desde» ni estado del 2FA | `created_at` y `mfa_enabled` en `Me` | RF-85 |
| B2 | V-13 | Sin buscador, sin totales de hallazgos abiertos y de proyectos por verificar si no caben en la página, sin insignia «en ejecución». `listProjects` solo tiene `page`, `page_size`, `sort` | Filtro `q` en `listProjects`; `active_run` en `ProjectSummary`; totales agregados en `ProjectPage` (`open_findings_total`, `pending_verification_total`) | RF-12 |
| B3 | V-15 | Sin aviso de nombre repetido: `createProject` no define 409 por nombre | Decidir si el nombre debe ser único por analista; si sí, 409 `project.name_taken` | RF-10 |
| B4 | V-16, V-17, C-03 | `Project` no trae el porcentaje de política confirmada, ni hallazgos por módulo, ni cuántas versiones, identidades, recursos, operaciones o ejecuciones hay | `Project.counts` con `operations` (total y confirmadas), `identities`, `resources`, `contracts`, `runs`; resumen por módulo en `last_run` | RF-45 |
| B5 | V-19, V-24 | Sin buscador de operaciones, sin respuestas ni conteo de esquemas por operación, sin autor de la última modificación de la política | Filtro `q` en `listOperations`; `responses` y `schema_count` en `Operation`; `modified_by` en `Operation` | RF-43 |
| B6 | V-20 | Solo se ve una versión frente a la anterior (`ContractVersion.changes`) | Operación para comparar dos versiones, por ejemplo `GET /projects/{project_id}/contracts/diff?from=…&to=…` | RF-26 |
| B7 | V-22 | No se puede probar una credencial antes de guardarla: `testIdentity` exige una identidad ya creada | Operación de prueba sin guardar (`POST /projects/{project_id}/identities/test` con el mismo cuerpo que `IdentityCreate`). Cuidado: la credencial viaja y no se guarda; mismas reglas SSRF | RF-32 |
| B8 | V-23 | Sin contador «Por confirmar» del proyecto: `listResources` solo filtra por `identity_id` y `resource_type` | Filtro `confirmed` y conteos por estado en `ResourcePage` | RF-37 |
| B9 | V-24 | No se puede quitar la política de una operación retirada: `updateOperation` y `applyPolicy` responden 409 `operation.retired` (`services/policy.py:92,177`) | Permitir limpiar la política de una operación retirada (o `DELETE …/operations/{operation_id}/policy`) | — |
| B10 | V-25 | `RunCreate` solo lleva `modules`, `limits`, `confirm_risk`: no se eligen identidades | `identity_ids` opcional en `RunCreate` (sin él, todas) | — |
| B11 | V-26 | `RunProgress` es global (`current_module`, `cells_planned`, `cells_evaluated`, `percent`): sin avance por módulo y sin avisos de credencial vencida o de peticiones bloqueadas por 429 | `modules[]` en `RunProgress` con avance y hallazgos por módulo, y contadores o eventos de credencial vencida y de 429 | RF-51 |
| B12 · **en parte (0.10.0: `failed_items`)** | V-26, V-27, V-32 | `Run` no trae resultados por módulo (hallazgos, omitidos, credenciales vencidas), ni la comparación con la ejecución anterior (nuevos, persistentes, resueltos, regresiones), y `created_resources` solo trae contadores | `Run.modules_result[]`, `Run.comparison` y `created_resources.items[]` (operación, ubicación y último error de cada recurso sin borrar) | RF-52, RF-72 |
| B13 | V-28 | `Result` no trae `finding_id`, ni el rol de la identidad ni la plantilla de política de la operación | `finding_id`, `identity.role` y `operation.policy` (ver también E2: la celda ya puede abrir el hallazgo) | RF-64 |
| B14 | V-28, V-32 | `expected` y `observed` son texto libre: no hay lista cerrada. Además `observed` no siempre es un código simple: `scanner/modules/object_access.py:118` genera `"200 own_data_only"` y `configuration.py:151` une códigos con coma | Publicar un enum o una lista de códigos en el contrato, y separar el código de los datos (`observed` y `observed_status`) | RF-64 |
| B15 | V-29 | Sin filtro por motivo de descarte: `listFindings` no tiene `dismissal_reason` y `FindingSummary` no trae `dismissal` | Filtro `dismissal_reason`; `dismissal.reason` en `FindingSummary` | RF-70 |
| B16 | V-30 | Sin «Volver a probar» un solo hallazgo | `POST /projects/{project_id}/findings/{finding_id}/retest` (lanza una ejecución mínima de su comprobación; mismas reglas de riesgo y 409 `project.active_run`) | — |
| B17 | V-30 | Sin «Esperado según la política» en la detección | `expected_policy` en `FindingOccurrence` | RF-62 |
| B18 | V-31 | `RunSummary` no trae cuántos hallazgos quedaron abiertos al terminar, ni cambios por fila, ni `created_resources` | `open_findings_at_end`, `comparison` y `created_resources` en `RunSummary` | RF-72 |
| B19 | V-32 | `FindingSummary` no trae evidencia, esperado y observado ni recomendación; el reporte solo lista la clasificación. Tampoco hay total de ejecuciones del proyecto | Agregar `recommendation` y `last_occurrence` a `FindingSummary`, o asignar `getFinding` a V-32 (E3); `runs_total` en `Project` | RF-75 |
| B20 · **resuelto (0.8.0 y 0.10.0)** | V-25 | Los módulos propiedades (API3), consumo de recursos (API4) e inyección SQL (CWE-89) **no están implementados** en el motor (CHANGELOG 0.1.0, «Fuera de esta versión»); una ejecución con ellos planea 0 celdas (`scanner/modules/__init__.py:4`) y no produce nada | Decidir cómo lo informa `Project.modules`: `available: false` con un motivo (por ejemplo `not_implemented`) hasta que existan | RF-44, RF-45 |
| B21 | V-29, V-32 | Los títulos de los hallazgos se repiten y el analista no sabe distinguirlos: el título es el de la regla («La API acepta un JWT con la firma alterada») y la operación afectada no forma parte de él. En una ejecución contra el laboratorio salen 19 hallazgos abiertos y varios con el mismo título, uno por operación, identidad o variante (el frontend ya los muestra con su operación en la fila, pero el reporte y el detalle se leen como duplicados). No es dato simulado: cada fila es un hallazgo distinto de la API | Elegir una de dos: (a) que `FindingSummary.title` incluya la operación (por ejemplo «… · GET /profile»), o (b) agregar a `FindingSummary` un campo `group_key` o `title_key` estable para que el frontend agrupe por título y muestre «N operaciones afectadas». Mientras tanto el frontend puede agrupar por `title` + módulo sin cambiar el contrato | RF-75 |

## 5. Grupo C · Trabajo interno del backend con requerimiento

### C1 · Escribir en la bitácora (`audit_log`) · resuelto

Se registran 12 de las 13 acciones del catálogo `AuditAction` en el mismo momento en que ocurren (`core/audit.py`, `services/audit.py`; commits f73b668 y 0ef6e58), con el host solo como HMAC versionado. Queda **`account_deleted`**, reservada hasta que exista la baja de cuenta (A3).

### C2 · Completar las métricas diarias · resuelto, salvo `deleted_accounts`

`DailyMetricName` tiene seis métricas. Se escriben todas en la misma transacción que el hecho que cuentan, menos `deleted_accounts`, que llega con la baja de cuenta (A3):

- `new_users` y `projects_created`, como antes.
- `runs_started`: al crear o repetir una ejecución (`services/runs.py`). Una que Redis revierte (503) no cuenta.
- `runs_cancelled` (nueva): al cancelar una ejecución en cola (API) o cuando el motor la termina cancelada (por el usuario o por perder la verificación).
- `runs_failed` (nueva): cuando el motor la termina con error o la reconciliación la da por perdida (`heartbeat_expired`, `lost_in_queue`).

Una ejecución completada solo cuenta en `runs_started`. `finding_metrics` se sigue escribiendo desde el motor. Migración `7c4e1a2b9d30` (catálogo de `daily_metrics`).

### C3 · Leer `X-Hindama-Client-IP` (RF-82) · resuelto

El backend la lee y la guarda en `source_ip` si es una IPv4 o IPv6 válida; si falta o no lo es, el registro queda sin IP. En las acciones del motor es `null`. Convenciones v0.8 (línea 39) y guía v0.10 (§4.1) lo dicen igual. El BFF ya la envía (`server/bff/proxy.ts`).

### C4 · Índices y retención · resuelto

Migración `30d24d99dab2` (catálogo de acciones de `audit_log`, con `CHECK`). `purge_audit_log()` sigue corriendo cada día (RF-90).

## 6. Grupo E · Lo que el frontend puede hacer ya

Para que quien trabaje en el frontend no espere al backend:

- **E1 · `discoverResources` (V-23).** **Listo en el PR #14 del frontend, pendiente de merge.** El backend lo implementa (commit 3b19492, `api/resources.py:106`). Lo que llevaba: Falta: esquemas Zod en `lib/api/schemas/resources.ts`, entrada en `specs.ts` (envía `{}` si no hay cuerpo), ruta `src/app/api/projects/[projectId]/resources/discovery/route.ts`, habilitar el botón de `resources-view.tsx` (espera de hasta 25 s) y manejar 409 `project.not_verified`, 409 `project.active_run` y 422 `resource.no_list_operations`. Los recursos creados quedan sin confirmar.
- **E2 · Abrir el hallazgo desde una celda `fail` de la matriz (V-28).** `listFindings` acepta `operation_id` e `identity_id` (guía §5.9) y `Result` trae ambos ids (`operation.id`, `identity.id`): con eso se llega al hallazgo sin cambiar el contrato.
- **E3 · Evidencia, esperado, observado y recomendación en el reporte (V-32).** Se pueden pedir con `getFinding` por cada hallazgo (hasta 100 por reporte, y cuentan para el límite de 100 peticiones por minuto: conviene pedirlos de a pocos o solo al abrir un hallazgo).
- **E4 · Cambiar contraseña (A7) y MFA (A5).** El BFF ya habla con Cognito; no dependen de FastAPI. A5 sí depende de la configuración del pool en AWS.
- **E5 · Conectar la bitácora (V-34) a `listAuditLog`.** Backend y contrato listos (A2). En el frontend: esquema Zod y entrada `listAuditLog` en `specs.ts` (consulta con `occurred_from`, `occurred_to`, `action` repetible, `user_id`, `host`, `page`, `page_size`), ruta `src/app/api/admin/audit-log/route.ts` y reemplazar `use-simulated-load.ts` y `AUDIT_RECORDS` por la consulta. Adaptaciones que pide la API: (1) acciones: sumar `project_verification_lost` y `finding_dismissal_reverted`, y renombrar `riskAccepted` a `finding_dismissed` y `targetBlocked` a `destination_blocked`; (2) filtro por usuario solo por UUID completo, sin correo; (3) fechas: enviar el inicio del día elegido y el del día siguiente con la zona del navegador, por ejemplo `2026-11-20T00:00:00-06:00` (guía §5.10); (4) quitar `hostFingerprint` y la huella en el registro, y filtrar por `host` con el nombre o la URL (el servidor calcula el HMAC); (5) quitar la bandera «eliminado» y el correo del usuario; (6) `source_ip` puede ser `null` (acciones del motor); (7) `details` es un objeto, no una lista de etiquetas: mostrar las claves que se conozcan e ignorar las demás; (8) paginar con la API (20 por defecto, hasta 100) en lugar de en el navegador. El 403 `role.forbidden` para un analista ya lo cubre `QueryState`.
- **E9 · Contrato 0.10.0, los siete módulos y su evidencia.** Contrato, hash y tipos como en E7. Después: (1) esquema Zod de `CreatedResourceCount` con `failed_items` (`operation_id`, `location`, `last_error`) y, en V-26 y V-31, la lista de recursos por borrar a mano con su ruta junto al aviso que ya existe; (2) en la evidencia (V-30, V-32), mostrar `request.body` como texto cuando no sea `null`; (3) textos de las claves nuevas de `context`: `undeclared` («Campos no declarados»), `accepted_fields` («Campos protegidos aceptados»), `created_resource`, `requests`, `request_body_bytes`, `operation`, `parameter` y `payload` (guía §5.9); (4) los tres módulos de riesgo medio o alto ya se pueden lanzar: V-25 pide la confirmación (RN-05), que ya existe.
- **E8 · Contrato 0.9.0 y estadísticas (V-33).** Contrato, hash y tipos como en E7 (si E7 no se hizo, sus tres puntos también aplican). Después, siguiendo la sección 8: esquema Zod de `AdminStats` y la entrada `getAdminStats` en `specs.ts` (consulta con `date_from`, `date_to` y `group`), la ruta `src/app/api/admin/stats/route.ts`, y cambiar en `stats-view.tsx` `useSimulatedLoad` y `STATS` por la consulta con `Loadable`. Adaptaciones: (1) el selector de periodo envía `date_from` (y `group=week` para 90 días); (2) la serie de hallazgos es semanal (`findings.weekly`), y la diaria es `activity`; (3) «—» cuando `average_days_to_resolve` es `null`; (4) severidades con color y texto (RNF-15). El 403 para un analista ya lo cubre `QueryState`.
- **E7 · Actualizar el contrato del frontend a 0.8.0.** Igual que E6: copiar `03-api/openapi.yaml` (LF), actualizar `EXPECTED_SHA256` y regenerar los tipos. Además: (1) agregar `not_implemented` al esquema Zod de `ModuleAvailability.missing` y su texto en V-16 y V-25 («Disponible en una versión próxima»), distinto de los requisitos que resuelve el analista; (2) cambiar el aviso de eliminar identidad en `es.json` (D1); (3) revisar que los `z.enum` de respuesta toleren valores nuevos (D2).
- **E6 · Actualizar el contrato del frontend a 0.7.0.** Copiar `03-api/openapi.yaml` a `contract/openapi.yaml` (respetando LF: el clon de `hindama-docs` puede traer CRLF), actualizar `EXPECTED_SHA256` en `scripts/check-contract.mjs` y regenerar `src/lib/api/schema.d.ts` con `npm run contract:types`. Sin eso, `contract:check` y `npm test` fallan.
- **E10 · Defectos del frontend que no dependen del backend.** Salen de la prueba en el navegador ([`pruebas-navegador-2026-11-23.md`](pruebas-navegador-2026-11-23.md), con `dev` en 31f23d6; los PR 17, 18 y 19 (contrato 0.10.0, estadísticas y licencia) no tocan estas vistas). Son del frontend y se pueden corregir ya: (1) **F-02 (media)**: la pantalla `/profile/two-factor` muestra una clave TOTP fija y acepta cualquier código; ocultar el botón o marcarlo «Próximamente» hasta que existan A5 y A6. (2) **F-03 (media)**: el 403 y el 404 con sesión abierta muestran «Iniciar sesión» y «Crear cuenta». (3) **F-04 (media)**: «Recursos» aparece bloqueado en la barra lateral de un proyecto sin verificar, pero la vista funciona. (4) **F-17 (media)**: resuelto con 0.10.0 (los siete módulos ya existen), pero conviene revisar que V-25 no ofrezca un módulo con `available: false`. (5) Bajas: F-05 (`/sign-in` y `/sign-up` con sesión abierta no redirigen), F-07 (error de importación termina en «..»), F-08 (el mismo aviso sale dos veces), F-09 («Revisa los avisos» sin avisos), F-10 (título de pestaña en el 404), F-12 (la barra lateral se pierde en páginas largas), F-13 (el 404 de un hallazgo habla del «proyecto»), F-18 (códigos crudos `baseline_failed` y `method_not_safe` en matriz y reporte), F-19 («Las 0 propuestas sin confirmar…»), F-20 (una ejecución de 11 s sale como «1 minuto» en resultados y «0:11» en el resumen) y F-21 (la tarjeta de «Acceso a objetos» dice «Lo cumples» con identidades sin recursos). (6) Informativas, sin urgencia: F-14 (idioma de una URL sin prefijo), F-15 (barra lateral de 2FA) y F-11/F-23 (lentitud de `next dev`). F-01 y F-06 (móvil) se descartaron por decisión de Luis; F-22 (resueltos frente a la ejecución anterior) depende de B12.
- **E11 · Lo que se puede hacer ya con lo que existe y lo que no se ha probado.** (1) **Títulos repetidos (B21)**: mientras el backend decide, agrupar en V-29 y V-32 por `title` y módulo y mostrar «N operaciones afectadas», sin cambiar el contrato. (2) **Cambiar contraseña (C-17)**: Cognito `ChangePassword` desde el BFF (ver E4); solo espera una decisión de producto. (3) **Valores desconocidos de un enum (D2)**: tratarlos como genéricos en vez de fallar. (4) **Vistas simuladas que siguen bloqueadas**: `account/service.ts` (2FA y acceso de administradores, A5 y A6) y la baja de cuenta (C-14, A3), que solo tiene un diálogo simulado. (5) **Sin probar con datos reales**: las vistas de administración (V-33 y V-34) con una cuenta de administrador (la prueba se hizo con un analista y solo vio el 403), los filtros de hallazgos con los tres criterios combinados, el historial con dos ejecuciones, revertir un descarte y cancelar una ejecución (el laboratorio termina en segundos; con `requests_per_second` en 1 la ejecución dura unos 45 s y se puede cancelar a mitad). (6) **Fuera del código**: despliegue del frontend en EC2 con su pool de Cognito, y decidir si se mantiene `'unsafe-inline'` en la CSP.

## 7. Orden sugerido

1. **Frontend:** E5 (bitácora), el PR #14 (V-23) y E6 a E9 (contrato 0.10.0 y V-33) ya están hechos; falta revisar y mezclar los PR de la fase 9.
2. ~~**C2**~~: hecho en la v1.2, salvo `deleted_accounts` (A3).
3. ~~**Contrato 0.9.0**: A1~~, hecho en la v1.3. **Contrato 0.10.0**: A3 y A4, con los campos de B que se decidan.
4. **Backend:** A3 (que también emite `account_deleted`) y A4, en ese orden.
5. **A5, A6, A7** cuando se decidan el pool de administradores y la configuración de MFA (AWS).
6. **B1 a B20** por vista, según lo que la demostración necesite; ninguno bloquea las vistas conectadas.

## 8. Cómo se entrega cada cambio (ADR-016)

1. PR a `hindama-docs` que cambia `openapi.yaml` (con `info.version` nuevo) y, si aplica, esta guía y `guia-frontend.md`. Revisado por las dos personas.
2. PR del backend que lo implementa. La prueba de contrato (`tests/contract/test_openapi_contract.py`) y Schemathesis fallan si no coincide; al implementar una operación nueva hay que borrar su bloque de `schemathesis.toml`.
3. PR del frontend, con estos pasos:
   - Copiar el contrato a `contract/openapi.yaml` (respetando LF) y actualizar `EXPECTED_SHA256` en `scripts/check-contract.mjs`.
   - Regenerar los tipos con `npm run contract:types`.
   - Agregar el esquema Zod, la entrada en `src/server/bff/specs.ts` y el `route.ts` bajo `src/app/api`, **antes** de conectar la vista (regla del proyecto: primero el BFF con la seguridad de la documentación, después el backend).
   - Conectar la vista con `useHttpClient()`, quitar el `TODO(api)` y la función simulada, y actualizar su fila en el inventario.
   - Correr typecheck, lint, pruebas unitarias, `build` y e2e antes de abrir el PR.
4. Cada entrega se anota en el historial de la guía del frontend (sección 9).

## 9. Contradicciones de documentación que conviene resolver con esto

- **D1 · `deleteIdentity` · resuelto (contrato 0.8.0, manda el backend; falta el texto del frontend, E7).** `openapi.yaml:845` dice «Los hallazgos que la usan se conservan». El backend cierra los hallazgos abiertos de la identidad con motivo `identity_deleted` (`repositories/identities.py:205`), igual que dicen `guia-frontend.md` §5.5 y §5.9 y RF-69. Hay que decidir cuál manda y corregir el otro. Es un cambio de texto del contrato (PATCH, `0.6.1`). El frontend dice hoy «Sus hallazgos se conservan» (`es.json`, claves `item2` y `deleteNote`).
- **D2 · `convenciones.md` §1 y §2 · resuelto (convenciones v0.9).** §1 dice que las respuestas son cerradas (`additionalProperties: false`) y §2 que el cliente debe ignorar los campos que no conoce. Conviene aclarar que lo primero es para pruebas del backend y lo segundo para el cliente.
- **D3 · `X-Hindama-Client-IP`.** Resuelto: `convenciones.md` v0.8 y `guia-frontend.md` v0.10 lo describen igual (el backend ya la lee, C3).

### 9.1 Documentos y entorno que quedaron atrás con el 0.7.0

Son cosas que el 0.7.0 y el backend 0.1.0 dejaron desactualizadas. **Todas se corrigieron en la v1.2** (ver la tabla del principio); se dejan como registro:

- **`03-api/entorno-local.md` §4 (generador del `.env` del backend).** El script reemplaza `cambia-esto-por-32-bytes-en-base64` con `.replace(...)` de una sola ocurrencia. `.env.example` ahora trae **dos** (`HINDAMA_CREDENTIAL_KEYS` y `HINDAMA_AUDIT_HMAC_KEYS`): la de la bitácora quedaría con el valor de ejemplo y, según `.env.example`, sin esa llave la API y el motor no arrancan. Hay que reemplazar cada una por una llave distinta de 32 bytes en base64, y agregar `HINDAMA_AUDIT_HMAC_KEY_VERSION=1`. Quien ya tiene un `.env` debe agregar las dos variables nuevas antes de reconstruir.
- **`03-api/entorno-local.md`, encabezado y §8.1.** Sigue en «backend 080eaca (contrato 0.6.0) y frontend d031d0e», con casi todo en «Falta»; ya no es así (ver el [inventario](inventario-endpoints-vistas-observaciones.md)).
- **`README.md` de `hindama-docs`.** La fila de `guia-frontend.md` dice «v0.8 (2026-11-22)» (hoy v0.10) y la de `convenciones.md`, «v0.7» (hoy v0.8).
- **Inventario (`06-frontend`) §1, §2 y §7, fila de V-34.** Dice que `/admin/*` no tiene contrato y que V-34 está «bloqueada». Con el 0.7.0 la bitácora tiene contrato e implementación: falta la vista (E5). V-33 (estadísticas) sigue sin contrato.
- **Frontend, `scripts/check-contract.mjs`.** Su hash es el del 0.6.0 (E6).
- **Docker local.** El backend cambió: hay que reconstruir con `docker compose up -d --build --wait`, y la migración `30d24d99dab2` se aplica sola. Primero hay que agregar al `.env` las llaves de la bitácora (ver el primer punto).

## 10. Lo que no cambia

Estas vistas y operaciones ya funcionan de punta a punta y no necesitan al backend: registro, verificación del correo, inicio de sesión, recuperación (Cognito por el BFF), `getMe`, términos, proyectos, verificación, contratos, operaciones, identidades, recursos (menos el descubrimiento, E1), política, ejecuciones, progreso, matriz, hallazgos, historial y reporte. La lista completa con sus `operationId` está en la sección 1 del [inventario](inventario-endpoints-vistas-observaciones.md).
