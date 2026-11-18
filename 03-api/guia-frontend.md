---
documento: Guía de integración para el frontend
proyecto: Hindama
version: 0.5
fecha: 2026-11-18
estado: vigente; crece con cada entrega del backend
---

# Guía de integración para el frontend

Lo que necesitas saber para conectar `hindama-frontend` (Next.js como BFF) con lo que ya existe: Amazon Cognito y la API de la plataforma. No sustituye al contrato ni a las convenciones; los resume y señala lo que no se ve a simple vista.

- **Contrato:** [`openapi.yaml`](openapi.yaml). Es la fuente de verdad de rutas, campos y códigos.
- **Convenciones:** [`convenciones.md`](convenciones.md): errores, paginación, formatos y cabeceras.
- **Sesión:** [ADR-005](../01-arquitectura/decisiones/ADR-005-sesion-bff-con-cookie-cifrada.md) y la sección 4.1 de la [arquitectura](../01-arquitectura/arquitectura.md).

La sección 9 registra cada cambio de esta guía. Cuando el backend entregue algo nuevo, se agrega aquí en el mismo pull request.

## 1. Qué existe hoy

| Pieza | Estado |
| --- | --- |
| User Pool de Cognito de **desarrollo** (`hindama-dev`) | Creado y probado de punta a punta |
| User Pool de producción (`hindama-prod`) | Se crea en la semana 3, con el despliegue |
| API: `GET /health`, `GET /me`, `POST /me/terms` | Implementados (CU-02, RF-16) |
| API: `GET/POST /projects`, `GET/PATCH/DELETE /projects/{project_id}` | Implementados (CU-05, CU-06) |
| API: `GET/POST /projects/{project_id}/verification` | Implementados (CU-07) |
| API: contratos (`/contracts`) y operaciones (`/operations`) | Implementados (CU-08) |
| API: identidades (`/identities`), recursos (`/resources`), política (`PATCH …/operations/{operation_id}`, `POST …/policy`) | Implementados (CU-09, CU-10, CU-11). Todo el contrato 0.3.0 está implementado |
| API: lanzar, listar y consultar ejecuciones (`POST/GET …/runs`, `GET …/runs/{run_id}`) | Implementados (CU-12). El motor tiene cuatro módulos: acceso a objetos, acceso a funciones, autenticación y configuración. Una ejecución genera celdas y hallazgos reales |
| API: cancelar (`POST …/runs/{run_id}/cancel`) y progreso por SSE (`GET …/runs/{run_id}/events`) | Implementados (CU-13, CU-14) |
| API: matriz de resultados (`GET …/runs/{run_id}/results`) | Implementada (RF-64) |
| API: descubrimiento de recursos (contrato 0.4.0) | En el contrato y en el simulador; el backend lo implementa con RF-36 |
| API: hallazgos (`/findings`, contrato 0.5.0) | En el contrato y en el simulador; el backend los implementa en la tarea 4.1 |
| Límite de 100 peticiones por minuto (429) y lectura de `X-Hindama-Client-IP` | Pendientes en el backend. Envía la cabecera desde ya |

## 2. Amazon Cognito

### 2.1 Datos del User Pool de desarrollo

| Variable sugerida en `.env.local` | Valor | ¿Secreto? |
| --- | --- | --- |
| `COGNITO_REGION` | `us-east-1` | No |
| `COGNITO_USER_POOL_ID` | `us-east-1_8qQxmtXn1` | No |
| `COGNITO_CLIENT_ID` | `f8oiqpgmhhlv9ineppp8a2mbl` | No |
| `COGNITO_CLIENT_SECRET` | En SSM: `/hindama/dev/frontend/cognito-client-secret` | **Sí** |

El secreto del cliente vive solo en SSM Parameter Store. No se envía por chat ni por correo y nunca se escribe en el repositorio. Lo lees tú mismo con un usuario de IAM propio (no compartan usuarios) que el equipo de backend crea en la cuenta `469332593110`. Ese usuario no tiene acceso a la consola y solo puede ejecutar `ssm:GetParameter` sobre `arn:aws:ssm:us-east-1:469332593110:parameter/hindama/dev/frontend/*`.

1. **Instala la AWS CLI** si no la tienes. En Mac: `brew install awscli`. En Windows, con el instalador de <https://aws.amazon.com/cli/>.
2. **Configura tu perfil** con las llaves que te dio el equipo de backend:

   ```bash
   aws configure --profile hindama
   ```

   Pega el ID de clave de acceso (`AKIA…`) y la clave secreta, y responde `us-east-1` y `json`.

3. **Comprueba que funcionan:**

   ```bash
   aws sts get-caller-identity --profile hindama
   ```

   Debe mostrar tu usuario (`…:user/<tu-usuario>`). Cualquier otro comando de AWS te dará `AccessDenied`: es lo esperado, porque solo puedes leer el secreto.

4. **Guarda el secreto en tu `.env.local`**, desde la carpeta de `hindama-frontend`. Una sola línea, y córrela **una sola vez** (si la repites, el secreto queda duplicado):

   ```bash
   printf 'COGNITO_CLIENT_SECRET=%s\n' "$(aws ssm get-parameter --profile hindama --region us-east-1 --name /hindama/dev/frontend/cognito-client-secret --with-decryption --query Parameter.Value --output text)" >> .env.local
   chmod 600 .env.local
   ```

   Para comprobarlo sin mostrar el secreto: `grep -c COGNITO_CLIENT_SECRET .env.local` debe dar `1`.

5. **Agrega las variables públicas** de la tabla al mismo `.env.local`:

   ```
   COGNITO_REGION=us-east-1
   COGNITO_USER_POOL_ID=us-east-1_8qQxmtXn1
   COGNITO_CLIENT_ID=f8oiqpgmhhlv9ineppp8a2mbl
   ```

