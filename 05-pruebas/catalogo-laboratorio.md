# Catálogo del laboratorio

- **Versión:** 1.3 (2026-11-23). Cubre Acceso a objetos (API1), Acceso a funciones (API5), Autenticación (API2), Configuración (API8) y Consumo de recursos (API4). Los demás módulos se agregan conforme se programan.
- **Historial:** 1.0 (API1), congelada con la etiqueta `catalogo-api1`. 1.1 agrega API5 y API2, congelada con `catalogo-api5-api2`. 1.2 agrega API8, congelada con `catalogo-api8`. 1.3 agrega API4 y se congela al fusionarse con `catalogo-api4`. Las fallas anteriores no cambian.
- **Relacionado con:** RF-54, RF-55, RF-56, RF-57, RF-59, RF-61, RF-62, RN-05, RN-06, ADR-014, tarea 3.2 del plan del backend.

## 1. Propósito

El motor de pruebas no se puede juzgar contra sí mismo: hay que saber de antemano qué fallas tiene la API que examina. Este catálogo fija, **antes de programar cada módulo**, qué debe encontrar Hindama y qué no:

- En el **modo vulnerable** del laboratorio, cada falla del catálogo debe aparecer con su tipo, operación, identidad y severidad.
- En el **modo seguro**, la misma operación no debe producir ningún hallazgo.
- Los **señuelos** son respuestas que parecen una falla y no lo son (por ejemplo, un 200 con un error en el cuerpo). Nunca deben producir hallazgos (RF-61).

Si el motor encuentra algo fuera del catálogo, o deja de encontrar algo que está en él, la prueba de integración del backend falla. Cambiar el catálogo exige una nueva versión de este documento.

## 2. Las APIs del laboratorio

| API | Dónde vive | Uso |
| --- | --- | --- |
| **Mini API** | `hindama-backend/tests/lab/` (FastAPI), con modo `secure` y `vulnerable` | Pruebas de integración del motor. Las pruebas la levantan en loopback; solo ellas pueden permitir esa dirección (ADR-008) |
| **VAmPI** | Imagen pública de VAmPI, fuera de los repositorios | Prueba de carga y demostración en el despliegue (tarea 3.5). Sus fallas se catalogan entonces |

### 2.1 Identidades de la mini API

| Identidad | Rol declarado | Autenticación | Recursos propios |
| --- | --- | --- | --- |
| `ana` | usuario | login automático (`POST /auth/login`), que emite un JWT HS256 | pedido `ord-ana-1`, factura `inv-ana-1`, cuenta `acc-ana` |
| `beto` | usuario | token Bearer | pedido `ord-beto-1`, factura `inv-beto-1`, cuenta `acc-beto` |
| `raiz` | administrador | token Bearer | ninguno |
| anónima | — | sin credencial | ninguno |

### 2.2 Operaciones de la mini API

| Operación | Política confirmada | Parámetro de recurso | Modo vulnerable | Modo seguro |
| --- | --- | --- | --- | --- |
| `GET /orders` | cualquier autenticado | — | Lista los pedidos propios | Igual |
| `GET /orders/{order_id}` | solo propietario | `order_id` → `orders` | Devuelve cualquier pedido a cualquier autenticado | 404 si el pedido es ajeno |
| `DELETE /orders/{order_id}` | solo propietario | `order_id` → `orders` | Borra cualquier pedido | 404 si es ajeno |
| `GET /invoices/{invoice_id}` | solo propietario | `invoice_id` → `invoices` | **Señuelo:** 200 con `{"error": "not_found"}` si es ajena | Igual |
| `GET /accounts/{account_id}/statement` | propietario o administrador | `account_id` → `accounts` | Cualquier autenticado lee cualquier estado de cuenta | Solo el dueño y `raiz`; los demás reciben 403 |
| `GET /reports` | cualquier autenticado | — | Responde **sin credenciales** | 401 sin credenciales |
| `GET /admin/users` | solo administrador | — | Cualquier autenticado lista los usuarios | 403 si no es `raiz` |
| `GET /admin/audit` | solo administrador | — | **Señuelo:** 200 con `{"error": "forbidden"}` si no es `raiz` | Igual |
| `DELETE /admin/users/{user_id}` | solo administrador | — | Cualquier autenticado borra | 403 si no es `raiz` |
| `POST /auth/login` | pública | — | Emite el JWT de `ana` | Igual |
| `GET /catalog` | pública | — | Responde siempre (sin límite de peticiones) | Desde la petición 21 de la misma ejecución responde 429 con `Retry-After` |
| `POST /tickets` | sin confirmar | — | Lee cualquier cuerpo, sin límite de tamaño, y lo valida (un arreglo es 422) | Un cuerpo de más de 1 MB recibe 413 antes de leerse |

