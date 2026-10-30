---
documento: Convenciones de la API
proyecto: Hindama
version: 0.1
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
  - La cabecera `Prefer` elige qué devolver: `Prefer: example=proyectoNuevoHttp` (un ejemplo por nombre) o `Prefer: code=422` (un código de estado).
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
| `X-Hindama-IP-Cliente` | Next.js → API | IP real del navegador, para la bitácora (RF-82). FastAPI solo la acepta si la petición viene de la IP privada del frontend; si no, la ignora. Nunca se usa para autorizar. |
| `X-Request-Id` | Ambas | Identificador de la petición. Si Next.js lo envía, la API lo conserva; si no, lo genera. Siempre vuelve en la respuesta y en los errores (`id_peticion`), y aparece en los registros. |
| `Retry-After` | API → Next.js | En las respuestas 429. |

- **Rol:** sale del claim `cognito:groups` (RN-04). Los endpoints de proyectos responden **403** al administrador (RF-80); los de `/admin/*`, 403 al analista.
- **Sin la sesión, el resto no existe:** una petición sin token o con un token inválido recibe 401 antes de cualquier otra validación, incluso si la ruta no existe.

## 4. Nombres y rutas

- Rutas y campos **en español, sin acentos ni `ñ`**: `/proyectos`, `estado_verificacion`, `tamano`.
- Campos JSON en `snake_case`. Valores de catálogo (estados, módulos, severidades) en `snake_case` y minúsculas: `pendiente`, `acceso_objetos`, `critica`.
- Colecciones en plural. Todo lo que pertenece a un proyecto cuelga de él, con **dos niveles como máximo**: `/proyectos/{proyecto_id}/contratos/{contrato_id}`. Así la propiedad queda explícita en la ruta y la API comprueba que el hijo pertenece al proyecto.
- Acciones que no son CRUD: `POST` sobre un sustantivo que describe el resultado: `POST /proyectos/{id}/verificacion`, `POST /yo/terminos`. Si no hay un sustantivo natural, se usa un verbo en infinitivo: `POST …/ejecuciones/{id}/cancelar`.
- Administración bajo `/admin/*`.
- `operationId` en `camelCase`, verbo + recurso: `listarProyectos`, `crearProyecto`, `verificarPropiedad`. El frontend los usa como nombres de función.

## 5. Formatos

| Tipo | Formato |
| --- | --- |
| Identificadores | UUID en texto (`format: uuid`). Son opacos: el cliente no los interpreta ni los genera. |
| Fechas y horas | RFC 3339 en UTC con `Z`: `2026-10-30T18:04:05Z`. |
| Números consecutivos para mostrar | Enteros (`numero` de ejecución o de versión de contrato). Solo sirven para mostrar; las rutas usan el UUID. |
| Campos opcionales | **Siempre presentes**, con `null` si no tienen valor. Nunca se omiten. |
| Texto | UTF-8. Los textos que vienen de la API del analista (evidencias, avisos del contrato) son **no confiables**: el frontend los muestra como texto escapado, nunca como HTML. |

## 6. Respuestas

- **Un recurso:** el objeto directamente, sin sobre.
- **Una lista:** siempre paginada, con este sobre:

```json
{
  "elementos": [ … ],
  "total": 37,
  "pagina": 1,
  "tamano": 20
}
```

- **Creación:** `201` con el recurso creado y la cabecera `Location`.
- **Eliminación:** `204` sin cuerpo.
- **Trabajo asíncrono** (ejecuciones, desde la semana 2): `202` con el recurso en su estado inicial.

## 7. Paginación, filtros y orden

- Parámetros `pagina` (desde 1, por defecto 1) y `tamano` (1 a 100, por defecto 20). Una página fuera de rango devuelve `elementos: []` con el `total` real, no un error.
- **Excepción:** `GET …/operaciones` acepta `tamano` hasta 500, porque las pantallas de política y de operaciones necesitan la lista completa de un contrato (RNF-02 considera hasta 500 operaciones).
- Los filtros son parámetros de consulta con el nombre del campo: `?estado=nuevo&severidad=alta`. Para varios valores se repite el parámetro: `?severidad=critica&severidad=alta`.
- Cada lista documenta su orden por defecto en el contrato. Donde se puede elegir el orden, se usa `orden=campo` o `orden=-campo` (descendente).