6. **Confirma que `.env.local` no se sube al repositorio:** `git check-ignore .env.local` debe imprimir `.env.local`. Si no imprime nada, agrégalo al `.gitignore` antes de cualquier commit.

Si el paso 4 falla:

| Error | Causa |
| --- | --- |
| `AccessDenied` | La política no está asociada a tu usuario, o su ARN tiene un error. Avisa al equipo de backend. |
| `ParameterNotFound` | Falta `--region us-east-1`, o el nombre del parámetro está mal escrito. |
| `InvalidClientTokenId` o `SignatureDoesNotMatch` | Las llaves del paso 2 están mal copiadas. Repite `aws configure --profile hindama`. |

Si el secreto cambia (por ejemplo, porque se recreó el cliente), borra la línea `COGNITO_CLIENT_SECRET` de tu `.env.local` y repite el paso 4.

### 2.2 Cómo está configurado

| Aspecto | Configuración | Qué implica para el frontend |
| --- | --- | --- |
| Identificador | El **correo**, sin distinguir mayúsculas | El formulario pide correo, no nombre de usuario. |
| Atributos obligatorios | `email` y `name` (1 a 100 caracteres) | `SignUp` debe enviar los dos (RF-01). |
| Contraseña | Mínimo 12, con mayúsculas, minúsculas, números y símbolos; no repite las últimas 5 | Valida en el formulario para dar buen mensaje, pero la regla la aplica Cognito (RF-03). |
| Verificación | Código de 6 dígitos al correo | Pantalla de confirmación después del registro (RF-02). |
| Recuperación | Código al correo verificado | `ForgotPassword` y `ConfirmForgotPassword` (RF-05). |
| Cliente | `hindama-web`, **confidencial**, sin interfaz alojada ni OAuth | Todas las llamadas a Cognito salen del **servidor** de Next.js con `SECRET_HASH` (ADR-005). |
| Flujos | `USER_PASSWORD_AUTH` y `REFRESH_TOKEN_AUTH` | Son los únicos que acepta el cliente. |
| Vigencia | Access e id token: 15 minutos; refresh token: 7 días | Renueva cuando falten menos de 5 minutos (ADR-005). |
| Revocación | Activa | El cierre de sesión llama a `RevokeToken` con el refresh token (RF-04). |
| Errores de existencia | Ocultos | Con credenciales incorrectas, Cognito no dice si el correo existe (RF-06). |
| Bloqueo | Automático tras intentos fallidos | Muestra el mismo mensaje genérico. |
| MFA | Desactivado | Llega con F-15; el flujo ya tiene previsto el desafío `SOFTWARE_TOKEN_MFA`. |
| Correo | El de Cognito | **Máximo 50 correos al día** en todo el pool. Si dejan de llegar códigos en pruebas, es este límite. |

### 2.3 Llamadas que hace Next.js

Todas son de la API de Cognito Identity Provider (por ejemplo, con `@aws-sdk/client-cognito-identity-provider`) y **ninguna necesita credenciales de AWS**: se autentican con el Client ID y el `SECRET_HASH`. Solo `RevokeToken` envía el secreto del cliente tal cual.

| Pantalla | Llamada | Notas |
| --- | --- | --- |
| Crear cuenta | `SignUp` | `Username` = correo; `UserAttributes` = `email` y `name`. |
| Confirmar correo | `ConfirmSignUp`; `ResendConfirmationCode` | |
| Iniciar sesión | `InitiateAuth` con `AuthFlow: USER_PASSWORD_AUTH` | Parámetros `USERNAME`, `PASSWORD`, `SECRET_HASH`. |
| Renovar | `InitiateAuth` con `AuthFlow: REFRESH_TOKEN_AUTH` | Ver la trampa de la sección 2.4. |
| Cerrar sesión | `RevokeToken` | Con `Token` = refresh token, `ClientId` y `ClientSecret`. Después borra la cookie. |
| Olvidé mi contraseña | `ForgotPassword`; `ConfirmForgotPassword` | |

**`SECRET_HASH`** = Base64(HMAC-SHA256(llave = secreto del cliente, mensaje = `username` + `client_id`)). Calcúlalo en el servidor; el secreto nunca llega al navegador.

### 2.4 Trampas conocidas

- **El `username` interno no es el correo.** Como el pool inicia sesión con correo, Cognito asigna a cada cuenta un `username` interno (un UUID). En `USER_PASSWORD_AUTH` el `SECRET_HASH` se calcula con el correo, pero en **`REFRESH_TOKEN_AUTH` se calcula con ese `username` interno**. Sácalo del claim `username` del access token (decodifícalo sin verificar; quien lo verifica es FastAPI) y guárdalo junto a los tokens en la sesión cifrada. Si usas el correo, la renovación falla con `NotAuthorizedException`.
- **No reveles si el correo existe** (RF-06). Muestra el mismo mensaje para `NotAuthorizedException` y `UserNotFoundException`. `UserNotConfirmedException` sí se puede distinguir: lleva a la pantalla de confirmación.
- **Códigos de error útiles:** `UsernameExistsException` (registro con un correo ya usado), `InvalidPasswordException` (no cumple la política), `CodeMismatchException` y `ExpiredCodeException` (código de verificación), `LimitExceededException` y `TooManyRequestsException` (demasiados intentos).
- **No registres** cuerpos de petición de las rutas de autenticación ni los tokens (ADR-005).

### 2.5 Cuentas de prueba y rol de administrador

- Mientras no exista la pantalla de registro, las cuentas de prueba se crean en la consola de AWS y se activan con `deploy/cognito/set-dev-password.sh` del backend ([procedimiento, sección 2.4](../../hindama-backend/deploy/PROCEDIMIENTO.md)). Con el registro listo, crea las tuyas desde la interfaz.
- **Administrador:** solo se asigna en la consola, agregando la cuenta al grupo `administradores` (RF-09). El frontend no tiene ninguna pantalla para esto. El cambio aparece en el siguiente token.
- **El rol se lee de `GET /me`**, no del token. Next.js lo usa solo para elegir la pantalla inicial (`/projects` o `/admin`); cada permiso lo vuelve a decidir la API (RNF-08).

