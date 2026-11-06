---
documento: Guía de integración para el frontend
proyecto: Hindama
version: 0.2
fecha: 2026-11-04
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
| API: verificación (`/verification`), contratos (`/contracts`) y operaciones (`/operations`) | En el contrato, sin implementar. Usa el simulador (sección 6) |
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

## 6. Trabajar sin el backend: el simulador

Para lo que aún no está implementado (o para no levantar el backend):

```bash
npx @stoplight/prism-cli mock hindama-docs/03-api/openapi.yaml   # http://localhost:4010
```

Responde con los ejemplos del contrato. Elige uno con `Prefer: example=newHttpProject`, o un estado con `Prefer: code=422`. También rechaza peticiones que no cumplen el contrato. Genera los tipos con `npx openapi-typescript hindama-docs/03-api/openapi.yaml -o src/lib/api/schema.d.ts`.

## 7. Levantar el backend en local

Necesitas acceso al repositorio `hindama-backend` y Docker Desktop.

1. Copia `.env.example` a `.env` y cambia:
   - Las tres contraseñas de la base de datos por valores aleatorios largos.
   - `HINDAMA_COGNITO_USER_POOL_ID` y `HINDAMA_COGNITO_CLIENT_ID` por los de la sección 2.1. El backend no usa el secreto del cliente.
2. `docker compose up -d --build`. La API queda en `http://localhost:8000` (`GET /health` responde 200). En desarrollo, `http://localhost:8000/docs` muestra la documentación interactiva.
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
