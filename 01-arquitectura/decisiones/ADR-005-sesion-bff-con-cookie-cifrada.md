# ADR-005: Sesión BFF con los tokens de Cognito en una cookie cifrada HttpOnly

- **Estado:** aceptada (revisada el 2026-10-30 tras [ADR-010](ADR-010-una-sola-cuenta-aws.md))
- **Fecha:** 2026-10-30
- **Relacionado con:** RF-04, RF-06, RF-07, RF-08, RNF-07, RNF-08

## Contexto

Los tokens de Cognito no deben ser accesibles desde el JavaScript del navegador (RF-08). Next.js actúa como BFF y es el único componente con el que habla el navegador. La EC2 del frontend no tiene base de datos ni Redis donde guardar sesiones del lado del servidor.

## Decisión

- **Formulario propio:** Next.js presenta formularios de Hindama y llama a Cognito **desde el servidor** con un **cliente de aplicación confidencial** (`InitiateAuth`, `RespondToAuthChallenge`, `REFRESH_TOKEN_AUTH`, `RevokeToken`, `SignUp`, `ConfirmSignUp`, `ForgotPassword`). El secreto del cliente vive solo en el servidor (SSM).
- **Contenido de la cookie:** solo el access token y el refresh token, cifrados con AES-256-GCM. La llave está en SSM. El id token no se guarda.
- **Atributos de la cookie:**
  - Nombre `__Host-hindama_sesion`, con `HttpOnly`, `Secure`, `SameSite=Lax` y `Path=/`.
  - Si el valor supera 4 KB, se divide en fragmentos numerados.
- **Renovación:** cuando el access token vence en menos de 5 minutos, Next.js lo renueva con el refresh token antes de reenviar la petición.
- **Reenvío:** Next.js envía a FastAPI la cabecera `Authorization: Bearer <access_token>`. FastAPI valida firma (JWKS), `iss`, `client_id`, `token_use = access` y `exp` en cada petición.
- **CSRF:** token sincronizado guardado en la sesión cifrada y enviado en `X-CSRF-Token`, más verificación del `Origin` en toda petición que modifica datos.
- **Rol:** el rol se consulta a FastAPI (`GET /yo`) y solo se usa para elegir la pantalla inicial; cada decisión de autorización la vuelve a tomar FastAPI.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Interfaz alojada de Cognito (Managed Login) con PKCE | Viable y evita manejar la contraseña en Next.js, pero la experiencia queda fuera del diseño propio y de los mensajes en español controlados. Se puede adoptar después sin cambiar el contrato con FastAPI. |
| Tokens en `localStorage` o en el cliente de Amplify | Expone los tokens al JavaScript del navegador: contradice RF-08. |
| Sesión del lado del servidor en Redis o RDS | La EC2 del frontend no tiene almacén. Usar el Redis del backend mezclaría responsabilidades y abriría un puerto más entre las dos EC2. |
| Guardar también el id token | Pasa fácilmente de 4 KB y no aporta nada que `/yo` no dé. |

## Consecuencias

- **Positivas:**
  - Los tokens nunca llegan al navegador.
  - Next.js no guarda estado y puede reiniciarse sin cerrar sesiones.
- **Negativas:**
  - La contraseña pasa por el servidor de Next.js, dentro de TLS. Next.js nunca debe registrar cuerpos de petición de las rutas de autenticación.
  - Una sesión robada no se invalida antes de que venza el access token (se configura con 15 minutos de vida). El cierre de sesión revoca el refresh token.
  - La llave de cifrado de la cookie es un secreto crítico. Rotarla cierra todas las sesiones.