## 3. La sesión en Next.js

Resumen de [ADR-005](../01-arquitectura/decisiones/ADR-005-sesion-bff-con-cookie-cifrada.md) y de las reglas del proyecto:

- **Cookie** `__Host-hindama_sesion`: `HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`. Contiene solo el access token y el refresh token (más el `username` interno de la sección 2.4), cifrados con AES-256-GCM. El id token no se guarda.
- Si el valor cifrado supera 4 KB, se divide en `__Host-hindama_sesion.0`, `.1`…
- El JavaScript del navegador **nunca** ve los tokens (RF-08).
- **Renovación:** antes de reenviar una petición, si al access token le quedan menos de 5 minutos, renueva con el refresh token.
- **CSRF:** token sincronizado dentro de la sesión, enviado en `X-CSRF-Token`, más verificación del `Origin` en toda petición que modifica datos (RNF-07).
- **Cabeceras:** HSTS, Content-Security-Policy y `X-Content-Type-Options: nosniff`.
- **El navegador solo habla con Next.js.** La API de la plataforma no es pública.

## 4. Cómo llamar a la API

### 4.1 Cabeceras

| Cabecera | Cuándo |
| --- | --- |
| `Authorization: Bearer <access_token>` | En todo, salvo `GET /health`. |
| `X-Request-Id` | Opcional. Si la envías, la API la conserva y la devuelve; útil para seguir una petición en los registros de los dos lados. |
| `X-Hindama-Client-IP` | La IP real del navegador, para la bitácora (RF-82). Envíala desde ya aunque el backend todavía no la lea. |
| `Content-Type: application/json` | En `POST` y `PATCH`. |

### 4.2 Errores

Todo error es Problem Details (`application/problem+json`) con `code`, `request_id` y `errors[]` (convenciones, sección 8). **Elige el texto según `code`** (y `errors[].code` para marcar campos); `detail` es solo un respaldo en español.

| Respuesta | Qué hacer |
| --- | --- |
| 401 `auth.required` o `auth.invalid_token` | Renueva el token y reintenta **una vez**. Si vuelve a dar 401, cierra la sesión. También pasa si la sesión se revocó en Cognito aunque el token no haya vencido. |
| 403 `terms.not_accepted` | Muestra los términos de uso responsable y llama a `POST /me/terms` (sección 5.1). |
| 403 `role.forbidden` | El administrador intentó entrar a proyectos (o el analista a `/admin`). Redirige a su pantalla. |
| 404 `resource.not_found` | Igual para un recurso inexistente y para uno de otro analista (RN-02). No intentes distinguirlos. |
| 422 `validation.failed` | Errores de campo en `errors[]`: `field` es el nombre del campo y `code` puede ser `validation.required`, `validation.length` o `validation.format`. |
| 422 con otro `code` | Regla de negocio; el catálogo está en convenciones, sección 8.2, y en cada endpoint del contrato. |
| 503 `service.unavailable` | La base de datos o Cognito no responden. Mensaje de «intenta en unos minutos» con el `request_id`. |
| 500 `internal` | Muestra el `request_id` para reportarlo. |

### 4.3 Formatos que importan

- Los campos opcionales **siempre vienen**, con `null` si no tienen valor.
- Fechas en RFC 3339 UTC (`2026-11-04T15:32:09Z`). Conviértelas a la zona del usuario al mostrarlas.
- **Ignora los campos que no conozcas**: agregar campos es un cambio compatible.
- Textos que vienen de la API del analista (evidencias, avisos de contratos): **siempre escapados**, nunca como HTML.
- **Severidades:** el color siempre va acompañado de texto, con contraste WCAG 2.1 AA (RNF-15).

## 5. Lo implementado, endpoint por endpoint

### 5.1 Cuenta: `GET /me` y `POST /me/terms`

- `GET /me` devuelve `id` (el de la plataforma, no el `sub` de Cognito), `name`, `email`, `role` (`analyst` o `admin`) y `terms`. La primera llamada da de alta al usuario en la base, así que llámalo justo después del inicio de sesión.
- `terms.acceptance_required: true` significa que no ha aceptado la versión vigente (`terms.current_version`). Sin aceptarla no puede crear proyectos (RN-12). Puede volver a `true` si se publica una versión nueva de los términos.
- El **texto** de los términos lo publica el frontend; la API solo maneja la versión (hoy `2026-10-30`). Si cambian el texto, acuerden la versión nueva con el backend.
- `POST /me/terms` con `{"version": "<current_version>"}`. Responde el mismo `Me`. Una versión distinta da 422 `terms.outdated_version`: vuelve a pedir `/me` y muestra los términos vigentes. Aceptar dos veces la misma versión no cambia la fecha.

### 5.2 Proyectos

