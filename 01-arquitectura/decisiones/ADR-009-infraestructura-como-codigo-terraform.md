# ADR-009: Infraestructura como código con Terraform, desplegable en una o dos cuentas

- **Estado:** sustituida por [ADR-011](ADR-011-despliegue-con-compose-y-procedimiento.md) el 2026-10-30. Terraform queda como mejora futura; con 4 semanas de desarrollo, el despliegue se hace con Docker Compose y un procedimiento escrito.
- **Fecha:** 2026-10-30
- **Relacionado con:** RNF-20, RNF-23, sección 11 de requerimientos (despliegue reproducible)

## Contexto

La plataforma se reparte en dos cuentas con créditos limitados que vencen alrededor de abril de 2027 (ADR-001). El equipo pidió que los scripts de despliegue permitan levantar la aplicación completa en cualquiera de las dos cuentas, para poder moverla si una se queda sin créditos o se cierra.

## Decisión

- Toda la infraestructura se describe en **Terraform**: VPC, subredes, peering, security groups, EC2, RDS, Cognito, parámetros de SSM, roles IAM y presupuestos.
- Hay **dos proveedores con alias**, `aws.frontend` y `aws.backend`, y una variable `modo`:
  - `dividido`: cada alias apunta a su cuenta.
  - `unico`: los dos alias apuntan a la misma cuenta. Se crean las mismas dos VPC y el peering dentro de esa cuenta, así que la topología, las reglas de seguridad y los archivos de Compose no cambian.
- La configuración de cada EC2 (instalación de Docker, Compose y carga de parámetros de SSM) se hace con `user_data` versionado, sin pasos manuales.
- El **estado de Terraform** se guarda en un bucket S3 de la cuenta que contiene el backend, con bloqueo nativo de S3, cifrado y versionado. El estado nunca se versiona en git.
- El procedimiento para mudar la plataforma tiene cuatro pasos y se documenta junto al código: `apply`, restaurar el volcado externo, cargar los parámetros y cambiar el DNS.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| CloudFormation | Funciona por cuenta. Desplegar en dos cuentas requiere StackSets u orquestación manual, y la portabilidad es más torpe. |
| Scripts de AWS CLI | No son idempotentes ni detectan desviaciones. |
| Configuración manual en la consola | No es reproducible e incumple el requisito del equipo. |
| AWS CDK | Válido, pero agrega otro lenguaje y otra cadena de herramientas al proyecto. |

## Consecuencias

- **Positivas:**
  - Mudar la plataforma o recrearla tras un incidente es un procedimiento probado.
  - Los cambios de infraestructura se revisan en pull requests como el código.
- **Negativas:**
  - El User Pool de Cognito se recrea vacío al cambiar de cuenta: los usuarios deben registrarse de nuevo y sus `sub` cambian. Se mitiga manteniendo Cognito en la cuenta con más vida o con un script de exportación e importación.
  - La IP elástica de salida cambia al mudarse.
  - Falta decidir en qué repositorio vive el código de infraestructura. La propuesta es `hindama-backend/infra/`.
