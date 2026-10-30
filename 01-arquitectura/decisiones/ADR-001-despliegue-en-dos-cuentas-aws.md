# ADR-001: Despliegue repartido en dos cuentas de AWS con VPC peering

- **Estado:** sustituida por [ADR-010](ADR-010-una-sola-cuenta-aws.md) el 2026-10-30. Con la entrega a finales de noviembre, una sola cuenta alcanza y la división dejó de justificarse.
- **Fecha:** 2026-10-30
- **Relacionado con:** RNF-07, RNF-08, RNF-16, sección 6 de requerimientos

## Contexto

Hindama se despliega completo en AWS. El equipo tiene dos cuentas personales creadas en octubre de 2026, ambas en el plan gratuito basado en créditos: 100 USD al registrarse y hasta 100 USD más por actividades, durante 6 meses. No hay presupuesto adicional. Una sola cuenta no alcanza para todo el sistema durante 6 meses sin agotar sus créditos.

La API de la plataforma (FastAPI) no debe ser pública: solo Next.js puede llamarla.

## Decisión

- La plataforma se reparte en dos cuentas:
  - **Cuenta A (frontend):** EC2 con Next.js y el User Pool de Cognito.
  - **Cuenta B (backend):** EC2 con FastAPI, el worker RQ y Redis, más la base de datos en RDS.
- Las dos VPC se conectan con **VPC peering entre cuentas**, con estas condiciones:
  - Misma región en ambas cuentas: `us-east-1`.
  - Rangos CIDR sin traslape: `10.10.0.0/16` (A) y `10.20.0.0/16` (B).
  - Las subredes de las EC2 están en la misma zona por **ID** (`use1-az1`), no por nombre, porque los nombres de zona se asignan distinto en cada cuenta. Así se evita el cargo por tráfico entre zonas.
  - Las tablas de rutas solo incluyen el CIDR de la otra VPC.
- El reparto coincide con los responsables de cada repositorio: frontend y backend.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Todo en una cuenta | La cuenta del backend apenas alcanza; con el frontend se agotarían los créditos antes de los 6 meses. Se conserva como modo de respaldo (ADR-009). |
| Cuenta A con la plataforma y cuenta B solo con el motor aislado | Aísla mejor el componente expuesto a tráfico no confiable, pero el worker necesitaría llegar por peering a RDS y Redis de la otra cuenta. Eso abre más superficie y Redis no está diseñado para exponerse en red. |
| Producción en una cuenta y staging en la otra | No resuelve el problema de créditos de producción. |
| Conectar las cuentas por Internet (FastAPI pública con allowlist de IP) | Contradice RNF-07: la API no acepta tráfico público. |
| Transit Gateway o PrivateLink | Tienen cargo por hora (unos 36 USD al mes o más); el peering es gratuito. |

## Consecuencias

- **Positivas:**
  - El costo se reparte y cada cuenta cabe en sus créditos.
  - Hay una frontera de cuenta real entre el borde (Next.js) y los datos: comprometer la cuenta A no da acceso a RDS ni a las credenciales cifradas.
- **Negativas:**
  - Hay que operar dos cuentas: dos consolas, dos facturaciones y dos juegos de alarmas de presupuesto.
  - El peering entre cuentas requiere aceptar la conexión desde la cuenta B. Terraform lo automatiza con dos proveedores (ADR-009).
  - Si una cuenta se cierra, la plataforma cae hasta que se vuelva a desplegar en la otra (modo `unico`).