## 8. Errores

Todos los errores usan **Problem Details** ([RFC 9457](https://www.rfc-editor.org/rfc/rfc9457)) con `Content-Type: application/problem+json`, extendido con `codigo`, `id_peticion` y, si hay errores por campo, `errores`:

```json
{
  "type": "urn:hindama:error:url.destino_no_permitido",
  "title": "La URL apunta a un destino no permitido",
  "status": 422,
  "detail": "La URL base resuelve a una dirección privada. Usa una dirección pública de tu API.",
  "codigo": "url.destino_no_permitido",
  "id_peticion": "0192e3b1-7c1a-7d40-9f5e-1b2c3d4e5f60",
  "errores": [
    { "campo": "url_base", "codigo": "url.destino_no_permitido", "mensaje": "Resuelve a una dirección privada." }
  ]
}
```

- `type` es `urn:hindama:error:<codigo>`: un identificador, no una página que se pueda abrir.
- **`codigo` es el contrato; `title` y `detail` no.** El frontend elige el texto que muestra según `codigo` (y `errores[].codigo`), lo que mantiene los textos separados del código para poder agregar inglés (sección 11 de requerimientos). `detail` está en español y sirve de respaldo para códigos que el frontend aún no conoce.
- `errores[].campo` usa la ruta del campo en el cuerpo con puntos (`credencial.valor`) o el nombre del parámetro de consulta. Es `null` para errores que no son de un campo.
- **Nunca** hay trazas, nombres de tablas, SQL, rutas de archivos ni datos de otros usuarios en un error (RNF-07). Un 500 solo trae `codigo: interno` e `id_peticion`, que sirve para buscar el detalle en los registros.
- Los errores de validación de FastAPI (422 por defecto) se transforman a este formato; nunca sale el formato `{"detail": [...]}` de FastAPI.

### 8.1 Códigos de estado

| Estado | Cuándo | `codigo` típico |
| --- | --- | --- |
| 400 | JSON mal formado o tipo de contenido incorrecto | `peticion.mal_formada` |
| 401 | Sin token, token vencido o inválido. Incluye `WWW-Authenticate: Bearer`. | `autenticacion.requerida`, `autenticacion.token_invalido` |
| 403 | El rol no permite la operación, o faltan los términos de uso | `rol.no_permitido`, `terminos.no_aceptados` |
| 404 | No existe **o es de otro analista**. Las dos respuestas son idénticas (RN-02, RNF-05). | `recurso.no_encontrado` |
| 409 | Conflicto con el estado actual | `proyecto.ejecucion_activa` |
| 413 | Archivo demasiado grande | `contrato.demasiado_grande` |
| 422 | Validación de campos o regla de negocio | Ver el catálogo del endpoint |
| 429 | Más de 100 peticiones por minuto del usuario (RNF-09). Incluye `Retry-After`. | `limite.peticiones` |
| 500 | Error inesperado | `interno` |
| 503 | Dependencia caída (base de datos, Redis, Cognito) | `servicio.no_disponible` |

### 8.2 Catálogo de códigos

Los códigos son estables: una vez publicados no cambian de significado. Formato `area.motivo`. El catálogo completo de cada endpoint está en la descripción de sus respuestas en `openapi.yaml`. Códigos de la semana 1:

| Código | Estado | Significado |
| --- | --- | --- |
| `peticion.mal_formada` | 400 | Cuerpo ilegible. |
| `validacion.campo_requerido`, `validacion.longitud`, `validacion.formato` | 422 | Errores genéricos de campo. |
| `terminos.no_aceptados` | 403 | Crear un proyecto sin haber aceptado los términos (RN-12). |
| `terminos.version_obsoleta` | 422 | Se intentó aceptar una versión de los términos que no es la vigente. |
| `url.formato_invalido` | 422 | La URL no se puede interpretar, trae usuario y contraseña, o trae fragmento. |
| `url.esquema_no_permitido` | 422 | El esquema no es `http` ni `https` (RF-11). |
| `url.destino_no_permitido` | 422 | El host es una IP, o resuelve a una, privada, de loopback, de enlace local, de metadatos o propia de Hindama (RF-11, ADR-008). |
| `proyecto.confirmacion_incorrecta` | 422 | Al eliminar, el nombre de confirmación no coincide (RF-14). |
| `proyecto.ejecucion_activa` | 409 | Eliminar un proyecto con una ejecución activa (CU-06 E2). |
| `verificacion.archivo_no_encontrado` | 422 | El archivo de verificación no existe (RF-21). |
| `verificacion.contenido_distinto` | 422 | El archivo existe pero no contiene el código. |
| `verificacion.txt_ausente` | 422 | No hay un registro TXT con el código. |
| `verificacion.error_conexion` | 422 | No se pudo conectar, o se agotó el tiempo de espera. |
| `verificacion.destino_no_permitido` | 422 | El host resolvió a una dirección no permitida; queda en la bitácora. |
| `contrato.invalido` | 422 | No es un OpenAPI 3 válido; `errores` indica la ubicación (RF-25). |
| `contrato.version_no_soportada` | 422 | Es Swagger 2 u otra versión (RF-25). |
| `contrato.origen_requerido` | 422 | No se envió ni archivo ni URL, o se enviaron los dos. |
| `contrato.demasiado_grande` | 413 | Más de 5 MB (RF-22). |
| `contrato.url_inaccesible` | 422 | La URL del contrato no respondió o no devolvió 200. |
| `contrato.url_no_permitida` | 422 | La URL del contrato resuelve a un destino no permitido. |

## 9. Advertencias

Una operación puede tener éxito y aun así tener algo que el analista debe saber. Esas situaciones van en un campo `advertencias` del recurso, **no** como error:

```json
"advertencias": [
  { "codigo": "url.sin_tls", "mensaje": "La URL usa HTTP: el tráfico y las credenciales de prueba viajarán sin cifrar.", "ubicacion": null }
]
```

Hay advertencias **persistentes**, que vuelven en toda respuesta mientras la condición siga (por ejemplo `url.sin_tls`), y **momentáneas**, que solo vienen en la respuesta de la operación que las causó (por ejemplo `proyecto.verificacion_perdida`). El contrato indica de qué tipo es cada una. Igual que los errores, el frontend elige el texto según `codigo`. Códigos de la semana 1: `url.sin_tls` (CU-05 E4), `url.no_resuelve` (el host aún no resuelve en DNS; se podrá verificar cuando resuelva), `proyecto.verificacion_perdida` (RF-13), `contrato.servidores_distintos` (RF-27), `contrato.referencia_externa` (RF-23), `contrato.elemento_no_interpretado`, `contrato.sin_cambios` (la versión importada es idéntica a la anterior). En los avisos del contrato, `ubicacion` es un JSON Pointer dentro del documento.

## 10. Edición y eliminación

- `PATCH` con cambios parciales: lo que no viene no cambia, y `null` borra un campo opcional. No hay `PUT`.
- **Sin control de concurrencia en v1.0:** si dos pestañas editan lo mismo, gana la última. Es una limitación declarada.
- La eliminación de un proyecto exige `?confirmacion=<nombre exacto>` (RF-14). No es un control de seguridad: evita que un error del cliente borre un proyecto.

## 11. Secretos

- Las credenciales de las identidades son **`writeOnly`**: se envían al crear o editar y nunca vuelven en una respuesta; en su lugar viene `credencial_sufijo` con los últimos 4 caracteres (RF-31, RN-11).
- La API nunca devuelve tokens de Cognito, claves ni datos de otro usuario.
- Ningún secreto viaja en la URL (ni en parámetros de consulta ni en la ruta), porque las URLs quedan en los registros.

## 12. Límites y tiempos

- 100 peticiones por minuto por usuario (RNF-09). Abrir el stream de progreso cuenta como una; sus eventos no cuentan (ADR-006).
- Cuerpo máximo: 5 MB para la importación de contratos y 1 MB para todo lo demás.
- Las operaciones síncronas que salen a Internet (verificación, importación por URL) tienen sus propios tiempos de espera (ADR-008) y pueden tardar hasta 20 segundos. El BFF debe esperar al menos 30 segundos antes de cortar.
