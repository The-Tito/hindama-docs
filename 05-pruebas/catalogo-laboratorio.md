# Catálogo del laboratorio

- **Versión:** 1.0 (2026-11-16). Cubre el módulo Acceso a objetos (API1). Los demás módulos se agregan conforme se programan (tareas 3.2 en adelante).
- **Estado:** API1 se congela al fusionarse, con la etiqueta `catalogo-api1` sobre `main`.
- **Relacionado con:** RF-56, RF-61, RF-62, RN-05, RN-06, ADR-014, tarea 3.2 del plan del backend.

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
| `ana` | usuario | login automático (`POST /auth/login`) | pedido `ord-ana-1`, factura `inv-ana-1`, cuenta `acc-ana` |
| `beto` | usuario | token Bearer | pedido `ord-beto-1`, factura `inv-beto-1`, cuenta `acc-beto` |
| `raiz` | administrador | token Bearer | ninguno |
| anónima | — | sin credencial | ninguno |

### 2.2 Operaciones de la mini API (acceso a objetos)

| Operación | Política confirmada | Parámetro de recurso | Modo vulnerable | Modo seguro |
| --- | --- | --- | --- | --- |
| `GET /orders` | cualquier autenticado | — | Lista los pedidos propios | Igual |
| `GET /orders/{order_id}` | solo propietario | `order_id` → `orders` | Devuelve cualquier pedido a cualquier autenticado | 404 si el pedido es ajeno |
| `DELETE /orders/{order_id}` | solo propietario | `order_id` → `orders` | Borra cualquier pedido | 404 si es ajeno |
| `GET /invoices/{invoice_id}` | solo propietario | `invoice_id` → `invoices` | **Señuelo:** 200 con `{"error": "not_found"}` si es ajena | Igual |
| `GET /accounts/{account_id}/statement` | propietario o administrador | `account_id` → `accounts` | Cualquier autenticado lee cualquier estado de cuenta | Solo el dueño y `raiz`; los demás reciben 403 |

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