**Operaciones que no cambian lo anterior.** Las de la versión 1.3 se agregan sin alterar ningún resultado de las secciones 3 a 7:
- `GET /catalog` es pública y `POST /tickets` queda sin política: API1, API2 y API5 no prueban ninguna de las dos (RN-08).
- Configuración (API8) sigue eligiendo las mismas rutas: su petición principal va a la primera GET sin parámetros (`GET /admin/audit`) y ninguna de las nuevas tiene parámetros de ruta.
- `POST /tickets` exige autenticación en los dos modos; `GET /catalog` es pública por diseño.
- El límite de 1 MB del modo seguro aplica a toda la mini API; ninguna prueba anterior envía cuerpos de ese tamaño.

**Configuración de la mini API (API8).**

| Aspecto | Modo vulnerable | Modo seguro |
| --- | --- | --- |
| Cabeceras de seguridad | Ninguna | `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` y `Strict-Transport-Security` |
| CORS | Devuelve en `Access-Control-Allow-Origin` el origen que recibe, con `Access-Control-Allow-Credentials: true` | Sin cabeceras CORS |
| Errores | `GET /invoices/{invoice_id}` con un identificador mal formado (sin el prefijo `inv-`) responde 500 con el traceback de Python | Igual que con una factura ajena: el señuelo de API1 |
| Versión | `X-Powered-By: Python/3.12 FastAPI/0.115` | Sin `X-Powered-By` |
| Ruta inexistente | **Señuelo:** el 404 normal de FastAPI, `{"detail": "Not Found"}` | Igual |

**Tokens.** Los de `beto` y `raiz` son opacos. El de `ana` es un JWT HS256 firmado por la mini API:
- En modo **vulnerable**, la mini API lee el JWT **sin verificar la firma** y acepta `alg: none`.
- En modo **seguro**, verifica la firma y exige `HS256`; cualquier otra cosa recibe 401.

## 3. Acceso a objetos (API1)

### 3.1 Cómo decide el módulo

Para cada operación con política de propiedad confirmada y un parámetro de recurso, y para cada identidad autenticada (una celda de la matriz, RF-64):

1. **Víctimas:** hasta 3 recursos confirmados del mismo tipo que pertenezcan a otras identidades. Solo se prueban operaciones cuyos parámetros de ruta son todos parámetros de recurso; en `/users/{u}/orders/{o}` se ataca el último y los demás toman recursos del mismo dueño.
2. **Control:** pide cada recurso como su dueño. Si el dueño no obtiene 2xx, ese recurso no sirve como prueba. Sin ningún recurso útil, la celda queda `skipped` con `baseline_failed`.
3. **Ataque:** pide el mismo recurso como la identidad de la celda. Hay falla solo si se cumplen las tres condiciones:
   - responde 2xx;
   - el cuerpo no está vacío;
   - el cuerpo contiene el identificador del recurso o es igual al que recibió el dueño.
4. **Métodos:** solo GET y HEAD. Los métodos que modifican quedan `skipped` con `method_not_safe` hasta que existan recursos creados por la plataforma (RN-06).
5. **Administrador:** con la política «propietario o administrador», la celda de una identidad administradora espera `allowed` y nunca es falla.