- **Lista** `GET /projects`: `page`, `page_size` (1 a 100) y `sort` (`created_at`, `name`, `last_run_at`, con `-` para descendente; por defecto `-created_at`). Una página fuera de rango devuelve `items: []` con el `total` real.
- **Crear** `POST /projects` con `name` (1 a 100, se recortan espacios), `description` opcional (hasta 500; vacía cuenta como `null`) y `base_url`. Responde 201 con el dashboard y la cabecera `Location`.
- **Errores de la URL base** (422, con `errors[0].field = "base_url"`): `url.invalid_format` (sin esquema, con usuario o contraseña, con `#fragmento`, puerto inválido), `url.scheme_not_allowed` (no es `http` ni `https`) y `url.destination_not_allowed` (resuelve a una dirección privada, local, de metadatos o reservada).
- **Dashboard** `GET /projects/{project_id}`: verificación, contrato vigente, última ejecución, hallazgos abiertos por severidad y los siete módulos con `available` y `missing`. Usa `missing` para explicar qué falta (RF-45). Los módulos `property_access`, `resource_consumption` y `sql_injection` tienen riesgo `medium` o `high` y exigirán confirmación en cada ejecución (RN-05).
- **Editar** `PATCH /projects/{project_id}`: solo los campos que envías; `"description": null` la borra; `name` y `base_url` no aceptan `null`; un cuerpo vacío da 422. Si cambia el **host**, el proyecto vuelve a `pending`.
- **Eliminar** `DELETE /projects/{project_id}?confirmation=<nombre exacto>`. Responde 204. `project.confirmation_mismatch` (422) si el nombre no coincide; `project.active_run` (409) si hay una ejecución en cola o en curso.
- **Advertencias** (`warnings[]`), muéstralas siempre que vengan:

  | Código | Tipo | Cuándo |
  | --- | --- | --- |
  | `url.no_tls` | Persistente | La URL base usa HTTP. Vuelve en cada respuesta mientras siga así. |
  | `url.unresolved` | Momentánea | Al crear o editar, el host aún no resuelve en DNS. El proyecto se guarda igual. |
  | `project.verification_lost` | Momentánea | Al editar, cambió el host de un proyecto verificado. Solo viene en esa respuesta: muéstrala en ese momento. |

### 5.3 Verificación de propiedad

- **Instrucciones** `GET /projects/{project_id}/verification`: `status` (`pending` o `verified`), `host`, `code`, `method` y `verified_at` (ambos `null` mientras esté pendiente), y los datos de cada método listos para mostrar:
  - `file.url` y `file.content`: el archivo va en la raíz del host, con el esquema y el puerto de la URL base (la ruta de la URL base no cuenta). Su contenido es solo el código; se toleran espacios y saltos de línea al inicio o al final.
  - `dns.name`, `dns.type` (`TXT`) y `dns.value`: el registro va en `_hindama-verificacion.<host>`, solo para el host exacto. El del dominio padre no cuenta.
- **Comprobar** `POST /projects/{project_id}/verification` con `{"method": "file"}` o `{"method": "dns"}`. Es síncrona y puede tardar hasta 20 segundos: muestra un estado de espera y no permitas un segundo envío mientras tanto. Si responde 200, devuelve la misma `Verification` ya en `verified`, y el dashboard deja de listar `project_not_verified` en `missing`.
- **Si falla** responde 422 con `application/problem+json`, y el proyecto queda en `pending`, **aunque antes estuviera verificado**. El campo `found` resume lo que se obtuvo y puede ser `null`. Es texto del servidor del analista, no de Hindama: muéstralo siempre escapado y nunca como HTML.

  | `code` | Qué pasó | Qué sugerir |
  | --- | --- | --- |
  | `verification.file_not_found` | El servidor respondió con un error (`found`: `HTTP 404`, `HTTP 500`…). | Publicar el archivo en `file.url`. |
  | `verification.content_mismatch` | El archivo existe, pero no contiene exactamente el código, o pesa más de 1 KiB. | Copiar `file.content` tal cual, sin nada más. |
  | `verification.txt_missing` | No hay un TXT con el código. `found` lista los TXT encontrados, o es `null` si no hay ninguno. | Crear el registro y esperar a que el DNS se propague. |
  | `verification.connection_error` | El host no resuelve, no responde, se agotó el tiempo de espera o el certificado TLS no es válido. | Revisar que la URL base responda desde Internet. |
  | `verification.destination_not_allowed` | El host resuelve a una dirección privada o reservada, o redirige fuera del host. | Usar una dirección pública, sin redirecciones a otro host. |

- Un `method` distinto de `file` o `dns` da 422 `validation.failed` con el esquema `Problem` normal. Un proyecto ajeno o inexistente da 404 en ambos endpoints.

### 5.4 Contrato y operaciones

- **Importar** `POST /projects/{project_id}/contracts` como `multipart/form-data`, con **exactamente uno** de dos campos:
  - `file`: el documento OpenAPI 3.0 o 3.1, en JSON o YAML, de hasta 5 MB.
  - `url`: una URL pública `http` o `https`, que puede estar en otro host distinto al de la API.

  No hace falta que el proyecto esté verificado. La petición es síncrona y puede tardar hasta 30 segundos: muestra un estado de espera.
- **Respuestas:**
  - **201:** se creó una versión nueva. Trae la cabecera `Location`.
  - **200:** el documento es idéntico a la versión vigente y no se creó otra. Trae la advertencia momentánea `contract.unchanged`.

  En ambos casos el cuerpo es la `ContractVersion`, con `warnings` y `changes`.
- **Errores:**

  | `code` | Estado | Qué mostrar |
  | --- | --- | --- |
  | `contract.source_required` | 422 | Faltó el archivo y la URL, o se enviaron los dos. |
  | `contract.too_large` | 413 | El documento pesa más de 5 MB (por archivo o por URL). |
  | `contract.invalid` | 422 | Lista `errors[]`: `field` es un JSON Pointer (`/paths/~1orders/get/responses`) o «línea N», con su `message`. |
  | `contract.unsupported_version` | 422 | Es Swagger 2 u otra versión: pide convertirlo a OpenAPI 3. |
  | `contract.url_not_allowed` | 422 | La URL no es `http`/`https`, lleva usuario o contraseña, o apunta a una dirección privada o reservada. |
  | `contract.url_unreachable` | 422 | La URL no respondió, no resolvió o no devolvió 200. |

  Los `code` de `errors[]` en `contract.invalid` sirven para elegir un texto propio: `contract.invalid_json`, `contract.invalid_yaml`, `contract.yaml_alias` (no se admiten anclas `&` ni alias `*` de YAML), `contract.encoding`, `contract.empty`, `contract.too_deep`, `contract.required_field`, `contract.invalid_type`, `contract.invalid_value`, `contract.unresolved_reference`, `contract.circular_reference`, `contract.duplicate_operation`, `contract.too_many_operations` (más de 2 000) y `contract.too_complex`.
