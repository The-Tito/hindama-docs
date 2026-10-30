---
documento: Convenciones de la API
proyecto: Hindama
version: 0.2
fecha: 2026-10-30
estado: propuesta para revisión
---

# Convenciones de la API de la plataforma

Reglas que cumplen **todos** los endpoints de la API de Hindama (FastAPI). El contrato está en [`openapi.yaml`](openapi.yaml); este documento explica lo que el contrato no puede expresar o lo que se repite en cada endpoint.

La API es **privada**: su único cliente es el servidor de Next.js (BFF), que reenvía las peticiones del navegador ([arquitectura, sección 2](../01-arquitectura/arquitectura.md)). Lo que ocurre entre el navegador y Next.js (cookie de sesión, token anti-CSRF, rutas `/api/...` del BFF) no forma parte de este contrato.

## 1. El contrato es la fuente de verdad

- `openapi.yaml` se escribe a mano en este repositorio. El backend lo implementa y el frontend lo consume. **Ningún endpoint cambia sin cambiar primero el contrato** ([ADR-016](../01-arquitectura/decisiones/ADR-016-contrato-primero-con-verificacion-automatica.md)).
- La CI del backend comprueba que la implementación cumple el contrato:
  1. `oasdiff` compara el OpenAPI que genera FastAPI con `openapi.yaml` y falla ante cualquier diferencia estructural.
  2. Schemathesis genera peticiones contra la aplicación y valida que cada respuesta cumpla su esquema.
- El frontend genera sus tipos de TypeScript con `openapi-typescript` y puede trabajar contra un servidor simulado antes de que exista el endpoint real:
  - `npx @stoplight/prism-cli mock openapi.yaml` levanta el simulador en `http://localhost:4010` y responde con los ejemplos del contrato.
  - La cabecera `Prefer` elige qué devolver: `Prefer: example=newHttpProject` (un ejemplo por nombre) o `Prefer: code=422` (un código de estado).
  - El simulador también rechaza peticiones que no cumplen el contrato (por ejemplo, sin `Authorization` o con un campo inválido).
- **Las respuestas son cerradas** (`additionalProperties: false`): un campo que no está en el contrato es un error de la implementación. Así Schemathesis detecta si el backend filtra un campo que no debe, como una credencial cifrada.
- **Cómo se cambia el contrato:** pull request a `hindama-docs` que modifica `openapi.yaml`, con `info.version` actualizado y revisado por ambos integrantes. Después, el pull request del backend que lo implementa y el del frontend que lo usa.

## 2. Versionado

- Sin versión en la URL. La API tiene un solo cliente, que se despliega junto con ella.
- `info.version` sigue semver: el MAJOR sube con un cambio que rompe al cliente (quitar un campo o un endpoint, cambiar un tipo), el MINOR con un agregado compatible y el PATCH con correcciones de documentación.
- Agregar un campo a una respuesta o un parámetro opcional es compatible. El frontend debe **ignorar los campos que no conoce**.

## 3. Autenticación y cabeceras

| Cabecera | Dirección | Uso |
| --- | --- | --- |
| `Authorization: Bearer <access_token>` | Next.js → API | Access token de Cognito. Obligatorio en todo endpoint, salvo `GET /salud`. FastAPI valida firma, `iss`, `client_id`, `token_use = access` y `exp` (RF-07). |
| `X-Hindama-Client-IP` | Next.js → API | IP real del navegador, para la bitácora (RF-82). FastAPI solo la acepta si la petición viene de la IP privada del frontend; si no, la ignora. Nunca se usa para autorizar. |
| `X-Request-Id` | Ambas | Identificador de la petición. Si Next.js lo envía, la API lo conserva; si no, lo genera. Siempre vuelve en la respuesta y en los errores (`request_id`), y aparece en los registros. |
| `Retry-After` | API → Next.js | En las respuestas 429. |

- **Rol:** sale del claim `cognito:groups` (RN-04). Los endpoints de proyectos responden **403** al administrador (RF-80); los de `/admin/*`, 403 al analista.
- **Sin la sesión, el resto no existe:** una petición sin token o con un token inválido recibe 401 antes de cualquier otra validación, incluso si la ruta no existe.

## 4. Nombres y rutas

- **Todos los identificadores en inglés** ([ADR-017](../01-arquitectura/decisiones/ADR-017-identificadores-en-ingles.md)): rutas, campos, parámetros, valores de catálogo, códigos de error y `operationId`. La traducción de cada término del dominio está en el [glosario de identificadores](glosario-identificadores.md). Las descripciones del contrato y los textos para el usuario siguen en español.
- Campos JSON y parámetros en `snake_case`: `verification_status`, `page_size`. Valores de catálogo en `snake_case` y minúsculas: `pending`, `object_access`, `critical`.
- Colecciones en plural. Todo lo que pertenece a un proyecto cuelga de él, con **dos niveles como máximo**: `/projects/{project_id}/contracts/{contract_id}`. Así la propiedad queda explícita en la ruta y la API comprueba que el hijo pertenece al proyecto.
- Acciones que no son CRUD: `POST` sobre un sustantivo que describe el resultado: `POST /projects/{id}/verification`, `POST /me/terms`. Si no hay un sustantivo natural, se usa un verbo: `POST …/runs/{id}/cancel`.
- Rutas de varias palabras en `kebab-case`: `/admin/audit-log`.
- Administración bajo `/admin/*`.
- `operationId` en `camelCase`, verbo + recurso: `listProjects`, `createProject`, `verifyOwnership`. El frontend los usa como nombres de función.