Vocabulario de `expected` y `observed` en `results`:
- `allowed`, `denied` y `no_data` cuando hubo respuesta;
- `baseline_failed`, `method_not_safe`, `no_resources` (ninguna otra identidad tiene recursos de ese tipo), `login_failed` y `credential_expired` (RF-33) cuando la celda queda `skipped`;
- `error` cuando ninguna petición obtuvo respuesta (red o guardia SSRF);
- `observed` lleva delante el código HTTP, por ejemplo `200 allowed`.

### 3.2 Hallazgo

| Campo | Valor |
| --- | --- |
| `finding_type` | `object_access.unauthorized_read` |
| Severidad | alta |
| OWASP | API1:2023 Broken Object Level Authorization |
| CWE | CWE-639 Authorization Bypass Through User-Controlled Key |
| Evidencia | La petición del ataque y su respuesta (credencial enmascarada, cuerpo truncado a 10 KB) y el recurso ajeno con su dueño |

### 3.3 Fallas esperadas

| ID | Operación | Identidad | Modo vulnerable | Modo seguro |
| --- | --- | --- | --- | --- |
| LAB-API1-01 | `GET /orders/{order_id}` | `ana` | Hallazgo (lee `ord-beto-1`) | `pass` (`404 denied`) |
| LAB-API1-02 | `GET /orders/{order_id}` | `beto` | Hallazgo (lee `ord-ana-1`) | `pass` |
| LAB-API1-03 | `GET /orders/{order_id}` | `raiz` | Hallazgo: la política es «solo propietario» | `pass` |
| LAB-API1-04 | `GET /accounts/{account_id}/statement` | `ana` y `beto` | Hallazgo cada una | `pass` (`403 denied`) |
| LAB-API1-05 | `GET /accounts/{account_id}/statement` | `raiz` | `pass` (`200 allowed`, esperado) | `pass` |
| LAB-API1-06 | `GET /invoices/{invoice_id}` | `ana`, `beto` y `raiz` | **Señuelo:** `pass` (`200 no_data`), sin hallazgo | `pass` |
| LAB-API1-07 | `DELETE /orders/{order_id}` | todas | `skipped` (`method_not_safe`), sin petición | Igual |
| LAB-API1-08 | `GET /orders` | todas | Sin celda: no es una política de propiedad | Igual |

Totales en el modo vulnerable: **5 hallazgos** de acceso a objetos (LAB-API1-01 a 04). En el modo seguro: **0**.

## 4. Regla común: ¿la respuesta es un acceso real? (RF-61)

API5 y API2 comparan la respuesta sospechosa con la de una **petición de control** hecha por una identidad que la política sí permite. Hay acceso solo si se cumplen las tres condiciones:
- la respuesta es 2xx;
- el cuerpo no está vacío;
- el cuerpo es igual al del control o tiene **su misma forma**: el mismo tipo JSON y las mismas claves de primer nivel, o dos listas.

Así, un 200 con `{"error": ...}` frente a un control con datos no es un acceso (`no_data`). Si el control no obtiene 2xx, la celda queda `skipped` con `baseline_failed`. Como en API1, solo se envían GET y HEAD, y el vocabulario de `expected` y `observed` es el mismo de la sección 3.1.

## 5. Acceso a funciones (API5)

### 5.1 Cómo decide el módulo

- **Celdas:** cada operación con política confirmada «solo administrador» por cada identidad **autenticada y no administradora**. La identidad anónima pertenece a Autenticación (API2), para no reportar dos veces la misma falla.
- **Requisitos (RF-45, RF-57):** una identidad administradora y una autenticada que no lo sea; si falta la segunda, el módulo indica `insufficient_identities`.
- **Control:** la identidad administradora. **Ataque:** la identidad de la celda. Se espera `denied`.
- Los parámetros de ruta se llenan con recursos de la identidad de control. Si alguno no es un parámetro de recurso o no hay recurso, la celda queda `skipped` con `no_resources`.

### 5.2 Hallazgo

| Campo | Valor |
| --- | --- |
| `finding_type` | `function_access.unauthorized_call` |
| Severidad | alta |
| OWASP | API5:2023 Broken Function Level Authorization |
| CWE | CWE-285 Improper Authorization |