- **Avisos de la versión** (`warnings[]`, guardados con ella). `location` es un JSON Pointer dentro del documento:

  | Código | Cuándo |
  | --- | --- |
  | `contract.servers_mismatch` | Un servidor del contrato está en otro host. Las pruebas usan siempre la URL base del proyecto (RF-27). |
  | `contract.external_reference` | Una `$ref` a otro archivo o URL. No se sigue, y lo que dependía de ella queda fuera (RF-23). |
  | `contract.unparsed_element` | `webhooks`, `callbacks` o un esquema de seguridad que no está declarado en `components.securitySchemes`. |

- **Versiones** `GET /projects/{project_id}/contracts`: de la más reciente a la más antigua. `GET .../contracts/{contract_id}` trae `is_current` y `changes`:
  - `changes` es `null` en la primera versión.
  - En las demás tiene `added`, `modified` y `removed` respecto a la versión anterior (RF-26).
  - `modified` incluye los cambios en los esquemas compartidos que usa la operación.
- **Operaciones** `GET /projects/{project_id}/operations`: las de la versión vigente, ordenadas por ruta y luego por método.
  - Filtros: `method` e `include_retired=true` (agrega las retiradas, con `retired_at`).
  - `page_size` acepta hasta 500, y por defecto es 100.
  - Una operación conserva su `id` entre versiones: `/users/{id}` y `/users/{userId}` son la misma.
- **Texto no confiable:** `api_title`, `summary`, `tags`, `operation_id`, nombres de parámetros y rutas vienen del documento del analista. Muéstralos escapados, nunca como HTML.

### 5.5 Identidades

- **Lista** `GET /projects/{project_id}/identities`: la anónima va primero y después las demás, por fecha de creación. Cada proyecto la tiene desde que se crea: `auth_type: none`, sin credencial. No se edita, no se elimina ni se prueba (409 `identity.anonymous`).
- **Registrar** `POST /projects/{project_id}/identities` con `name`, `role` (`admin`, `user` u `other`), `role_label` opcional, `auth_type` y `credential`. La forma de `credential` depende de `auth_type`:

  | `auth_type` | `credential` | Además |
  | --- | --- | --- |
  | `bearer` | `{"token": "…"}` (sin `Bearer `) | — |
  | `cookie` | `{"value": "…"}` | `field_name`: nombre de la cookie |
  | `header` | `{"value": "…"}` | `field_name`: nombre de la cabecera. No se admiten `Host`, `Content-Length`, `Cookie`, `User-Agent`… |
  | `login` | `{"username": "…", "password": "…"}` | `login_operation_id`: una operación vigente. Las candidatas traen `is_login_candidate: true` en `/operations` |

- **La credencial nunca vuelve.** La respuesta trae `credential_suffix`:
  - con `bearer`, `cookie` o `header`: los últimos 4 caracteres, o vacío si la credencial mide menos de 8;
  - con `login`: los últimos 4 caracteres del usuario. La contraseña nunca se muestra, ni en parte.

  Para cambiar la credencial, se envía completa otra vez.
- **Editar** `PATCH …/identities/{identity_id}`: solo los campos enviados. Si cambia `auth_type`, hay que enviar también la `credential` de la forma nueva (422 `identity.credential_required`). Una credencial nueva deja la identidad en `status: active`.
- **Eliminar** `DELETE …/identities/{identity_id}` responde 204:
  - la credencial se borra en el acto y el nombre queda libre;
  - se eliminan sus recursos;
  - sus hallazgos abiertos pasan a «resuelto».

  Con una ejecución activa responde 409 `project.active_run`.
- **Probar** `POST …/identities/{identity_id}/test`:
  - Cuerpo opcional `{"operation_id": "…"}`. Si falta, el sistema elige un GET protegido sin parámetros de ruta.
  - Exige el proyecto verificado (409 `project.not_verified`). Es síncrona y puede tardar hasta 20 s.
  - **Responde 200 aunque la credencial falle.** Mira `succeeded`, `status_code` y `failure`: `rejected` (la API no respondió 2xx; las redirecciones no se siguen), `login_failed`, `connection_error` o `destination_not_allowed`.
  - El resultado queda en `last_tested_at` y `last_test_status_code` de la identidad.
- **Errores al registrar o editar** (422 salvo que se indique):
  - `identity.credential_mismatch`;
  - `identity.field_name_required`;
  - `identity.field_name_reserved`;
  - `identity.login_operation_required`;
  - `identity.name_taken` (409);
  - `identity.limit_reached` (409, a las 20 contando la anónima).

  Al probar: `identity.no_test_operation`, si no hay un GET protegido sin parámetros de ruta o el indicado no sirve.
- **Aviso persistente** `identity.no_resources`: la identidad no tiene recursos y el módulo de acceso a objetos no podrá probarla.

### 5.6 Recursos

- **Lista** `GET /projects/{project_id}/resources`: por tipo y luego por identificador. Filtros: `identity_id` y `resource_type`.
- **Registrar** `POST …/resources` con `identity_id`, `resource_type` (por ejemplo `orders`) y `value` (el identificador en la API del analista, como `101`). Queda con `source: manual` y `confirmed: true`.
- **Editar o confirmar** `PATCH …/resources/{resource_id}`: `identity_id`, `resource_type`, `value` o `confirmed`.
- **Eliminar** `DELETE …/resources/{resource_id}` responde 204.
- **Errores:**
  - `resource.owned_by_other` (409): ese tipo e identificador ya están registrados. Un objeto tiene un solo dueño.
  - `identity.not_found` (422): la identidad no existe o fue eliminada.
  - `resource.anonymous_owner` (422): la identidad anónima no tiene recursos.
