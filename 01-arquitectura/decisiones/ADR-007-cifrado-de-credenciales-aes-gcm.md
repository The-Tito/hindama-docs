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
