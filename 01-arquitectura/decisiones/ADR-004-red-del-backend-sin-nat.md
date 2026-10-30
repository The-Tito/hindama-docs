# ADR-004: Backend en subred pública con security group cerrado e IP elástica, sin NAT

- **Estado:** aceptada (revisada el 2026-10-30 tras [ADR-010](ADR-010-una-sola-cuenta-aws.md): una sola VPC, sin peering)
- **Fecha:** 2026-10-30
- **Relacionado con:** RNF-07, RF-11, RF-50

## Contexto

FastAPI no debe aceptar tráfico público (RNF-07). Pero el motor de pruebas, y FastAPI en la verificación de propiedad, necesitan salir a Internet para llegar a las APIs de los analistas. Lo habitual sería poner la EC2 en una subred privada con salida por NAT, pero un NAT Gateway cuesta unos 33 USD al mes y una instancia NAT agrega otra EC2.

## Decisión

- La EC2 del backend vive en una **subred pública** con una **IP elástica**.
- Su **security group no tiene ninguna regla de entrada desde Internet**. Solo permite TCP 8443 desde el **security group del frontend** (referencia entre security groups, no un rango de IP).
- La salida queda abierta, porque las APIs de los analistas pueden usar cualquier puerto.
- RDS queda en subredes privadas sin ruta a Internet.
- **Defensa en profundidad** en la EC2 del backend:
  - IMDSv2 obligatorio con `http_put_response_hop_limit = 1`, para que los contenedores no alcancen los metadatos de la instancia.
  - La guardia SSRF de la aplicación ([ADR-008](ADR-008-guardia-ssrf-con-ip-fijada.md)) bloquea los destinos privados, incluido el rango de la VPC, y las IP elásticas propias de Hindama.
  - El rol IAM de la instancia solo puede leer los parámetros `/hindama/backend/*` y escribir en sus grupos de CloudWatch Logs.
- La IP elástica es la **IP de salida fija** de Hindama. La interfaz y la página «Acerca del tráfico» la muestran para que los analistas puedan agregarla a su lista de permitidos.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Subred privada + NAT Gateway | Unos 33 USD al mes más el tráfico: sería el componente más caro. |
| Subred privada + instancia NAT (fck-nat) | Otra EC2 que mantener y otra IP pública. Complica la administración sin cambiar la exposición real, que ya depende del security group. |
| Subred pública sin IP elástica | La IP de salida cambiaría en cada reinicio y los analistas no podrían permitirla. |

## Consecuencias

- **Positivas:** no hay costo de NAT, y la IP de salida es fija y comunicable.
- **Negativas:**
  - La instancia tiene IP pública. Su aislamiento depende por completo del security group, así que una regla mal configurada la expondría. Se mitiga con la lista de verificación del procedimiento de despliegue ([ADR-011](ADR-011-despliegue-con-compose-y-procedimiento.md)) y con un escaneo externo (nmap desde fuera) en la CI.
  - Con la salida abierta, la contención de SSRF depende de la guardia de la aplicación y del límite de IMDS, no de la red. Este riesgo residual se documenta en el modelo de amenazas.
  - Las dos IP públicas (frontend y backend) cuestan unos 7.30 USD al mes.