- Usa el mismo `resource_type` que en `resource_parameters` de las operaciones (sección 5.7): así el módulo de acceso a objetos sabe qué recurso va en cada ruta.

### 5.7 Política de acceso

- **Propuesta del sistema.** Al importar el contrato, cada operación trae:
  - `suggested_policy`: `public` si no declara seguridad, `admin_only` en un área de administración, `owner_only` si la ruta termina en un identificador, `authenticated` en lo demás;
  - `resource_parameters`: los parámetros de ruta que parecen identificadores, con un tipo tomado del segmento anterior (`/orders/{orderId}` → `orders`).

  **Las propuestas no se usan en las pruebas** hasta que el analista las confirma (`policy` no nula). Muéstralas como sugerencia, con una acción para aceptarlas.
- **Confirmar una operación** `PATCH /projects/{project_id}/operations/{operation_id}` con cualquiera de estos campos:
  - `policy`: fijarla es confirmarla, y `null` la deja sin confirmar.
  - `owner_field`: obligatorio con `owner_only` y `owner_or_admin`. Es un parámetro (`userId`) o un campo de la respuesta (`owner.id`). Al cambiar a otra plantilla se borra.
  - `resource_parameters`: reemplaza la selección completa.

  Devuelve la `Operation` completa, con `confirmed_at` y `modified_at`.
- **En bloque** `POST /projects/{project_id}/policy` con `operation_ids` (hasta 500, sin repetidos), `policy` y `owner_field`. Es todo o nada. Devuelve `items` ordenados por ruta y método.
- **Errores:**
  - `policy.owner_field_required` (422);
  - `operation.unknown_parameter` (422; `errors[].field` es `resource_parameters.N.name`);
  - `operation.not_found` (422 en bloque; `errors[].field` es `operation_ids.N`);
  - `operation.retired` (409): la operación ya no está en el contrato vigente.
- **Al reimportar el contrato:**
  - las políticas confirmadas se conservan;
  - los parámetros de recurso editados se conservan, menos los que ya no estén en la ruta;
  - la sugerencia se recalcula.
- Confirmar políticas y registrar recursos va quitando requisitos de `modules[].missing` en el dashboard (`policy_unconfirmed`, `no_resources`).

### 5.8 Ejecuciones (contrato 0.4.0)

Implementados: lanzar, listar, consultar, cancelar, el stream de progreso y la matriz. Pendiente en el backend: el descubrimiento de recursos; mientras tanto, usa el simulador.

- **Antes de lanzar.** El dashboard (`GET /projects/{project_id}`) trae `modules[]` con `risk`, `available` y `missing`. Muestra deshabilitados los módulos no disponibles, con lo que les falta (RF-45). Los de riesgo `medium` y `high` empiezan apagados (RN-05).
- **Lanzar** `POST /projects/{project_id}/runs` con:
  - `modules`: uno o varios, sin repetir. «Prueba completa» es enviar todos los disponibles.
  - `limits` (opcional): `requests_per_second` (1 a 20, por defecto 5), `concurrency` (1 a 5, por defecto 2), `max_requests` (hasta 5 000) y `max_duration_minutes` (hasta 30).
  - `confirm_risk: true`, obligatorio si hay un módulo de riesgo medio o alto. Pide la confirmación **en cada ejecución**, con la advertencia, y no la recuerdes entre ejecuciones (RF-46).

  Responde **202** con la `Run` en `queued` y `Location`. Abre la vista de progreso.
- **Errores al lanzar:**
  - `project.not_verified` y `project.active_run` (409). En el segundo, ofrece ir a la ejecución activa: es el `last_run` del dashboard.
  - `run.module_unavailable` (422; `errors[].field` es `modules.N`): el dashboard cambió desde que lo cargaste. Recárgalo.
  - `run.risk_not_confirmed` (422).
  - `service.unavailable` (503): la cola no responde y no se creó nada. Se puede reintentar.
- **Progreso en tiempo real** `GET …/runs/{run_id}/events` (SSE). En el navegador, `new EventSource('/api/projects/{pid}/runs/{rid}/progress')`; el route handler de Next.js agrega el Bearer y retransmite el stream **sin búfer ni transformación**, y cierra la conexión con FastAPI cuando el navegador cierra la suya (ADR-006).
  - `snapshot` (`Run` completa): siempre primero, también al reconectar.
  - `progress` (`RunProgress`): `current_module`, `requests_sent`, `percent` y `findings_by_severity`. Llega solo cuando algo cambió, como máximo uno por segundo. Una ejecución corta puede pasar de `snapshot` directo a `end`: no esperes un número fijo de `progress`.
  - `end` (`Run`): la ejecución terminó y el servidor cierra el stream. Navega al resumen y **no** dejes que `EventSource` reconecte (llama a `close()`).
  - Un `: ping` cada 15 s mantiene viva la conexión: no la cortes por inactividad.
  - `EventSource` reconecta solo, con `Last-Event-ID`. Si falla varias veces, consulta `GET …/runs/{run_id}`, que trae lo mismo que `snapshot`.
  - El servidor cierra el stream a los 15 minutos aunque la ejecución siga. Es normal: `EventSource` reconecta y recibe un `snapshot` nuevo. Los `id:` siguen creciendo entre reconexiones.
  - Un recurso ajeno o inexistente responde 404 antes de abrir el stream, en Problem Details (no `text/event-stream`).
