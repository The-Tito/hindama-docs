---
documento: Pendientes del backend para conectar todo el frontend
proyecto: Hindama
version: 1.0
fecha: 2026-11-23
estado: vigente; verificado contra backend dd58ba9 (develop), contrato 0.6.0 y frontend 7b5edc4 (dev)
---

# Pendientes del backend para conectar todo el frontend

Qué le falta al backend (y al contrato) para que **todas** las vistas del frontend dejen de usar datos fijos o simulados, y qué hace el frontend cuando llegue cada cosa. Está escrito para quien implemente el backend: cada pendiente trae la vista que lo necesita, el requerimiento, la evidencia en el código y una propuesta de cambio al contrato.

Las propuestas de contrato son **propuestas**: se acuerdan en un pull request a `hindama-docs` (ADR-016) antes de implementarse.

## 1. Estado de partida

- El backend implementa las **38 operaciones** del contrato 0.6.0: las `operationId` de `src/hindama/api/*.py` coinciden con las de `03-api/openapi.yaml`, y la API local responde 38 en `/openapi.json`.
- El frontend ya conecta por el BFF todas las vistas que tienen contrato, salvo una (§6, E1). Ver [inventario](inventario-endpoints-vistas-observaciones.md), secciones 1 y 10 a 15.
- Lo que sigue **simulado o fijo** en el frontend es lo que el contrato 0.6.0 no cubre. Eso es este documento.
- El separador de roles ya existe: el rol sale del grupo `administradores` de Cognito (`config.py:81`, `core/auth.py:121`), `GET /me` lo devuelve y las rutas de proyectos usan el guardia `Analyst` (403 `role.forbidden` para un administrador, RF-80). El guardia `Admin` (`api/dependencies.py:72`) existe, pero **ninguna ruta lo usa**.

## 2. Resumen

| Grupo | Qué es | Pendientes |
| --- | --- | --- |
| A | Funciones sin contrato (rutas u operaciones nuevas) | A1 a A8 |
| B | Campos, filtros y operaciones que se agregan a lo ya existente | B1 a B19 |
| C | Trabajo interno del backend que ya tiene requerimiento | C1 a C4 |
| D | Contradicciones entre contrato, guía y código | D1 a D3 |
| E | Lo que el frontend puede hacer ya, sin esperar al backend | E1 a E4 |

Prioridad sugerida (a la entrega de finales de noviembre): primero C1 y C2 (sin ellos A1 y A2 no tienen datos), luego A2, A1, A3, A4 y A5; B según el tiempo. Orden en la sección 7.

## 3. Grupo A · Funciones sin contrato

### A1 · Panel de estadísticas del administrador (V-33, F-13)

- **Requerimientos:** RF-78, RF-79, RF-89. Prioridad baja.
- **Frontend hoy:** `src/features/admin/stats-view.tsx` con datos de ejemplo (`admin/data.ts`, `STATS`) y carga simulada (`use-simulated-load.ts`).
- **Backend hoy:** no existe ruta ni contrato. Las tablas sí existen (`models/audit.py`: `daily_metrics`, `finding_metrics`), pero no todo se escribe (C2).
- **Propuesta:** `GET /admin/stats` con `period` (`7`, `30`, `90` o rango `from` y `to`). Solo para el administrador (guardia `Admin`; 403 para un analista). Devuelve datos agregados y anónimos, sin URLs, contratos, credenciales ni identificadores de analistas (RF-79). Lo que la vista pinta hoy:
  - Seis indicadores: usuarios (con los nuevos del periodo), proyectos, ejecuciones (con canceladas y fallidas), días promedio entre detección y resolución, cuentas eliminadas y regresiones.
  - Una serie de hallazgos detectados (por día en el periodo de 7 días y por semana en los demás; la vista usa `unit: "day" | "week"`).
  - Hallazgos por módulo y por categoría OWASP.
- **Fuentes de datos:** `daily_metrics` (`new_users`, `deleted_accounts`, `projects_created`, `runs_started`) y `finding_metrics` (`week`, `module`, `owasp_category`, `days_to_resolve`, `regressions`).
- **Lo que decide el backend:** de dónde salen las ejecuciones canceladas y fallidas (hoy no hay métrica diaria para ellas) y los usuarios totales.
- **Frontend cuando llegue:** esquema Zod y entrada en `specs.ts`, ruta `src/app/api/admin/stats/route.ts`, y reemplazar `useSimulatedLoad` por la consulta con `Loadable` (los tres estados ya existen).