### 5.3 Fallas esperadas

| ID | Operación | Identidad | Modo vulnerable | Modo seguro |
| --- | --- | --- | --- | --- |
| LAB-API5-01 | `GET /admin/users` | `ana` y `beto` | Hallazgo cada una (`200 allowed`) | `pass` (`403 denied`) |
| LAB-API5-02 | `GET /admin/audit` | `ana` y `beto` | **Señuelo:** `pass` (`200 no_data`) | Igual |
| LAB-API5-03 | `DELETE /admin/users/{user_id}` | `ana` y `beto` | `skipped` (`method_not_safe`), sin petición | Igual |
| LAB-API5-04 | operaciones «solo administrador» | `raiz` y anónima | Sin celda | Igual |

Totales: **2 hallazgos** en modo vulnerable, **0** en el seguro.

## 6. Autenticación (API2)

### 6.1 Cómo decide el módulo

Se prueban las operaciones con política confirmada distinta de «pública» (RF-54). Hay dos clases de celda:

1. **Anónima, una por operación:**
   - Primero la petición **sin credenciales**.
   - Solo si se rechaza, la misma petición con **credenciales vacías** (`Authorization: Bearer` sin valor). Si la primera ya pasó, la segunda no aporta nada.
   - Control: una identidad que la política permite: la administradora para «solo administrador», la dueña de un recurso para las de propiedad, y cualquier autenticada para «cualquier autenticado».
2. **Una por operación e identidad cuyo token es un JWT**, solo en las operaciones que esa identidad puede usar según la política:
   - **Firma alterada:** el mismo JWT con otra firma.
   - **`alg: none`:** la misma cabecera y carga con `"alg": "none"` y sin firma.
   - Control: la propia identidad con su token real.
   - Si la operación responde también sin credenciales, la celda queda `skipped` con `no_auth_required`, porque eso ya es la falla de la celda anónima.
   - Las identidades con login automático se planean siempre, porque su token se conoce al iniciar sesión. Si no resulta un JWT, la celda queda `skipped` con `not_jwt`.

**Credenciales vencidas (RF-54).** Sin la llave de la API del analista no se puede fabricar un token vencido que sea válido. Las dos variantes de firma lo cubren: si la API acepta un JWT modificado, también acepta uno con el vencimiento cambiado. Los tokens reales que vencen durante la ejecución los detecta RF-33.

### 6.2 Hallazgos

| `finding_type` | Variante | Severidad | CWE |
| --- | --- | --- | --- |
| `authentication.no_credentials` | sin credenciales | alta | CWE-306 Missing Authentication for Critical Function |
| `authentication.empty_credentials` | credenciales vacías | alta | CWE-287 Improper Authentication |
| `authentication.tampered_signature` | firma alterada | crítica | CWE-347 Improper Verification of Cryptographic Signature |
| `authentication.alg_none` | `alg: none` | crítica | CWE-347 Improper Verification of Cryptographic Signature |

Todos con OWASP API2:2023 Broken Authentication. Una celda puede producir dos hallazgos, uno por variante, cada uno con su huella.

### 6.3 Fallas esperadas

| ID | Operación | Identidad | Modo vulnerable | Modo seguro |
| --- | --- | --- | --- | --- |
| LAB-API2-01 | `GET /reports` | anónima | Hallazgo `no_credentials`; las credenciales vacías no se prueban | `pass` (`401 denied`, también con credenciales vacías) |
| LAB-API2-02 | demás operaciones GET protegidas | anónima | `pass` (`401 denied`) | Igual |
| LAB-API2-03 | `GET /orders`, `GET /orders/{order_id}`, `GET /invoices/{invoice_id}`, `GET /accounts/{account_id}/statement` | `ana` | Dos hallazgos en cada una: `tampered_signature` y `alg_none` | `pass` (`401 denied`) |
| LAB-API2-04 | `GET /reports` | `ana` | `skipped` (`no_auth_required`) | `pass` |
| LAB-API2-05 | `DELETE` protegidos | anónima y `ana` | `skipped` (`method_not_safe`) | Igual |
| LAB-API2-06 | cualquier operación | `beto` y `raiz` | Sin celda: sus tokens no son JWT | Igual |
| LAB-API2-07 | `GET /admin/users`, `GET /admin/audit` | `ana` | Sin celda: la política no se lo permite | Igual |