## 5. Formatos

| Tipo | Formato |
| --- | --- |
| Identificadores | UUID en texto (`format: uuid`). Son opacos: el cliente no los interpreta ni los genera. |
| Fechas y horas | RFC 3339 en UTC con `Z`: `2026-10-30T18:04:05Z`. |
| Números consecutivos para mostrar | Enteros (`number` de ejecución o de versión de contrato). Solo sirven para mostrar; las rutas usan el UUID. |
| Campos opcionales | **Siempre presentes**, con `null` si no tienen valor. Nunca se omiten. |
| Texto | UTF-8. Los textos que vienen de la API del analista (evidencias, avisos del contrato) son **no confiables**: el frontend los muestra como texto escapado, nunca como HTML. |

## 6. Respuestas

- **Un recurso:** el objeto directamente, sin sobre.
- **Una lista:** siempre paginada, con este sobre:

```json
{
  "items": [ … ],
  "total": 37,
  "page": 1,
  "page_size": 20
}
```

- **Creación:** `201` con el recurso creado y la cabecera `Location`.
- **Eliminación:** `204` sin cuerpo.
- **Trabajo asíncrono** (ejecuciones, desde la semana 2): `202` con el recurso en su estado inicial.

## 7. Paginación, filtros y orden

- Parámetros `page` (desde 1, por defecto 1) y `page_size` (1 a 100, por defecto 20). Una página fuera de rango devuelve `items: []` con el `total` real, no un error.
- **Excepción:** `GET …/operations` acepta `page_size` hasta 500, porque las pantallas de política y de operaciones necesitan la lista completa de un contrato (RNF-02 considera hasta 500 operaciones).
- Los filtros son parámetros de consulta con el nombre del campo: `?status=new&severity=high`. Para varios valores se repite el parámetro: `?severity=critical&severity=high`.
- Cada lista documenta su orden por defecto en el contrato. Donde se puede elegir el orden, se usa `sort=field` o `sort=-field` (descendente).

## 8. Errores

Todos los errores usan **Problem Details** ([RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)) con `Content-Type: application/problem+json`, extendido con `code`, `request_id` y, si hay errores por campo, `errors`:

```json
{
  "type": "urn:hindama:error:url.destination_not_allowed",
  "title": "La URL apunta a un destino no permitido",
  "status": 422,
  "detail": "La URL base resuelve a una dirección privada. Usa una dirección pública de tu API.",
  "code": "url.destination_not_allowed",
  "request_id": "0192e3b1-7c1a-7d40-9f5e-1b2c3d4e5f60",
  "errors": [
    { "field": "base_url", "code": "url.destination_not_allowed", "message": "Resuelve a una dirección privada." }
  ]
}
```

- `type` es `urn:hindama:error:<code>`: un identificador, no una página que se pueda abrir.
- **`code` es el contrato; `title` y `detail` no.** El frontend elige el texto que muestra según `code` (y `errors[].code`), lo que mantiene los textos separados del código para poder agregar inglés (sección 11 de requerimientos). `detail` está en español y sirve de respaldo para códigos que el frontend aún no conoce.
- `errors[].field` usa la ruta del campo en el cuerpo con puntos (`credential.value`) o el nombre del parámetro de consulta. Es `null` para errores que no son de un campo.
- **Nunca** hay trazas, nombres de tablas, SQL, rutas de archivos ni datos de otros usuarios en un error (RNF-07). Un 500 solo trae `code: internal` y `request_id`, que sirve para buscar el detalle en los registros.
- Los errores de validación de FastAPI (422 por defecto) se transforman a este formato; nunca sale el formato `{"detail": [...]}` de FastAPI.

### 8.1 Códigos de estado

| Estado | Cuándo | `code` típico |
| --- | --- | --- |
| 400 | JSON mal formado o tipo de contenido incorrecto | `request.malformed` |
| 401 | Sin token, token vencido o inválido. Incluye `WWW-Authenticate: Bearer`. | `auth.required`, `auth.invalid_token` |
| 403 | El rol no permite la operación, o faltan los términos de uso | `role.forbidden`, `terms.not_accepted` |
| 404 | No existe **o es de otro analista**. Las dos respuestas son idénticas (RN-02, RNF-05). | `resource.not_found` |
| 409 | Conflicto con el estado actual | `project.active_run` |
| 413 | Archivo demasiado grande | `contract.too_large` |
| 422 | Validación de campos o regla de negocio | Ver el catálogo del endpoint |
| 429 | Más de 100 peticiones por minuto del usuario (RNF-09). Incluye `Retry-After`. | `rate_limit.exceeded` |
| 500 | Error inesperado | `internal` |
| 503 | Dependencia caída (base de datos, Redis, Cognito) | `service.unavailable` |

