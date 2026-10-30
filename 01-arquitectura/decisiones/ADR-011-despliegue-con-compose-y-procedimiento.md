# ADR-011: Despliegue con Docker Compose y procedimiento escrito; Terraform diferido

- **Estado:** aceptada
- **Fecha:** 2026-10-30
- **Sustituye a:** [ADR-009](ADR-009-infraestructura-como-codigo-terraform.md)
- **Relacionado con:** RNF-20, RNF-23, sección 11 de requerimientos (despliegue reproducible)

## Contexto

ADR-009 describía toda la infraestructura en Terraform, con dos proveedores para poder desplegar en una o dos cuentas. Con una sola cuenta ([ADR-010](ADR-010-una-sola-cuenta-aws.md)) y 4 semanas para construir el producto, escribir y probar Terraform compite directamente con el desarrollo.

Aun así, el despliegue debe ser reproducible: si la cuenta principal falla, la plataforma tiene que poder levantarse en la cuenta de respaldo en pocas horas y sin depender de la memoria de nadie.

## Decisión

- La **infraestructura de AWS** (VPC, subredes, security groups, EC2, RDS, Cognito, parámetros de SSM, roles IAM y presupuesto) se crea desde la consola o la CLI siguiendo un **procedimiento escrito paso a paso**: `deploy/PROCEDIMIENTO.md`. Cada paso indica el valor exacto de cada campo.
- La **configuración de cada EC2** (instalar Docker y Compose, cargar los parámetros de SSM y arrancar los contenedores) está en un script `user_data` versionado, sin pasos manuales dentro de la instancia.
- Las **aplicaciones** se despliegan con Docker Compose: un archivo por EC2 (`deploy/frontend/compose.yaml`, `deploy/backend/compose.yaml`) que usa las imágenes publicadas por la CI.
- Todo vive en la carpeta `deploy/` de `hindama-backend`.
- El procedimiento se prueba de punta a punta al menos una vez antes de la entrega, en la cuenta de respaldo, y después se destruye ese despliegue de prueba.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Terraform (ADR-009) | Es lo correcto para un sistema que dura, pero aprenderlo, escribirlo y probarlo cuesta días que hoy van al producto. Queda como mejora: el procedimiento escrito es la especificación a partir de la cual se escribiría. |
| CloudFormation o AWS CDK | El mismo costo de tiempo que Terraform. |
| Configuración manual sin documentar | No es reproducible y deja la recuperación en la memoria de una persona. |

## Consecuencias

- **Positivas:**
  - Cero tiempo en herramientas de infraestructura nuevas.
  - El procedimiento sirve además como documentación para la entrega.
- **Negativas:**
  - Los pasos manuales pueden desviarse del procedimiento. Se mitiga con una lista de verificación al final del documento (puertos, IMDSv2, cifrado, presupuesto) y con el escaneo externo de la CI.
  - Recrear la infraestructura toma horas, no minutos.
