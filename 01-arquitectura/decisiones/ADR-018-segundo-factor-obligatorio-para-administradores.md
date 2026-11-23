# ADR-018: Segundo factor obligatorio para administradores en el mismo User Pool, exigido por la API

- **Estado:** aceptada
- **Fecha:** 2026-11-23
- **Relacionado con:** RF-85, RF-86, RF-87, RNF-08, CU-22, [ADR-005](ADR-005-sesion-bff-con-cookie-cifrada.md), [arquitectura, pendientes](../arquitectura.md)
- **Resuelve:** la propuesta abierta de `arquitectura.md` «Exigir 2FA a administradores (RF-86)», que planteaba un segundo User Pool.

## Contexto

RF-85 pide que cualquier usuario pueda activar el TOTP desde su perfil, y RF-86 que sea obligatorio para los administradores. Cognito configura el MFA por User Pool (`OFF`, `OPTIONAL` u `ON`), no por grupo, y el administrador es un usuario del pool `hindama-dev` con el grupo `administradores` (RN-04, RF-09).

Los access tokens de Cognito no dicen si el inicio de sesión usó el segundo factor (no traen `amr`). Lo que sí se sabe en cada petición es si el usuario **tiene activo** el TOTP: `GetUser`, que la API ya llama con el token del usuario para leer su nombre y correo (ADR-015), devuelve `UserMFASettingList`. Con el pool en `OPTIONAL`, Cognito pide el código en cada inicio de sesión a quien tiene el TOTP activo.

## Decisión

- **Un solo pool, con MFA `OPTIONAL` y solo TOTP** (sin SMS). Cualquier usuario lo activa desde su perfil con las llamadas de Cognito que hace el BFF (`AssociateSoftwareToken`, `VerifySoftwareToken`, `SetUserMFAPreference`).
- **La API exige el TOTP activo al administrador.** El guardia de `/admin/*` lee `UserMFASettingList` con `GetUser` y, si no contiene `SOFTWARE_TOKEN_MFA`, responde 403 `auth.mfa_required` (RF-86). La regla vive en la API, no en el frontend (RNF-08).
- **`GET /me` informa `mfa_enabled`**, para que Next.js lleve al administrador a activarlo y muestre el estado en el perfil.
- **Desactivarlo** (RF-87, CU-22 A1 y E2) lo hace el BFF con Cognito pidiendo antes un código válido, y no lo ofrece al administrador. Si un administrador lo desactivara por otra vía, la API lo vuelve a bloquear en su siguiente petición.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Segundo User Pool solo para administradores, con MFA `ON` (la propuesta original) | Otro pool, otro cliente y su secreto, y una API que valide dos emisores y deduzca el rol del emisor. Más configuración en AWS y en el BFF para el mismo resultado, y dos lugares donde mantener la política de contraseñas. |
| MFA `ON` en el pool único | Obliga a todos los analistas a usar TOTP, y RF-85 lo hace opcional para ellos. |
| Exigirlo solo en el BFF | La autorización no puede depender del frontend (RNF-08): una llamada directa a la API se lo saltaría. |
| Leer `amr` del token | Cognito no lo incluye en los tokens de User Pool. |

## Consecuencias

- **Positivas:**
  - Sin recursos nuevos en AWS ni cambios en la validación del token: un ajuste del pool (`SetUserPoolMfaConfig`) y una comprobación en el guardia `Admin`.
  - El rol sigue saliendo del grupo `administradores`, como hasta ahora.
- **Negativas y límites:**
  - Cada petición a `/admin/*` hace una llamada a `GetUser`. Ese tráfico es bajo y la llamada ya ocurre en `GET /me`.
  - La primera activación ocurre con una sesión que no usó el segundo factor. Quien tenga la contraseña de un administrador sin TOTP podría activarlo él mismo. Es el mismo riesgo que con un pool en `ON`, cuyo primer inicio de sesión también pide configurar el TOTP. Por eso el grupo `administradores` se asigna desde la consola (RF-09) a una cuenta que ya tiene el TOTP activo.
  - El access token de esa sesión (15 minutos) sirve para el panel en cuanto se activa el TOTP, sin volver a iniciar sesión.