- **Cancelar** `POST …/runs/{run_id}/cancel` (pide confirmación antes). Responde 202 con la `Run`: si estaba en cola, ya viene `cancelled`; si estaba en curso, viene `cancel_requested_at` y el `end` llega en menos de 5 s (en las pruebas, en menos de 1 s). Repetirla mientras se detiene responde lo mismo. `run.not_active` (409) significa que ya había terminado. `service.unavailable` (503): la cola no respondió y la ejecución sigue en curso; se puede reintentar.
- **Historial** `GET …/runs`: de la más reciente a la más antigua, con filtro `status` (se repite para varios valores). Cada elemento es un `RunSummary`, igual que `last_run`, con `end_reason`, `modules`, `requests_sent` y `findings_by_severity`. La duración es `finished_at` menos `started_at`.
- **Estado final y motivo** (`end_reason`): `completed` con `normal` o `limit_reached` (avisa que se detuvo por un límite y que los resultados son parciales); `cancelled` con `cancelled_by_user` o `verification_invalid` (el proyecto volvió a «Pendiente de verificación», RF-20); `failed` con `heartbeat_expired`, `lost_in_queue` o `error`.
  - `heartbeat_expired`: el motor dejó de responder a mitad de la ejecución. Los resultados que alcanzó a registrar se conservan. Se detecta en menos de 6 minutos (una pasada de la reconciliación cada 5 minutos, tras 60 s sin latido).
  - `lost_in_queue`: la ejecución esperó más de 10 minutos y su trabajo se perdió de la cola. Si el trabajo se pierde antes, la plataforma lo vuelve a encolar sin que el analista haga nada.
  - En los dos casos, un stream abierto recibe `end`. Sugiere volver a lanzar la ejecución.
- **Recursos que no se pudieron borrar:** si `created_resources.failed` es mayor que 0, avisa al analista que debe borrarlos a mano en su API (CU-23 E1).
- **Matriz identidad × operación** `GET …/runs/{run_id}/results` (RF-64). Cada elemento es una celda con `module`, `operation` (`null` en las comprobaciones de toda la API), `identity`, `expected`, `observed` y `verdict`. Una discrepancia es `verdict: fail`: márcala con color **y** texto (RNF-15). `page_size` acepta hasta 500; filtra por `module` para armar una matriz por módulo. `expected` y `observed` son códigos cortos en inglés (`allowed`, `denied`, `own_data_only`…) con el vocabulario del [catálogo del laboratorio](../05-pruebas/catalogo-laboratorio.md) (secciones 3.1, 4 y 7.1): tradúcelos cuando los conozcas y muéstralos tal cual si no.
- **Descubrir recursos** `POST /projects/{project_id}/resources/discovery` (CU-10, RF-36), con `identity_ids` opcional. Síncrona, hasta 25 s. Devuelve los recursos nuevos en `created` (sin confirmar, para que el analista los revise en la sección 5.6) y, por identidad, cuántos encontró y si falló (`failure`, con los mismos valores que la prueba de una identidad y `not_attempted`). Si `truncated` es `true`, puede haber más. Errores: `project.not_verified`, `project.active_run` (409) y `resource.no_list_operations` (422).

### 5.9 Hallazgos (contrato 0.5.0)

En el contrato y en el simulador; el backend los implementa en la tarea 4.1. Un hallazgo es una falla **lógica**: aparece una sola vez aunque varias ejecuciones lo detecten, y cada detección es una **ocurrencia** con su evidencia (RF-68).

- **Lista** `GET /projects/{project_id}/findings` (RF-65). Ordenada por severidad y luego por la detección más reciente. Filtros repetibles `module`, `severity` y `status`, más `run_id`, `identity_id` y `operation_id`.
  - Los **abiertos** son `new`, `persistent` y `regression`. Para la vista de pendientes, envía los tres en `status`.
  - `run_id` da «lo que encontró esta ejecución» para el resumen (CU-15). Cada hallazgo trae su estado **actual**, que puede ser distinto del que tuvo en esa ejecución.
  - `operation_id` con `identity_id` lleva de una celda `fail` de la matriz a su hallazgo.
  - La severidad va con color **y** texto (RNF-15).
- **Detalle** `GET …/findings/{finding_id}` (RF-62, RF-66): título, clasificación (`owasp_category`, `cwe`), `recommendation`, `last_occurrence` con su `explanation` y `evidence`, y `history`, que es la evolución de estados (RF-72).
  - `dismissal` trae el motivo y la justificación cuando el hallazgo está en `accepted_risk`. Muestra «Riesgo aceptado» o «Falso positivo» según `dismissal.reason`.
  - `resolution_reason` explica un `resolved`: `not_detected` (una ejecución lo volvió a evaluar y ya no apareció), `identity_deleted` u `operation_retired`.
  - En `history`, `run: null` significa que el cambio lo hizo el analista.
- **Evidencia** (`Evidence`): `request` (método, URL, cabeceras y `body`, que hoy siempre es `null`), `response` (código, cabeceras, cuerpo de hasta 10 KB y `body_truncated`) y `context`, con datos del módulo como el recurso ajeno en acceso a objetos. Las credenciales ya vienen enmascaradas (`****abcd`).
  - Todo lo que viene de la API del analista, como las cabeceras, el cuerpo y la URL, **no es confiable**. Muéstralo siempre como texto, nunca como HTML ni Markdown interpretado.
  - `context` puede traer claves nuevas cuando lleguen más módulos: muestra las que conozcas e ignora las demás.
- **Ocurrencias anteriores** `GET …/findings/{finding_id}/occurrences`: una por ejecución, de la más reciente a la más antigua, de 10 en 10 (hasta 20 por página).
- **Aceptar el riesgo o marcar falso positivo** `POST …/findings/{finding_id}/dismissal` (CU-16, RF-70), con `reason` (`accepted_risk` o `false_positive`) y `justification` (obligatoria, hasta 2 000 caracteres, RN-09). Responde 200 con el hallazgo en `accepted_risk`.
  - `finding.not_open` (409): ya estaba resuelto o aceptado. Recarga el detalle.
  - Un hallazgo aceptado que se vuelve a detectar **sigue** aceptado; solo gana una ocurrencia.