Totales: **9 hallazgos** en modo vulnerable (1 + 4 × 2), **0** en el seguro.

## 7. Configuración (API8)

### 7.1 Cómo decide el módulo

- **Una sola celda para toda la API:** sin operación y con la identidad anónima. Ejecuta todas las comprobaciones y puede producir varios hallazgos, cada uno con su huella. Una celda por operación repetiría la misma cabecera ausente en cada operación.
- **No requiere contrato (RF-45).** Si hay contrato, lo usa para elegir rutas reales.
- **Como mucho 6 peticiones, todas GET:**
  1. **Petición principal**, como la identidad anónima, a la primera operación GET del contrato sin parámetros de ruta, o a la URL base si no hay contrato. Lleva `Origin: https://origen-no-confiable.hindama.invalid`. Sirve para las cabeceras, CORS y la versión.
  2. **Ruta inexistente** (`/hindama-ruta-inexistente`).
  3. **Hasta 3 operaciones GET con parámetros de ruta**, con un valor mal formado en cada parámetro: una cadena larga de letras, sin comillas ni sintaxis SQL, para no invadir el módulo de inyección SQL.

  Las peticiones 2 y 3 usan la primera identidad autenticada, para pasar la autenticación y llegar al código que falla; si no hay ninguna, la anónima.
- **Cabeceras ausentes**, en la petición principal:
  - `Strict-Transport-Security`, solo si la URL base es HTTPS;
  - `X-Content-Type-Options: nosniff`;
  - protección contra marcos: `X-Frame-Options` o `frame-ancestors` en `Content-Security-Policy`.

  `Cache-Control` no se exige, para no llenar de ruido a las APIs públicas.
- **CORS:** es falla si la respuesta devuelve el origen ficticio, o `*`, junto con `Access-Control-Allow-Credentials: true`.
- **Detalles internos:** solo en respuestas 4xx y 5xx. Se buscan:
  - trazas de Python, Java, .NET, Node o PHP;
  - errores de base de datos (`SQLSTATE`, `ORA-`, errores de sintaxis SQL);
  - rutas de archivos del servidor.
- **Versión:** `Server` o `X-Powered-By` con un número de versión.
- `expected` es `hardened`. `observed` es la lista de fallas encontradas, por ejemplo `missing_header.nosniff, cors.any_origin_with_credentials`, o `hardened` si no hay ninguna.

### 7.2 Hallazgos

| `finding_type` | Severidad | CWE |
| --- | --- | --- |
| `configuration.missing_header.hsts` | baja | CWE-319 Cleartext Transmission of Sensitive Information |
| `configuration.missing_header.nosniff` | baja | CWE-693 Protection Mechanism Failure |
| `configuration.missing_header.frame_options` | baja | CWE-1021 Improper Restriction of Rendered UI Layers |
| `configuration.cors.any_origin_with_credentials` | media | CWE-942 Permissive Cross-domain Policy with Untrusted Domains |
| `configuration.error_details` | media | CWE-209 Generation of Error Message Containing Sensitive Information |
| `configuration.version_disclosure` | informativa | CWE-200 Exposure of Sensitive Information to an Unauthorized Actor |

Todos con OWASP API8:2023 Security Misconfiguration.

### 7.3 Fallas esperadas

| ID | Comprobación | Modo vulnerable | Modo seguro |
| --- | --- | --- | --- |
| LAB-API8-01 | `X-Content-Type-Options` | Hallazgo `missing_header.nosniff` | Sin hallazgo |
| LAB-API8-02 | Protección contra marcos | Hallazgo `missing_header.frame_options` | Sin hallazgo |
| LAB-API8-03 | HSTS | Sin hallazgo: la mini API es HTTP. La regla se prueba con pruebas unitarias | Igual |
| LAB-API8-04 | CORS | Hallazgo `cors.any_origin_with_credentials` | Sin hallazgo |
| LAB-API8-05 | `GET /invoices/{invoice_id}` mal formado | Hallazgo `error_details` (traceback) | Sin hallazgo (200 del señuelo) |
| LAB-API8-06 | `X-Powered-By` | Hallazgo `version_disclosure` | Sin hallazgo |
| LAB-API8-07 | Ruta inexistente | **Señuelo:** 404 sin detalles, sin hallazgo | Igual |