### A2 · Bitácora de auditoría (V-34, F-14)

- **Requerimientos:** RF-81 a RF-84, RF-90. Prioridad media.
- **Frontend hoy:** `audit-log-view.tsx` con 34 registros de ejemplo (`AUDIT_RECORDS`) y filtros de fecha, acción, usuario y host. La huella del host se calcula en el navegador con FNV-1a (`hostFingerprint`); el diseño pide HMAC del servidor.
- **Backend hoy:** la tabla `audit_log` existe e inmutable (trigger, `purge_audit_log()` diario en `scanner/reconciliation.py:155`), pero **nada escribe en ella** (C1) y no hay ruta de lectura.
- **Propuesta:** `GET /admin/audit-log` con `from`, `to`, `action`, `user_id`, `host` (el servidor calcula su HMAC y compara; nunca devuelve el host), `page` y `page_size`. Solo administrador. Cada registro: `id`, `occurred_at`, `user_id` (opaco), `action`, `project_id` (opaco o `null`), `source_ip`, `details` y la huella del host solo en «destino bloqueado».
- **Acciones (RF-81):** cuenta creada y eliminada, proyecto creado, verificado y eliminado, identidad creada y eliminada, ejecución lanzada y cancelada, riesgo aceptado y destino bloqueado (son los 11 valores que usa la vista). Hay que acordar los nombres en inglés (ADR-017) y las claves de `details` de cada acción (módulos, límites, riesgo confirmado, motivo…), sin credenciales ni justificaciones (RF-83).
- **Decisión abierta:** la vista marca al usuario «eliminado». `audit_log` no tiene llave foránea a `users` y el administrador solo lee `audit_log` y `metric_*` (`modelo.md` 7.1), así que no puede saber si el usuario sigue existiendo. Opciones: guardar el dato en el registro de baja, o dejar de mostrarlo.
- **Frontend cuando llegue:** igual que A1, más cambiar la huella local por el filtro `host` del servidor y borrar `AUDIT_RECORDS`, `USERS` y `hostFingerprint`.

### A3 · Baja de cuenta (C-14, RF-88)

- **Frontend hoy:** no hay pantalla ni diálogo.
- **Backend hoy:** el contrato no tiene `DELETE /me`.
- **Propuesta:** `DELETE /me` con confirmación escrita del correo (como `deleteProject` con `confirmation`). Debe: rechazar con 409 si hay ejecuciones activas, borrar la cuenta en Cognito, el registro de usuario y todos sus proyectos con su contenido (ADR-015), conservar métricas anónimas y bitácora, sumar `deleted_accounts` (C2) y registrar `account_deleted` (C1). Requiere permiso de la API para borrar usuarios del pool (AWS: lo configura el equipo de backend; no lo hice).
- **Frontend cuando llegue:** diálogo en el perfil (C-07, eliminación con confirmación escrita), ruta BFF, borrar la cookie de sesión y llevar a V-01 con el aviso «cuenta eliminada».

### A4 · Exportar hallazgos a Excel (RF-77)