### 8.2 Catálogo de códigos

Los códigos son estables: una vez publicados no cambian de significado. Formato `area.reason`. El catálogo completo de cada endpoint está en la descripción de sus respuestas en `openapi.yaml`. Códigos de la semana 1:

| Código | Estado | Significado |
| --- | --- | --- |
| `request.malformed` | 400 | Cuerpo ilegible. |
| `validation.required`, `validation.length`, `validation.format` | 422 | Errores genéricos de campo. |
| `terms.not_accepted` | 403 | Crear un proyecto sin haber aceptado los términos (RN-12). |
| `terms.outdated_version` | 422 | Se intentó aceptar una versión de los términos que no es la vigente. |
| `url.invalid_format` | 422 | La URL no se puede interpretar, trae usuario y contraseña, o trae fragmento. |
| `url.scheme_not_allowed` | 422 | El esquema no es `http` ni `https` (RF-11). |
| `url.destination_not_allowed` | 422 | El host es una IP, o resuelve a una, privada, de loopback, de enlace local, de metadatos o propia de Hindama (RF-11, ADR-008). |
| `project.confirmation_mismatch` | 422 | Al eliminar, el nombre de confirmación no coincide (RF-14). |
| `project.active_run` | 409 | Eliminar un proyecto con una ejecución activa (CU-06 E2). |
| `verification.file_not_found` | 422 | El archivo de verificación no existe (RF-21). |
| `verification.content_mismatch` | 422 | El archivo existe pero no contiene el código. |
| `verification.txt_missing` | 422 | No hay un registro TXT con el código. |
| `verification.connection_error` | 422 | No se pudo conectar, o se agotó el tiempo de espera. |
| `verification.destination_not_allowed` | 422 | El host resolvió a una dirección no permitida; queda en la bitácora. |
| `contract.invalid` | 422 | No es un OpenAPI 3 válido; `errors` indica la ubicación (RF-25). |
| `contract.unsupported_version` | 422 | Es Swagger 2 u otra versión (RF-25). |
| `contract.source_required` | 422 | No se envió ni archivo ni URL, o se enviaron los dos. |
| `contract.too_large` | 413 | Más de 5 MB (RF-22). |
| `contract.url_unreachable` | 422 | La URL del contrato no respondió o no devolvió 200. |
| `contract.url_not_allowed` | 422 | La URL del contrato resuelve a un destino no permitido. |

## 9. Advertencias

Una operación puede tener éxito y aun así tener algo que el analista debe saber. Esas situaciones van en un campo `warnings` del recurso, **no** como error:

```json
"warnings": [
  { "code": "url.no_tls", "message": "La URL usa HTTP: el tráfico y las credenciales de prueba viajarán sin cifrar.", "location": null }
]
```

Hay advertencias **persistentes**, que vuelven en toda respuesta mientras la condición siga (por ejemplo `url.no_tls`), y **momentáneas**, que solo vienen en la respuesta de la operación que las causó (por ejemplo `project.verification_lost`). El contrato indica de qué tipo es cada una. Igual que los errores, el frontend elige el texto según `code`. Códigos de la semana 1: `url.no_tls` (CU-05 E4), `url.unresolved` (el host aún no resuelve en DNS; se podrá verificar cuando resuelva), `project.verification_lost` (RF-13), `contract.servers_mismatch` (RF-27), `contract.external_reference` (RF-23), `contract.unparsed_element`, `contract.unchanged` (la versión importada es idéntica a la anterior). En los avisos del contrato, `location` es un JSON Pointer dentro del documento.

## 10. Edición y eliminación

- `PATCH` con cambios parciales: lo que no viene no cambia, y `null` borra un campo opcional. No hay `PUT`.
- **Sin control de concurrencia en v1.0:** si dos pestañas editan lo mismo, gana la última. Es una limitación declarada.
- La eliminación de un proyecto exige `?confirmation=<nombre exacto>` (RF-14). No es un control de seguridad: evita que un error del cliente borre un proyecto.

## 11. Secretos

- Las credenciales de las identidades son **`writeOnly`**: se envían al crear o editar y nunca vuelven en una respuesta; en su lugar viene `credential_suffix` con los últimos 4 caracteres (RF-31, RN-11).
- La API nunca devuelve tokens de Cognito, claves ni datos de otro usuario.
- Ningún secreto viaja en la URL (ni en parámetros de consulta ni en la ruta), porque las URLs quedan en los registros.

## 12. Límites y tiempos

- 100 peticiones por minuto por usuario (RNF-09). Abrir el stream de progreso cuenta como una; sus eventos no cuentan (ADR-006).
- Cuerpo máximo: 5 MB para la importación de contratos y 1 MB para todo lo demás.
- Las operaciones síncronas que salen a Internet (verificación, importación por URL) tienen sus propios tiempos de espera (ADR-008) y pueden tardar hasta 20 segundos. El BFF debe esperar al menos 30 segundos antes de cortar.