Totales: **5 hallazgos** en una sola celda en modo vulnerable, **0** en el seguro (la celda queda `pass` con `hardened`).

## 8. Consumo de recursos (API4)

### 8.1 Cómo decide el módulo

- **Riesgo alto (RN-05):** apagado por defecto; se confirma en cada ejecución. Requiere contrato (RF-45).
- **Una sola celda para toda la API**, sin operación, con la primera identidad autenticada (para pasar la autenticación); si no hay, la anónima. Hace dos comprobaciones y puede dar dos hallazgos, cada uno con su huella.
- **Límite de peticiones (ráfaga):**
  - Operación: la primera GET sin parámetros de ruta con política confirmada «pública» o «cualquier autenticado»; si no hay, la primera GET sin parámetros de ruta. Sin ninguna, la comprobación no aplica.
  - Hasta **40 peticiones seguidas**, una a la vez, al ritmo que permiten los límites de la ejecución (RF-47). Se detiene en cuanto la API responde **429 o 503**: eso es un límite.
  - La primera debe ser 2xx; si no, la comprobación no concluye (por ejemplo, la operación exige otra credencial).
  - Falla: las 40 respondieron sin 429 ni 503. El hallazgo dice «no se observó límite en 40 peticiones», no que la API no tenga ninguno.
- **Límite de tamaño del cuerpo:**
  - Operación: la primera POST, PUT o PATCH cuyo cuerpo declarado es JSON y su esquema es un **objeto**. Sin ninguna, la comprobación no aplica.
  - Cuerpos crecientes con tope: **64 KB, 1 MB y 8 MB**. Cada uno es un **arreglo JSON**, que el esquema obliga a rechazar: una API que cumple su contrato no crea nada (RN-06).
  - Se detiene en cuanto la API responde **413** o corta la conexión: eso es un límite.
  - Falla: el cuerpo de 8 MB recibe 2xx, 400 o 422, es decir, la API lo leyó completo. Otro código (401, 5xx) no concluye.
  - La evidencia guarda solo el principio del cuerpo enviado y su tamaño (`request_body_bytes` en `context`).
- **Como mucho 43 peticiones** en total (40 + 3).
- `expected` es `limited`. `observed` es la lista de fallas (`no_rate_limit, no_body_limit`), `limited` si no hubo ninguna, o `not_applicable` si ninguna comprobación aplicó o concluyó.

### 8.2 Hallazgos

| `finding_type` | Severidad | CWE |
| --- | --- | --- |
| `resource_consumption.no_rate_limit` | media | CWE-770 Allocation of Resources Without Limits or Throttling |
| `resource_consumption.no_body_limit` | media | CWE-400 Uncontrolled Resource Consumption |

Ambos con OWASP API4:2023 Unrestricted Resource Consumption.

### 8.3 Fallas esperadas

| ID | Comprobación | Modo vulnerable | Modo seguro |
| --- | --- | --- | --- |
| LAB-API4-01 | Ráfaga a `GET /catalog` | Hallazgo `no_rate_limit` (40 respuestas 200) | Sin hallazgo: 429 en la petición 21 |
| LAB-API4-02 | Cuerpos crecientes a `POST /tickets` | Hallazgo `no_body_limit` (422 al de 8 MB) | Sin hallazgo: 413 al de 1 MB |
| LAB-API4-03 | Escrituras | Ninguna: `POST /tickets` responde 422 al arreglo y no guarda nada | Igual |

Totales: **2 hallazgos** en una sola celda en modo vulnerable (identidad `ana`), **0** en el seguro (la celda queda `pass` con `limited`).