- **Frontend hoy:** se quitó el botón «Exportar a Excel» de V-27, V-29 y V-32 (comentarios `TODO(api)` en `findings-view.tsx:343` y `report-view.tsx:353`).
- **Backend hoy:** no existe.
- **Propuesta:** `GET /projects/{project_id}/findings/export` con los mismos filtros de `listFindings`, que responde `.xlsx` (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`). Evidencia enmascarada (RN-11). Hay que definir qué columnas lleva y un tope de filas.
- **Frontend cuando llegue:** el BFF debe relevar un cuerpo binario (hoy `apiRoute` maneja JSON), y un botón con descarga y espera.

### A5 · Segundo factor TOTP (V-05, V-10, V-11, F-15)

- **Requerimientos:** RF-85, RF-86, RF-87. Prioridad baja, «fase final».
- **Frontend hoy:** simulado en `account/service.ts` (`confirmTwoFactor`, `disableTwoFactor`, `verifyLoginTwoFactor`; clave `TOTP_SECRET_STUB` y QR de relleno).
- **Backend hoy:** el MFA está **desactivado** en el pool de Cognito (guía §2.2). No hay nada en FastAPI.
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
| B12 | V-26, V-27, V-32 | `Run` no trae resultados por módulo (hallazgos, omitidos, credenciales vencidas), ni la comparación con la ejecución anterior (nuevos, persistentes, resueltos, regresiones), y `created_resources` solo trae contadores | `Run.modules_result[]`, `Run.comparison` y `created_resources.items[]` (operación, ubicación y último error de cada recurso sin borrar) | RF-52, RF-72 |
| B13 | V-28 | `Result` no trae `finding_id`, ni el rol de la identidad ni la plantilla de política de la operación | `finding_id`, `identity.role` y `operation.policy` (ver también E2: la celda ya puede abrir el hallazgo) | RF-64 |
| B14 | V-28, V-32 | `expected` y `observed` son texto libre: no hay lista cerrada. Además `observed` no siempre es un código simple: `scanner/modules/object_access.py:118` genera `"200 own_data_only"` y `configuration.py:151` une códigos con coma | Publicar un enum o una lista de códigos en el contrato, y separar el código de los datos (`observed` y `observed_status`) | RF-64 |
| B15 | V-29 | Sin filtro por motivo de descarte: `listFindings` no tiene `dismissal_reason` y `FindingSummary` no trae `dismissal` | Filtro `dismissal_reason`; `dismissal.reason` en `FindingSummary` | RF-70 |
| B16 | V-30 | Sin «Volver a probar» un solo hallazgo | `POST /projects/{project_id}/findings/{finding_id}/retest` (lanza una ejecución mínima de su comprobación; mismas reglas de riesgo y 409 `project.active_run`) | — |
| B17 | V-30 | Sin «Esperado según la política» en la detección | `expected_policy` en `FindingOccurrence` | RF-62 |
| B18 | V-31 | `RunSummary` no trae cuántos hallazgos quedaron abiertos al terminar, ni cambios por fila, ni `created_resources` | `open_findings_at_end`, `comparison` y `created_resources` en `RunSummary` | RF-72 |
| B19 | V-32 | `FindingSummary` no trae evidencia, esperado y observado ni recomendación; el reporte solo lista la clasificación. Tampoco hay total de ejecuciones del proyecto | Agregar `recommendation` y `last_occurrence` a `FindingSummary`, o asignar `getFinding` a V-32 (E3); `runs_total` en `Project` | RF-75 |

## 5. Grupo C · Trabajo interno del backend con requerimiento

### C1 · Escribir en la bitácora (`audit_log`)

`AuditLogEntry` solo está definido en `models/audit.py`: **ningún servicio inserta registros** (búsqueda en `src/hindama`: sin otros usos). Sin esto, A2 mostraría una bitácora vacía. Hay que registrar las acciones de RF-81 en el mismo momento en que ocurren, con la IP de origen (C3) y el host solo como HMAC. Tampoco hay una llave de HMAC en `config.py` ni en `.env.example`: hay que definirla, versionarla (`hmac_version` ya está en la tabla) y guardarla fuera del código.

### C2 · Completar las métricas diarias

`DailyMetricName` define cuatro métricas (`new_users`, `deleted_accounts`, `projects_created`, `runs_started`), pero `increment_daily` solo se llama para `new_users` (`services/accounts.py:25`) y `projects_created` (`services/projects.py:256`). Faltan `runs_started` (al crear o repetir una ejecución) y `deleted_accounts` (A3). `finding_metrics` sí se escribe desde el motor (`scanner/recorder.py:156`, `resolution.py`). Para A1 hay que decidir cómo contar ejecuciones canceladas y fallidas (hoy no hay métrica).

### C3 · Leer `X-Hindama-Client-IP` (RF-82)

El BFF ya la envía (`server/bff/proxy.ts`), pero el backend **no la lee** (búsqueda sin resultados) y la guía §1 la marca pendiente. `convenciones.md:39` dice que FastAPI la acepta solo si la petición viene de la IP privada del frontend: hay que implementarlo así. Sin eso, `source_ip` de la bitácora (C1) sería la IP del servidor de Next.js.

### C4 · Índices y retención

`purge_audit_log()` ya corre cada día. Al crear A1 y A2, revisar los índices de `audit_log` para los filtros nuevos (hay índices por fecha, usuario, acción y `host_hmac`) y que el administrador pueda leerla bajo RLS sin acceso a tablas de proyecto (`modelo.md` 7.1).

## 6. Grupo E · Lo que el frontend puede hacer ya

Para que quien trabaje en el frontend no espere al backend:

- **E1 · `discoverResources` (V-23).** El backend lo implementa (commit 3b19492, `api/resources.py:106`). Falta: esquemas Zod en `lib/api/schemas/resources.ts`, entrada en `specs.ts` (envía `{}` si no hay cuerpo), ruta `src/app/api/projects/[projectId]/resources/discovery/route.ts`, habilitar el botón de `resources-view.tsx` (espera de hasta 25 s) y manejar 409 `project.not_verified`, 409 `project.active_run` y 422 `resource.no_list_operations`. Los recursos creados quedan sin confirmar.
- **E2 · Abrir el hallazgo desde una celda `fail` de la matriz (V-28).** `listFindings` acepta `operation_id` e `identity_id` (guía §5.9) y `Result` trae ambos ids (`operation.id`, `identity.id`): con eso se llega al hallazgo sin cambiar el contrato.
- **E3 · Evidencia, esperado, observado y recomendación en el reporte (V-32).** Se pueden pedir con `getFinding` por cada hallazgo (hasta 100 por reporte, y cuentan para el límite de 100 peticiones por minuto: conviene pedirlos de a pocos o solo al abrir un hallazgo).
- **E4 · Cambiar contraseña (A7) y MFA (A5).** El BFF ya habla con Cognito; no dependen de FastAPI. A5 sí depende de la configuración del pool en AWS.

## 7. Orden sugerido

1. **C3, C1, C2** (sin contrato nuevo): la bitácora y las métricas empiezan a llenarse desde ya.
2. **Contrato 0.7.0** en `hindama-docs`: A1, A2, A3 y A4, con los campos de B que se decidan, en un solo PR.
3. **Backend:** A2, A1, A3, A4 en ese orden.
4. **A5, A6, A7** cuando se decidan el pool de administradores y la configuración de MFA (AWS).
5. **B1 a B19** por vista, según lo que la demostración necesite; ninguno bloquea las vistas conectadas.

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

- **D1 · `deleteIdentity`.** `openapi.yaml:841` dice «Los hallazgos que la usan se conservan». El backend cierra los hallazgos abiertos de la identidad con motivo `identity_deleted` (`repositories/identities.py:205`), igual que dicen `guia-frontend.md` §5.5 y §5.9 y RF-69. Hay que decidir cuál manda y corregir el otro. Es un cambio de texto del contrato (PATCH, `0.6.1`). El frontend dice hoy «Sus hallazgos se conservan» (`es.json`, claves `item2` y `deleteNote`).
- **D2 · `convenciones.md` §1 y §2.** §1 dice que las respuestas son cerradas (`additionalProperties: false`) y §2 que el cliente debe ignorar los campos que no conoce. Conviene aclarar que lo primero es para pruebas del backend y lo segundo para el cliente.
- **D3 · `X-Hindama-Client-IP`.** `convenciones.md:39` lo describe como funcionando y `guia-frontend.md` §1 como pendiente (C3). Corregir al implementar C3.

El resto de documentos desactualizados (entorno local §8.1, inventario, README) se listó en el análisis de este día y se corrige aparte.

## 10. Lo que no cambia

Estas vistas y operaciones ya funcionan de punta a punta y no necesitan al backend: registro, verificación del correo, inicio de sesión, recuperación (Cognito por el BFF), `getMe`, términos, proyectos, verificación, contratos, operaciones, identidades, recursos (menos el descubrimiento, E1), política, ejecuciones, progreso, matriz, hallazgos, historial y reporte. La lista completa con sus `operationId` está en la sección 1 del [inventario](inventario-endpoints-vistas-observaciones.md).
