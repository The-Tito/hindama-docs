# ADR-007: Credenciales de identidades cifradas con AES-256-GCM y clave maestra en SSM Parameter Store

- **Estado:** aceptada (revisada el 2026-10-30 tras [ADR-010](ADR-010-una-sola-cuenta-aws.md) y [ADR-011](ADR-011-despliegue-con-compose-y-procedimiento.md))
- **Fecha:** 2026-10-30
- **Relacionado con:** RN-11, RF-31, RNF-06, sección 9.4 de requerimientos (clave fuera de la base de datos)

## Contexto

Las credenciales de las identidades de prueba (contraseñas, tokens, cookies, cabeceras) deben cifrarse en reposo con AES-256-GCM, con la clave fuera de la base de datos. Nunca deben aparecer en registros, evidencias, respuestas ni excepciones.

## Decisión

- **Clave maestra:** 256 bits en **SSM Parameter Store** como `SecureString`, cifrada por AWS con la llave administrada `aws/ssm`, que no tiene costo. Al arrancar, los contenedores `api` y `worker` la reciben como variable de entorno. No se escribe en disco.
- **Cifrado:** cada credencial se cifra con AES-256-GCM usando un nonce aleatorio de 96 bits. Se guarda `version_clave || nonce || texto_cifrado || tag`, con el `id` de la identidad como dato asociado (AAD), para que un texto cifrado no se pueda mover a otra fila.
- **Visibilidad:**
  - Solo se guardan aparte los últimos 4 caracteres para mostrarlos.
  - Los modelos de respuesta nunca incluyen el campo cifrado.
  - Los registros y la evidencia pasan por un filtro de enmascarado.
- **Rotación:** el campo `version_clave` permite rotar la clave. Un script vuelve a cifrar las filas con la clave nueva y después se retira la anterior.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Cifrado de sobre con una llave de AWS KMS propia | Más robusto: la clave maestra nunca sale de KMS. Pero cuesta 1 USD al mes más peticiones, y cada ejecución requiere llamar a KMS. Queda como mejora si sobra presupuesto. |
| Secrets Manager | 0.40 USD al mes por secreto, sin ventaja sobre SecureString para este uso. |
| Clave en el archivo `.env` de la EC2 | Queda en disco y en los respaldos de EBS. |
| `pgcrypto` en PostgreSQL | La clave viajaría en las consultas SQL y podría quedar en los registros de la base de datos. |

## Consecuencias

- **Positivas:** no tiene costo, y la clave nunca está en la base de datos ni en los respaldos.
- **Negativas:**
  - Quien tenga acceso a la EC2 del backend, o a `ssm:GetParameter` en la cuenta, puede obtener la clave. Se restringe el rol IAM de la instancia a los parámetros `/hindama/backend/*` y el acceso humano a los dos integrantes con MFA.
  - Al mover la plataforma a la cuenta de respaldo (ADR-011), la clave maestra debe migrar junto con la base de datos o las credenciales quedan ilegibles. Se guarda una copia fuera de línea junto a la llave privada de los respaldos.

## Resultado de la implementación (2026-11-16)

Implementado en la tarea 2.5 del backend (`core/credentials.py`, `services/identities.py`). La decisión no cambia; se precisaron estos puntos:

| Punto | Cómo quedó | Por qué |
| --- | --- | --- |
| Formato | `versión (1 byte) ‖ nonce (12) ‖ texto cifrado ‖ tag (16)`, con `cryptography` (AESGCM) | El de la decisión. El nonce es aleatorio en cada cifrado: dos cifrados de la misma credencial nunca coinciden |
| Dato asociado | `id` de la identidad **y** versión de la llave | Con solo el `id`, cambiar el byte de versión de una fila no se detectaba por la firma, sino por la llave equivocada. Así, cualquier alteración del encabezado falla la autenticación |
| Llaves | `HINDAMA_CREDENTIAL_KEYS` como mapa JSON `{versión: base64}` y `HINDAMA_CREDENTIAL_KEY_VERSION` | Rotar es agregar una versión sin dejar ilegibles las filas viejas. La API no arranca sin llave ni con una que no mida 32 bytes |
| Errores de configuración | `hide_input_in_errors` en la configuración | Una prueba mostró que el error de validación de Pydantic copiaba los valores leídos (`input_value`), y con ellos podía salir una llave en el registro de arranque |
| Sufijo visible (RF-31) | Los últimos 4 caracteres del token o del valor solo si mide 8 o más; en `login`, del usuario | En una credencial corta, 4 caracteres revelan la mitad o más. La contraseña nunca se muestra, ni en parte |
| Credencial en memoria | Tipo propio cuyo `repr` es `Credential(token: ***)` | Una traza o un registro accidental no la imprime |
| Credencial ilegible | 500 sin detalles y un evento `identity_credential_unreadable` en el registro | Una llave perdida o una fila alterada es una falla interna, no del analista (RNF-07) |

**Prueba de la identidad (RF-32).** Pasa por la guardia SSRF (ADR-008) y **no sigue redirecciones**: un 3xx cuenta como respuesta (`rejected`), para que la credencial nunca se reenvíe a otro destino. Los valores de las cabeceras se envían como bytes UTF-8: como texto, httpx rechazaba (500) un valor con caracteres fuera de ASCII.

**Evidencia:** 27 pruebas unitarias del cifrado y de la configuración (alteración de cada parte del valor guardado, fila ajena, llave equivocada, versión no cargada, rotación, nada secreto en `repr` ni en los errores), 34 del probador contra un servidor local y 43 de integración con PostgreSQL. Estas últimas incluyen que la credencial no aparezca en ninguna respuesta ni en el registro y que se guarde cifrada y ligada a su fila. Schemathesis: 1 595 casos sin fallas en 19 operaciones.

**Fallas encontradas de paso** (cada una con su prueba de regresión):

1. **No se podía borrar la cuenta de un analista con historial** (RF-88). Las llaves de `finding_events.user_id` y `operations.modified_by` hacia `users` se revisaban antes de que la cascada borrara las filas. Ahora se revisan al confirmar la transacción (migración `5b2e9c4d7a10`; modelo.md, sección 5.1). La prueba falla sin la migración y pasa con ella.
2. **La prueba de contrato era intermitente.** Ordenaba las opciones de un `oneOf` con `repr()`, que depende del orden de las llaves, y ese orden cambia con `PYTHONHASHSEED`. El `oneOf` de `Credential` fue el primero con varios objetos. Antes fallaba con 4 de 20 semillas; ahora se ordena con JSON canónico y pasa con las 20.