- **Revertir** `DELETE …/findings/{finding_id}/dismissal` (pide confirmación). Responde 204 y el hallazgo vuelve a `persistent`; recarga el detalle. `finding.not_dismissed` (409): no estaba aceptado.
- **Concluido** (RF-73): cuando un proyecto no tiene hallazgos abiertos y sí una ejecución completada, el dashboard lo muestra como `concluded`. Aceptar el último hallazgo abierto puede concluirlo.

## 6. Trabajar sin el backend: el simulador

Para lo que aún no está implementado (o para no levantar el backend):

```bash
npx @stoplight/prism-cli mock hindama-docs/03-api/openapi.yaml   # http://localhost:4010
```

Responde con los ejemplos del contrato. Elige uno con `Prefer: example=newHttpProject`, o un estado con `Prefer: code=422`. También rechaza peticiones que no cumplen el contrato. Genera los tipos con `npx openapi-typescript hindama-docs/03-api/openapi.yaml -o src/lib/api/schema.d.ts`.

## 7. Levantar el backend en local

Necesitas acceso al repositorio `hindama-backend` y Docker Desktop.

1. Copia `.env.example` a `.env` y cambia:
   - Las contraseñas de la base de datos y `HINDAMA_REDIS_PASSWORD` por valores aleatorios largos.
   - `HINDAMA_COGNITO_USER_POOL_ID` y `HINDAMA_COGNITO_CLIENT_ID` por los de la sección 2.1. El backend no usa el secreto del cliente.
2. `docker compose up -d --build`. Levanta PostgreSQL, Redis, la API y el motor de pruebas (`scanner`). La API queda en `http://localhost:8000` (`GET /health` responde 200). En desarrollo, `http://localhost:8000/docs` muestra la documentación interactiva.
3. Para probar a mano con un token real, sigue la sección 2.4 de [`deploy/PROCEDIMIENTO.md`](../../hindama-backend/deploy/PROCEDIMIENTO.md) (`get-dev-token.sh`).

En producción, Next.js habla con la API por la red privada entre las dos EC2; la dirección se definirá con el despliegue de la semana 3.

## 8. Cómo pedir cambios

- ¿Falta un campo o un endpoint? Pull request a `hindama-docs` que cambia `openapi.yaml` (con `info.version` actualizado), revisado por los dos. Después el backend lo implementa y tú lo consumes (ADR-016).
- Los identificadores técnicos van en inglés y los textos para el usuario en español ([glosario](glosario-identificadores.md), ADR-017).
- Si algo de esta guía no coincide con lo que hace la API, avisa: o la guía está mal o el backend tiene un error.

## 9. Historial de esta guía

| Fecha | Cambio |
| --- | --- |
| 2026-11-04 | Primera versión: User Pool `hindama-dev`, `/me`, `/me/terms` y proyectos. |
| 2026-11-04 | Sección 2.1: pasos completos para leer el secreto del cliente con el usuario de IAM propio, comprobaciones y errores comunes. |
| 2026-11-05 | Contrato 0.2.1: `page` admite hasta 10 000, `confirmation` no puede ir vacía y los textos rechazan caracteres de control (`validation.format`). Un formulario normal no se ve afectado. |
| 2026-11-15 | Sección 5.3: verificación de propiedad (`GET` y `POST /projects/{project_id}/verification`), con sus errores y qué sugerir en cada uno. |
| 2026-11-16 | Sección 5.4: importar el contrato por archivo o URL, sus errores y avisos, versiones con diferencias y lista de operaciones. |
| 2026-11-16 | Contrato 0.3.0: identidades, recursos manuales y política de acceso, en el simulador. `Operation` trae campos nuevos (`suggested_policy`, `policy`, `owner_field`, `confirmed_at`, `modified_at`, `resource_parameters`, `is_login_candidate`). |
| 2026-11-16 | El backend implementa todo el contrato 0.3.0 (identidades, recursos y política). Al importar, cada operación trae `suggested_policy` y `resource_parameters` propuestos; la regla está en modelo.md («Propuestas al importar»). |
| 2026-11-16 | Secciones 5.5 a 5.7: identidades (registrar, probar y eliminar), recursos y política de acceso, con sus errores. |
| 2026-11-16 | Contrato 0.4.0 y sección 5.8: ejecuciones (lanzar, listar, consultar, cancelar), progreso por SSE, matriz de resultados y descubrimiento de recursos, en el simulador. `RunSummary` (el `last_run` del dashboard) gana `end_reason`, `modules`, `requests_sent`, `findings_by_severity` y `started_at`. |
| 2026-11-16 | El backend implementa lanzar, listar y consultar ejecuciones, con Redis y el motor en Compose (sección 7). Sin módulos todavía, una ejecución termina `completed` con 0 celdas. |
| 2026-11-17 | Corrección a la entrada anterior: el motor ya tiene cuatro módulos (acceso a objetos, acceso a funciones, autenticación y configuración), así que una ejecución genera celdas y hallazgos. `expected` y `observed` usan el vocabulario del catálogo del laboratorio, y el cuerpo de la respuesta en la evidencia se muestra siempre como texto. |
| 2026-11-17 | El backend implementa cancelar y el progreso por SSE (sección 5.8). El stream envía `progress` solo cuando algo cambia, puede pasar de `snapshot` a `end` sin `progress` y se cierra a los 15 minutos para que el navegador reconecte. |
| 2026-11-17 | El backend reconcilia las ejecuciones interrumpidas (sección 5.8): `heartbeat_expired` y `lost_in_queue` ya ocurren de verdad, y una ejecución atascada deja de bloquear el proyecto. |
| 2026-11-18 | El backend implementa la matriz identidad × operación (sección 5.8). Contrato 0.5.0 y sección 5.9: hallazgos (lista, detalle con evidencia e historial, ocurrencias, aceptar el riesgo o marcar falso positivo y revertir), en el simulador. |
