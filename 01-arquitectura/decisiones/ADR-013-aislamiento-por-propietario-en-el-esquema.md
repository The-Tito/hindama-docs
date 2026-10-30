# ADR-013: Aislamiento por propietario en el esquema: UUID, llaves foráneas compuestas y Row-Level Security

- **Estado:** aceptada
- **Fecha:** 2026-10-30
- **Relacionado con:** RN-02, RN-03, RNF-05, RNF-08, RF-80, [modelo de datos](../../02-datos/modelo.md) secciones 1 y 5

## Contexto

Hindama es una herramienta de seguridad y debe superar sus propias pruebas: el módulo de Acceso a objetos (API1) que ofrece a los analistas es exactamente la falla que la plataforma no puede tener. La arquitectura confía el aislamiento a la capa de repositorio de FastAPI (toda consulta filtra por propietario). Eso funciona mientras ningún endpoint olvide el filtro; un solo olvido expone proyectos ajenos.

Hay tres riesgos distintos:

1. **Lectura ajena:** una consulta sin filtro devuelve filas de otro analista.
2. **Referencia cruzada:** una fila de mi proyecto apunta a una fila de otro (un recurso a una identidad ajena, un hallazgo a una operación ajena). Así, al leer mi proyecto, se filtrarían datos de otro.
3. **Enumeración:** identificadores secuenciales (`/projects/42`) revelan cuántos proyectos y ejecuciones hay y facilitan probar identificadores.

## Decisión

- **Identificadores:** UUID v7 generados en la aplicación como llave primaria y en las URLs. Las ejecuciones llevan además un `number` consecutivo por proyecto, solo para mostrar.
- **Llaves foráneas compuestas:** toda tabla del proyecto lleva `project_id` y `UNIQUE (project_id, id)`; sus referencias internas son `(project_id, x_id) → x(project_id, id)`. La base de datos rechaza cualquier referencia entre proyectos distintos.
- **Row-Level Security** en todas las tablas del proyecto y en `users` y `audit_log`:
  - FastAPI fija `app.cognito_sub`, `app.user_id` y `app.role` con `set_config(…, true)` al abrir la transacción de cada petición. Su alcance es la transacción, así que no se arrastran entre peticiones del pool.
  - `projects` se filtra por `owner_id`, y las tablas hijas con `EXISTS` sobre `projects`. `USING` y `WITH CHECK` son iguales, así que tampoco se puede escribir en un proyecto ajeno.
  - Sin variables, las políticas no devuelven nada (falla cerrada).
  - `hindama_scanner` tiene políticas permisivas: atiende ejecuciones de todos los analistas y no recibe entradas del usuario para elegir proyecto.
  - El administrador no es propietario de ningún proyecto, así que RLS también le niega el contenido (RN-03), además del 403 de FastAPI.
- **El filtro en el repositorio se mantiene** como capa principal, con pruebas automatizadas de acceso cruzado por endpoint. RLS y las FK son defensa en profundidad.

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Solo el filtro en el repositorio | Un olvido en un endpoint expone datos ajenos, y nada impide referencias cruzadas al escribir. |
| Filtro en el repositorio + FK compuestas, sin RLS | Cierra las referencias cruzadas, pero no la lectura sin filtro. Fue la recomendación inicial por simplicidad; el equipo eligió RLS por ser un proyecto de seguridad. |
| RLS sin FK compuestas | PostgreSQL revisa las FK **sin aplicar RLS**: una fila propia podría seguir apuntando a una fila ajena. Las dos capas se necesitan. |
| `owner_id` copiado en cada tabla hija | Simplifica las políticas, pero duplica el dato y obliga a mantenerlo consistente. El `EXISTS` sobre `projects` basta a esta escala. |
| `bigserial` en las URLs | Revela volúmenes y facilita enumerar. |

## Consecuencias

- **Positivas:**
  - Un endpoint con un filtro olvidado devuelve vacío o 404, no datos ajenos.
  - RN-03 queda garantizado también en la base de datos.
  - El aislamiento se puede demostrar con pruebas directas en SQL, además de las pruebas de la API.
- **Negativas:**
  - Cada transacción de FastAPI debe fijar las variables. Se centraliza en la dependencia de sesión de base de datos y se prueba.
  - Las políticas agregan un `EXISTS` a cada consulta de tablas hijas; hay que indexar `projects(owner_id)` y `project_id` en cada tabla.
  - Depurar con `psql` exige fijar las variables o usar el usuario dueño del esquema.
  - El respaldo (`pg_dump`) necesita un usuario que no quede limitado por RLS.
  - Las violaciones de unicidad podrían revelar que una fila existe en otro proyecto. Con UUID el riesgo es despreciable, y las restricciones únicas siempre incluyen `project_id`.
  - La prueba técnica de la semana 1 debe confirmar que `set_config(…, true)` se comporta como se espera con SQLAlchemy asíncrono y asyncpg.
