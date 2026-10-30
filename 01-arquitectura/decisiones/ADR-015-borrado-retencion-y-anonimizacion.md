# ADR-015: Borrado, retención y anonimización de datos

- **Estado:** aceptada
- **Fecha:** 2026-10-30
- **Relacionado con:** RF-14, RF-78, RF-79, RF-81 a RF-84, RF-88 a RF-90, RN-03, RN-13, RNF-17, sección 11 de requerimientos, sección 5.4 de la arquitectura, [modelo de datos](../../02-datos/modelo.md) sección 7

## Contexto

Varias exigencias chocan entre sí:

- RF-14 borra de forma permanente un proyecto y todo su contenido, y la sección 11 exige borrar los datos de un proyecto o de una cuenta en máximo 30 días, incluidos los respaldos.
- El equipo quiere que la baja de una cuenta **no haga perder las métricas** del panel de administración (RF-78).
- La bitácora es inalterable (RF-83) y sirve para investigar reportes de abuso (arquitectura 5.4): «qué proyecto, qué analista, cuándo». Si el proyecto se borra, se pierde el host que se probó. Pero mostrar el host al administrador contradice RN-03 y RF-79.
- La Ley Federal de Protección de Datos Personales en Posesión de los Particulares, vigente desde el 21 de marzo de 2025, reconoce los derechos de acceso, rectificación, cancelación y oposición (ARCO). La cancelación alcanza los archivos, registros y sistemas donde estén los datos, y exige **bloquear** los datos (conservarlos de forma segura e inaccesibles para su uso) antes de **suprimirlos** al vencer su plazo de conservación.
- Los datos anonimizados de forma irreversible dejan de ser datos personales.

## Decisión

### Métricas anónimas desde el diseño

- Las métricas del panel viven en tablas **sin vínculo con personas ni proyectos**:
  - `metrica_hallazgo`: un hecho por hallazgo, con la semana de detección, módulo, OWASP, CWE, severidad, días para resolver y regresiones.
  - `metrica_diaria`: contadores por día (usuarios nuevos, cuentas eliminadas, proyectos creados, ejecuciones lanzadas).
- Se escriben **cuando ocurre el hecho**, no al dar de baja. La única liga es `hallazgo.metrica_id`, del hallazgo a la métrica: al borrarse el hallazgo, la métrica queda sin ningún vínculo.
- Se usa la semana, no la fecha exacta, para dificultar cruzar una métrica con la bitácora.

### Borrado

- **Proyecto:** borrado físico en cascada (RF-14).
- **Cuenta:** borrado físico del usuario y, en cascada, de sus proyectos; después, borrado en Cognito con `DeleteUser` usando el access token del propio usuario. No hay proceso de anonimización: las métricas ya son anónimas.
- **Identidad:** borrado lógico. La credencial se borra de inmediato y la fila se conserva porque los hallazgos la referencian.
- **Respaldos:** caducan a los 7 días (RNF-17). Esa ventana es el **bloqueo** de los datos borrados: están cifrados, fuera del uso normal, y se suprimen al rotar.

### Bitácora

- Sin llaves foráneas: `usuario_id` y `proyecto_id` son UUID opacos que sobreviven al borrado.
- Guarda el **HMAC-SHA256 del host** (con una llave en SSM y su versión), no el host. Ante un reporte de abuso sobre un host, se calcula su HMAC y se busca. El administrador nunca ve hosts en claro.
- Nunca guarda credenciales, justificaciones ni texto libre del analista.
- **Inmutable:** los roles de la aplicación solo tienen `INSERT` y `SELECT`, y un trigger rechaza `UPDATE`, `TRUNCATE` y el `DELETE` de filas con menos de 6 meses.
- **Retención de 6 meses:** la función `purgar_bitacora()` borra lo más antiguo. Durante ese plazo, los registros de una cuenta eliminada quedan bloqueados para su único uso legítimo: investigar incidentes y abusos.

### Datos mínimos

La base de datos no guarda nombre ni correo del usuario; viven en Cognito.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Anonimizar al dar de baja: conservar los proyectos y borrar el `propietario_id` | No anonimiza: una URL base, un contrato o una evidencia identifican al dueño y pueden contener datos de terceros. Además es un proceso que puede fallar a medias. |
| Calcular las métricas en vivo sobre los datos existentes | Las métricas cambiarían con cada borrado de proyecto o de cuenta. |
| Bitácora con el host en claro | El administrador vería contenido de proyectos (RN-03, RF-79). |
| Bitácora sin datos del host | No permitiría investigar un abuso después de que se borre el proyecto. |
| Bitácora sin plazo de retención | Conserva datos personales (IP, usuario) sin límite; contradice la supresión que exige la ley. |
| Desactivar la cuenta en lugar de borrarla | No cumple la cancelación. |

## Consecuencias

- **Positivas:**
  - La baja es un borrado simple y atómico; las métricas no cambian.
  - Se puede investigar un abuso sin dar al administrador acceso al contenido.
  - Los plazos quedan dentro de los 30 días de la sección 11: inmediato en la base de datos, 7 días en respaldos, 6 meses en la bitácora (que tiene su propio fundamento).
- **Negativas:**
  - Un reporte de abuso solo se puede investigar dentro de los 6 meses de retención.
  - La llave del HMAC es otro secreto. Si se pierde, los HMAC anteriores no se pueden buscar; el campo `hmac_version` permite rotarla.
  - Con pocos usuarios, cruzar `metrica_hallazgo` con la bitácora durante su retención podría sugerir a qué analista pertenece una métrica. El riesgo es bajo porque la métrica no contiene nada del proyecto, y desaparece al purgarse la bitácora.
  - El fundamento legal de la retención y los plazos deben declararse en el aviso de privacidad. Este ADR no es una opinión legal; se confirma con el profesor antes de la entrega.
  - Se agregaron RF-88 a RF-90, RN-13 y CU-25, y se ajustaron RF-81, RF-83 y la sección 11 de requerimientos.
