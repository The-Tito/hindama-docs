# ADR-017: Identificadores técnicos en inglés; documentos y textos para el usuario en español

- **Estado:** aceptada
- **Fecha:** 2026-10-30
- **Relacionado con:** RNF-13, sección 11 de requerimientos (internacionalización), [ADR-016](ADR-016-contrato-primero-con-verificacion-automatica.md), [glosario de identificadores](../../03-api/glosario-identificadores.md)
- **Sustituye en parte a:** la convención C2 de la versión 0.1 de las convenciones de la API (rutas y campos en español).

## Contexto

La primera versión del contrato y del modelo de datos usaba identificadores en español (`/proyectos`, `estado_verificacion`, tabla `proyecto`), igual que los documentos. Al empezar el código, el equipo prefirió que todo lo técnico esté en inglés: es el idioma de FastAPI, SQLAlchemy, Next.js y sus bibliotecas, y de los ejemplos y la documentación que consulta el equipo.

Si solo el código estuviera en inglés, cada campo tendría que traducirse entre capas (alias en Pydantic y nombres de columna en SQLAlchemy). Cada traducción es un lugar donde puede aparecer un error.

## Decisión

- **En inglés:**
  - Rutas, parámetros y campos JSON de la API.
  - `operationId` y nombres de esquemas.
  - Valores de catálogo y códigos de error y de advertencia.
  - Tablas, columnas, roles y funciones de la base de datos.
  - Carpetas, archivos, clases, funciones, variables, comentarios y docstrings del código, en backend y frontend.
- **En español:**
  - Los documentos de `hindama-docs`, incluidas las descripciones del contrato.
  - Los textos que ve el usuario, incluidos los mensajes de respaldo `detail` y `message` de la API.
- **Un solo glosario** (`03-api/glosario-identificadores.md`) fija la traducción de cada término del dominio. Un término nuevo se agrega ahí en el mismo pull request que lo usa por primera vez.
- **Excepciones:** el archivo `/.well-known/hindama-verificacion.txt` y el registro `_hindama-verificacion.<host>` conservan su nombre, porque no son identificadores internos: son lo que el analista publica en su propio dominio, y RF-18 los define así.
- Las tablas van en plural (`users`, `projects`): `user` es palabra reservada en PostgreSQL.
- El motor de pruebas es el paquete `scanner`, y su rol de base de datos `hindama_scanner`, para no confundirlo con el *engine* de SQLAlchemy.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Todo en español (C2 original) | Mezcla español con las convenciones y bibliotecas en inglés, y el equipo prefiere leer y escribir código en inglés. |
| Solo el código en inglés; contrato y base de datos en español | Obliga a traducir cada campo entre capas con alias: más código y más lugares para errores. |
| También los documentos en inglés | Los documentos se entregan a la escuela y el producto es en español. |

## Consecuencias

- **Positivas:**
  - Un mismo nombre recorre la base de datos, el modelo de SQLAlchemy, el esquema de Pydantic, el JSON y el tipo de TypeScript, sin traducciones.
  - El código sigue las convenciones habituales de cada biblioteca.
- **Negativas:**
  - Los documentos mezclan el término en español con el identificador en inglés; el glosario es la referencia para pasar de uno a otro.
  - El contrato pasa a la versión 0.2.0, que no es compatible con la 0.1.0. Como todavía no hay código que lo use, el cambio no rompe nada.
