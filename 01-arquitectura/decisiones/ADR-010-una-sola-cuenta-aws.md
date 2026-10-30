# ADR-010: Una sola cuenta de AWS; la segunda queda como respaldo

- **Estado:** aceptada
- **Fecha:** 2026-10-30
- **Sustituye a:** [ADR-001](ADR-001-despliegue-en-dos-cuentas-aws.md)
- **Relacionado con:** RNF-07, RNF-16, sección 6 de requerimientos

## Contexto

ADR-001 repartió la plataforma en dos cuentas de AWS unidas por VPC peering, porque una sola cuenta del plan gratuito no alcanzaba para 6 meses de operación.

La entrega del proyecto es a finales de noviembre de 2026. La plataforma solo necesita vivir en AWS unas 4–8 semanas: del despliegue a la entrega y la evaluación. Con un costo estimado de unos 44 USD al mes, una sola cuenta lo cubre con los 100 USD iniciales, más hasta 100 USD por actividades.

La división en dos cuentas trae complejidad que ya no se justifica: peering con rutas en ambos lados, una CA interna entre cuentas, Terraform con dos proveedores, acceso de un integrante a la cuenta personal del otro, el doble de operación y dos puntos de falla. Con 4 semanas de desarrollo, ese tiempo debe ir al producto.

## Decisión

- Toda la plataforma vive en **una cuenta de AWS**, en `us-east-1`, con una sola VPC (`10.10.0.0/16`):
  - EC2 frontend (Next.js) y EC2 backend (FastAPI, motor, Redis) en una subred pública.
  - RDS en subredes privadas.
  - El User Pool de Cognito.
- El aislamiento entre el borde y el núcleo se conserva dentro de la cuenta:
  - EC2 separadas para el frontend y el backend.
  - El security group del backend solo acepta al security group del frontend en el puerto 8443.
  - Cada EC2 solo lee sus propios parámetros de SSM.
- La **segunda cuenta** del equipo queda como **respaldo**: si la principal se suspende o agota sus créditos, la plataforma se despliega ahí con el procedimiento de [ADR-011](ADR-011-despliegue-con-compose-y-procedimiento.md).
- Cada integrante tiene su propio usuario IAM con MFA en la cuenta principal. Nadie usa el usuario raíz para operar.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Dos cuentas con VPC peering (ADR-001) | Resolvía la duración de los créditos, que ya no es un problema. Agrega días de configuración y dos puntos de falla. |
| Producción en una cuenta y staging en la otra | Con 4 semanas no hay tiempo de mantener dos entornos en la nube. Las pruebas se hacen en el entorno local con Docker Compose. |
| Todo en una sola EC2 | Más barato, pero mezcla el borde expuesto a Internet con el núcleo y los secretos del backend. Dos EC2 cuestan unos 6 USD al mes más y mantienen la separación. |

## Consecuencias

- **Positivas:**
  - Sin peering, sin CA entre cuentas y sin acceso cruzado a cuentas personales.
  - Un solo presupuesto, una sola consola y un solo juego de alarmas.
  - Las reglas de red se expresan con referencias entre security groups, más simples y precisas que los rangos de IP.
- **Negativas:**
  - Se pierde la frontera de cuenta entre el borde y los datos: un compromiso de la cuenta da acceso a todo. Se mitiga con roles IAM mínimos por EC2, MFA y sin llaves de acceso de larga duración.
  - Si la cuenta se pierde, la plataforma cae hasta redesplegarla en la cuenta de respaldo.
  - La división en dos cuentas queda documentada (ADR-001) como evolución posible si el proyecto continúa después de la entrega.
