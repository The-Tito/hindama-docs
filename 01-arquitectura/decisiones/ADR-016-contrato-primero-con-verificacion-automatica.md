# ADR-016: Contrato de la API escrito primero y verificado automáticamente contra la implementación

- **Estado:** aceptada
- **Fecha:** 2026-10-30
- **Relacionado con:** RNF-07, RNF-08, RNF-22, [convenciones de la API](../../03-api/convenciones.md), [contrato](../../03-api/openapi.yaml)

## Contexto

El frontend y el backend los construyen personas distintas en paralelo, durante 4 semanas. El frontend necesita saber qué devuelve cada endpoint antes de que exista, y debe depender solo del contrato, nunca del esquema de la base de datos.

FastAPI genera su propio OpenAPI a partir del código (RNF-22). Si además se escribe un contrato a mano, hay dos descripciones de la misma API y pueden desfasarse sin que nadie lo note: el frontend construiría contra una versión y el backend implementaría otra.

## Decisión

- **`hindama-docs/03-api/openapi.yaml` es la fuente de verdad.** Se escribe a mano, antes de implementar. Ningún endpoint cambia sin un pull request que cambie primero el contrato.
- **La implementación se verifica en la CI del backend**, no por disciplina:
  1. **`oasdiff`** compara el OpenAPI que genera FastAPI (`app.openapi()`) con `openapi.yaml` y falla ante cualquier diferencia estructural en rutas, métodos, parámetros, códigos de estado o forma de los esquemas. Los nombres de los componentes no importan, porque compara la estructura ya resuelta.
  2. **Schemathesis** genera peticiones a partir del contrato contra la aplicación levantada en la CI y comprueba que cada respuesta cumpla su esquema.
- **Respuestas cerradas:** todos los esquemas de respuesta tienen `additionalProperties: false`. Un campo que sobra es una falla, lo que convierte a Schemathesis en un control de RN-11: detecta si un endpoint devuelve un campo que no debe.
- **Sin `allOf` en los esquemas**, para que `additionalProperties: false` funcione y para que la estructura coincida con la que genera Pydantic.
- **Ejemplos realistas** en el contrato, para que el frontend trabaje contra Prism y genere sus tipos con `openapi-typescript`.
- El backend ajusta lo que genera FastAPI para que coincida con el contrato: formato de errores (Problem Details en lugar del 422 por defecto), esquema de seguridad y `operationId`. Es trabajo de una sola vez, al montar el proyecto.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Endpoints esqueleto en FastAPI que generen el contrato | No puede desfasarse, pero la fuente de verdad se muda al repositorio del backend, contra lo acordado. El frontend no podría proponer cambios sin escribir Python, y el contrato no existiría hasta montar el backend. |
| Contrato a mano y modelos de Pydantic generados desde él (`datamodel-code-generator`) | El código generado se reescribe en cada regeneración: no admite validadores propios sin trucos, y agrega otra herramienta a la cadena. |
| Contrato a mano sin verificación automática | Es justo el riesgo de desfase que se quiere evitar. |

## Consecuencias

- **Positivas:**
  - El frontend tiene el contrato, sus tipos y un simulador desde el primer día.
  - Un desfase rompe la CI en lugar de llegar a producción.
  - La revisión de un cambio de API ocurre en un archivo pequeño y legible, antes del código.
- **Negativas:**
  - La verificación solo protege si la CI del backend existe y su resultado bloquea la integración. Se activa al montar el backend.
  - Un cambio de API toca dos repositorios (docs y backend) y a veces tres.
  - Hay que confirmar que `oasdiff` y Schemathesis soportan bien OpenAPI 3.1 (FastAPI genera 3.1). Si alguno falla, se compara normalizando a 3.0 o se usa la opción de soporte experimental de Schemathesis.
  - Tras este ADR, las rutas de la arquitectura y de ADR-006 se ajustaron a las convenciones (rutas anidadas bajo el proyecto e identificadores UUID).
