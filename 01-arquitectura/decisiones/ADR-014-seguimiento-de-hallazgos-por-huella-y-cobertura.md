# ADR-014: Seguimiento de hallazgos por huella y cobertura

- **Estado:** aceptada
- **Fecha:** 2026-10-30
- **Relacionado con:** F-11, RF-44, RF-52, RF-64, RF-68 a RF-73, RN-10, RNF-19, [modelo de datos](../../02-datos/modelo.md) secciones 3.3, 3.4, 4.3 y 6

## Contexto

F-11 pide seguir cada hallazgo entre ejecuciones (nuevo, persistente, resuelto, regresión, riesgo aceptado), conservar su historial y concluir el proyecto cuando no queden abiertos. RF-68 identifica un mismo hallazgo por una huella (operación, identidad, módulo y tipo de falla) y la versión 1.0 del documento decía «comparar con la ejecución anterior».

Comparar contra la ejecución anterior da resultados falsos, porque las ejecuciones no son homogéneas:

- Pueden correr módulos distintos (RF-44). Si la ejecución 3 solo corre Autenticación, todos los hallazgos de Acceso a objetos de la ejecución 2 parecerían resueltos.
- Pueden cancelarse o fallar a la mitad (RF-52, RNF-18).
- Pueden saltarse una identidad cuya credencial venció (RF-33).
- El contrato cambia entre versiones (RF-26) y una operación puede desaparecer.

Además, la aceptación de riesgo y su justificación deben persistir entre ejecuciones, y RF-78 necesita el tiempo de detección a resolución.

## Decisión

- **Tres entidades:**
  - `hallazgo`: la falla lógica, única por `(proyecto, módulo, tipo_falla, operación, identidad)`, con su estado actual.
  - `ocurrencia`: cada detección en una ejecución, con su evidencia enmascarada.
  - `evento_hallazgo`: cada cambio de estado, con su causa (ejecución o analista) y justificación. Solo se inserta.
- **La huella usa identificadores estables:**
  - La operación es una fila a nivel proyecto identificada por `(método, ruta normalizada)`. No es la fila de una versión del contrato, así que la huella sobrevive a una nueva importación.
  - La identidad se borra de forma lógica, así que su `id` sigue siendo válido.
- **Cobertura:** `resultado` guarda una fila por cada celda `(ejecución, módulo, operación, identidad)` evaluada por completo, con veredicto `ok`, `falla`, `omitido` o `error`. Es también la matriz de RF-64.
- **Regla de resolución:** un hallazgo abierto pasa a `resuelto` solo si la ejecución tiene un `resultado` con veredicto `ok` o `falla` para su misma `(módulo, operación, identidad)` y no volvió a detectarlo. Lo que no se evaluó conserva su estado. La regla vale también para ejecuciones canceladas o fallidas, en lo que alcanzaron a evaluar.
- **Riesgo aceptado** es un solo estado con `motivo_descarte` (`riesgo_aceptado` o `falso_positivo`). Si se vuelve a detectar, sigue aceptado; al revertir vuelve a `persistente`.
- **Cierre administrativo:** si la identidad se elimina o la operación se retira del contrato, sus hallazgos abiertos pasan a `resuelto` con un `motivo_resolucion` que lo distingue de una corrección real.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Una fila de hallazgo por ejecución, con el estado copiado | El estado y la aceptación de riesgo se repiten en muchas filas y hay que arrastrarlos en cada ejecución; el historial se reconstruye con consultas frágiles. |
| Hallazgo lógico con el historial en un campo JSON | Difícil de consultar, de validar y de usar para RF-78. |
| Comparar contra la ejecución anterior (RF-68 v1.0) | Resuelve hallazgos que no se volvieron a probar (ver Contexto). |
| Guardar cada petición enviada para saber qué se probó | Hasta 5,000 filas por ejecución, casi nunca consultadas. La celda basta. |
| Un sexto estado «obsoleto» para identidades u operaciones eliminadas | Cambia RF-69 y agrega un estado que la interfaz y los reportes deben explicar. El motivo de resolución da la misma información. |

## Consecuencias

- **Positivas:**
  - Los estados reflejan lo que realmente se probó: ejecutar un solo módulo nunca resuelve hallazgos de otro.
  - El historial (RF-72), la aceptación de riesgo (RF-70) y el tiempo de resolución (RF-78) salen directamente de los eventos.
  - La matriz y la cobertura son la misma tabla.
- **Negativas:**
  - El motor debe escribir cada celda solo al terminar de evaluarla; una escritura prematura resolvería hallazgos sin evidencia. Se cubre con pruebas del motor.
  - La huella depende de que los códigos `tipo_falla` de cada módulo sean estables. Cambiar un código hace que el hallazgo aparezca como nuevo.
  - Un hallazgo puede quedar abierto indefinidamente si su comprobación ya no se ejecuta (por ejemplo, el analista deja de correr ese módulo). Es correcto: no hay evidencia de que se corrigió. La interfaz muestra la fecha de la última evaluación.
  - Se ajustaron RF-68, RF-69, RF-70 y RF-73 y el CU-16 de los documentos de producto.
