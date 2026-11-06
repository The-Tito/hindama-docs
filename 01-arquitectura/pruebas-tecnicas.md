# Pruebas técnicas: validación de decisiones de arquitectura

- **Versión:** 1.0 (2026-11-05)
- **Estado:** PT-01, PT-02 y PT-03 concluidas
- **Relacionado con:** [ADR-008](decisiones/ADR-008-guardia-ssrf-con-ip-fijada.md), [ADR-012](decisiones/ADR-012-motor-asincrono.md), [ADR-016](decisiones/ADR-016-contrato-primero-con-verificacion-automatica.md), tarea 1.5 del plan del backend

## 1. Propósito

Algunas decisiones de arquitectura de Hindama dependen de que una biblioteca haga algo que no está garantizado por su documentación. Si se construye encima y resulta que no funciona, se rehace el trabajo de semanas. Una **prueba técnica** es un experimento corto que contesta una sola pregunta antes de escribir el código definitivo.

Este documento registra cada prueba técnica: por qué se hizo, qué riesgo resolvía, cómo se montó el experimento, qué escenarios se probaron, qué resultó y qué se decidió. Es el fundamento de las decisiones que se presentan en la entrega.

### 1.1 Método común

1. **Pregunta y criterio de éxito definidos antes de empezar.** El resultado se juzga contra ese criterio, no contra lo que salga.
2. **Código desechable fuera de los repositorios.** Los experimentos no forman parte del producto; el código definitivo se reescribe en `hindama-backend/src` con sus pruebas automáticas. Los fragmentos clave se citan aquí.
3. **Escenarios realistas.** Cada caso representa una situación que puede ocurrir en producción, incluidos ataques. Cuando un caso no prueba lo que se pretendía, se rediseña y se anota.
4. **Resultado en el ADR.** La conclusión se anota en el ADR correspondiente; si cambia la decisión, el ADR se actualiza.

### 1.2 Resumen

| ID | Pregunta | ADR | Resultado | Decisión |
| --- | --- | --- | --- | --- |
| PT-01 | ¿Puede httpx conectarse a una IP ya validada y a la vez validar TLS contra el nombre original? | ADR-008 | **Sí**, con dos enfoques; uno de ellos tiene un riesgo de reutilización de conexiones | *Network backend* propio de httpcore; un cliente por host verificado. No hace falta proxy de salida |
| PT-02 | ¿`arq` o `SAQ` cumplen cancelación en menos de 5 s, tiempo máximo por trabajo, reintentos y 10 ejecuciones por proceso? | ADR-012 | **Ambas** cumplen concurrencia y cancelación (< 1 s). arq tarda 310 s en detectar un motor caído y está en modo solo mantenimiento | **SAQ**, con latido y barrido cortos |
| PT-03 | ¿`oasdiff` y Schemathesis soportan el OpenAPI 3.1 que genera FastAPI? | ADR-016 | **Sí, las dos.** `oasdiff` genera demasiados falsos positivos al comparar lo generado contra el contrato. Schemathesis encontró 3 errores reales del backend y detecta fugas de campos | Schemathesis en la CI del backend; se mantiene la prueba de contrato propia; `oasdiff` solo entre versiones del contrato |

Otras dos suposiciones de la semana 1 se confirmaron durante la implementación y no requirieron un experimento aparte: el formulario propio con Cognito y cliente confidencial (ADR-005, User Pool `hindama-dev` probado de punta a punta el 2026-11-04) y Row-Level Security con `set_config` en SQLAlchemy asíncrono (ADR-013, cubierto por las pruebas de integración del backend).

---

## 2. PT-01: Guardia SSRF con IP fijada (ADR-008)

- **Fecha:** 2026-11-05
- **Entorno:** macOS, Python 3.12, httpx 0.28.1, httpcore 1.0.9, OpenSSL 3.5.5. Peticiones reales por Internet a `example.com`, `httpbin.org` y `badssl.com`. Se reutilizó `is_blocked` de `hindama-backend/src/hindama/core/destinations.py`.

### 2.1 Por qué se hizo

Hindama envía peticiones a URLs que controla el usuario: la verificación de propiedad, la descarga del contrato OpenAPI y, sobre todo, los miles de peticiones de los módulos de prueba. Eso la expone a **SSRF** (*Server-Side Request Forgery*): un usuario malicioso podría usar la plataforma para alcanzar destinos internos, como el servicio de metadatos de AWS (`169.254.169.254`), que entrega credenciales de la instancia.

Validar la URL al registrarla no basta, por dos ataques conocidos:

- **DNS rebinding:** el dominio resuelve a una IP pública cuando se valida y a una IP interna cuando se conecta. Si el cliente HTTP vuelve a resolver el nombre, se conecta al destino interno.
- **Redirecciones:** el servidor del usuario responde `302 Location: http://169.254.169.254/…` y el cliente la sigue.

ADR-008 decide resolver el nombre **una sola vez**, validar todas las IP y **conectar a esa IP exacta**. Validar las redirecciones salto por salto. El problema técnico es que, al conectar a una IP, TLS debe seguir enviando el nombre original (SNI) y validando el certificado contra ese nombre. Si no, o se rompe HTTPS, o se desactiva la validación del certificado, lo que abre otra falla. httpx no documenta esta combinación.

### 2.2 Qué resolvía

| Si la prueba fallaba | Consecuencia |
| --- | --- |
| No se puede fijar la IP con httpx | Plan B: proxy de salida (Smokescreen), otro servicio que desplegar y operar en la EC2 de 2 GB |
| Se descubre tarde, ya con el motor escrito | Rehacer `safe_http` y todo lo que lo usa en la semana 3 |

**Pregunta:** ¿puede httpx conectarse a una IP ya validada, conservando el `Host` y el SNI originales, validando el certificado contra el nombre original, sin una segunda resolución de DNS y sin parchear partes frágiles de la biblioteca?

**Criterio de éxito:** los escenarios de TLS, rebinding, redirecciones, tiempos de espera y tamaño se comportan como se espera, usando interfaces públicas de httpx/httpcore.

### 2.3 Enfoques evaluados

**E1: reescribir la URL a la IP y usar la extensión `sni_hostname`.** La petición se envía a `https://<IP>/…` con la cabecera `Host` original y la extensión pública `sni_hostname` de httpcore, que indica el nombre para el SNI y la validación del certificado.

```python
pinned = original.copy_with(host=str(ip))
request = client.build_request(
    "GET", pinned,
    headers={"Host": original.netloc.decode("ascii")},
    extensions={"sni_hostname": original.host},
)
```

**E2: *network backend* propio de httpcore.** La URL no cambia. El componente que abre el socket (`connect_tcp`) recibe el nombre y lo traduce a la IP ya validada; nunca consulta el DNS. httpcore sigue usando el nombre original para el SNI y el certificado.

```python
class PinnedBackend(httpcore.AsyncNetworkBackend):
    async def connect_tcp(self, host, port, timeout=None, **kwargs):
        ip = self.pins.get(host)           # IP validada antes de la petición
        if ip is None:
            raise httpcore.ConnectError(f"host sin IP fijada: {host}")
        return await self._inner.connect_tcp(str(ip), port, timeout=timeout, **kwargs)
```

Sobre los dos enfoques se montó una guardia mínima (`guarded_get`) con los pasos de ADR-008: host igual al verificado, resolución y validación en cada salto, IP fijada, `follow_redirects=False` con un máximo de 3 redirecciones, tiempos de espera y lectura en *stream* con corte por tamaño.

### 2.4 Escenarios y resultados

**TLS con la IP fijada**

| Caso | Situación | Cómo se simuló | Esperado | Obtenido |
| --- | --- | --- | --- | --- |
| A1 | API legítima por HTTPS (E1) | `example.com` fijado a su IP real | 200, TLS contra `example.com` | ✅ 200; conexión TCP a `104.20.23.154`, handshake con SNI `example.com` |
| A2 | Lo mismo con E2 | Igual | 200 | ✅ 200 |
| A3 | La IP fijada pertenece a otro servidor (E1) | `example.com` fijado a la IP de `httpbin.org` | Rechazo TLS | ✅ `CERTIFICATE_VERIFY_FAILED: Hostname mismatch` |
| A4 | Lo mismo con E2 | Igual | Rechazo TLS | ✅ Mismo rechazo |
| A5 | Certificado de otro nombre | `wrong.host.badssl.com` | Rechazo TLS | ✅ `Hostname mismatch` |
| A6 | Certificado vencido | `expired.badssl.com` | Rechazo TLS | ✅ `certificate has expired` |
| A7 | Certificado autofirmado | `self-signed.badssl.com` | Rechazo TLS | ✅ `self-signed certificate`. En una corrida dio *timeout* por lentitud de badssl.com (curl tardó 4.4 s en conectar); se repitió 3 veces y siempre se rechazó |

**DNS rebinding y nombres que apuntan a la red interna**

| Caso | Situación | Cómo se simuló | Esperado | Obtenido |
| --- | --- | --- | --- | --- |
| B1 | DNS rebinding | Resolver falso: la 1.ª respuesta es la IP real de `example.com`, las siguientes `127.0.0.1` | Una sola resolución; conexión a la IP validada | ✅ 1 resolución; la conexión TCP fue a `104.20.23.154` |
| B2 | Nombre público que resuelve a loopback | `localtest.me` (DNS real → `127.0.0.1`) | Bloqueo antes de conectar | ✅ Bloqueado |
| B3 | Nombre público que resuelve a metadatos de AWS | `169.254.169.254.nip.io` (DNS real → `169.254.169.254`) | Bloqueo antes de conectar | ✅ Bloqueado |

**Redirecciones**

| Caso | Situación | Cómo se simuló | Esperado | Obtenido |
| --- | --- | --- | --- | --- |
| C1 | Redirecciones normales en la misma API | `httpbin.org/redirect/2` | Se siguen | ✅ 200 tras 3 peticiones, cada una resuelta y validada |
| C2 | Cadena larga de redirecciones | `httpbin.org/redirect/5` | Corte al pasar de 3 | ✅ Cortado |
| C3 | Redirección en el mismo host con DNS que cambia a los metadatos en el 2.º salto | `httpbin.org/redirect/1` con un resolver que devuelve la IP real y luego `169.254.169.254` | Bloqueo en el 2.º salto | ✅ Bloqueado en el 2.º salto |
| C4 | Redirección a otro dominio | `httpbin.org/redirect-to?url=https://example.com/` | Bloqueo (fuera del host verificado) | ✅ Bloqueado |

> **Rediseño de C3.** La primera versión pedía a httpbin.org redirigir directamente a `http://169.254.169.254/…`. httpbin.org respondió `403 Forbidden redirect target: redirect target is an internal address`: el servicio de pruebas tiene su propia protección, así que el caso no probaba la guardia. Se reemplazó por el ataque realista de arriba. La redirección directa a una IP literal queda cubierta por la regla de C4, porque una IP no es el host verificado.

**Tiempos de espera y tamaño**

| Caso | Situación | Cómo se simuló | Esperado | Obtenido |
| --- | --- | --- | --- | --- |
| D1 | API que nunca termina de responder | `httpbin.org/delay/10` con lectura máxima de 3 s (en producción, 15 s) | `ReadTimeout` | ✅ `ReadTimeout` |
| D2 | Respuesta enorme | `httpbin.org/bytes/102400` (100 KiB) con límite de 64 KiB | Corte por tamaño sin leer todo | ✅ Cortada al pasar de 64 KiB |

**Reutilización de conexiones (hallazgo)**

| Caso | Situación | Cómo se simuló | Esperado | Obtenido |
| --- | --- | --- | --- | --- |
| E1 | Dos hosts en la misma IP, un solo cliente (E1) | `example.com` y luego `www.example.com` | Observar handshakes | ⚠️ Un solo handshake (SNI `example.com`); la 2.ª petición usó la conexión de la 1.ª |
| E2 | Lo mismo, con un 2.º host cuyo certificado no corresponde (E1) | `example.com` y luego `httpbin.org` fijado a la IP de `example.com` | Rechazo TLS | ❌ **La petición a `httpbin.org` se envió sin validar su certificado** (respondió 403 el servidor de `example.com`) |
| E3 | Mismo escenario con E2 | Igual, con el *network backend* | Rechazo TLS | ✅ Handshake nuevo para `httpbin.org`, rechazado |
| E4 | E2 integrado a httpx | Reemplazando el pool interno del transporte de httpx | 200 y URL original | ✅ 200; la URL registrada en la respuesta es `https://example.com/`, no la IP |

**Total:** 20 escenarios; 19 con el resultado esperado. El único que no, E2, es el hallazgo descrito abajo.

### 2.5 Hallazgos

1. **Fijar la IP sin romper TLS es posible con interfaces públicas.** Los dos enfoques validan el certificado contra el nombre original y rechazan certificados ajenos, vencidos, autofirmados o de otro nombre. No hace falta proxy de salida.
2. **El DNS rebinding queda neutralizado:** el nombre se resuelve una sola vez por petición y el socket se abre a la IP validada, comprobado con la traza de httpcore.
3. **E1 tiene un riesgo real de reutilización de conexiones.** httpcore agrupa las conexiones por destino (esquema, host, puerto). En E1 el destino es la IP, así que dos nombres que comparten IP, algo común detrás de una CDN como Cloudflare, comparten la conexión TLS y **el certificado del segundo nunca se valida**. En E2 el destino sigue siendo el nombre, así que cada host tiene su propio handshake.
4. **E2 conserva la URL original** en la petición y la respuesta. Las evidencias y los registros muestran `https://api.cliente.com/…` y no una IP, lo que hace falta para RF-63 a RF-67.
5. **Costo de E2:** el transporte de httpx no acepta un *network backend* propio. E4 lo logró reemplazando un atributo privado (`_pool`), que puede romperse al actualizar httpx.

### 2.6 Decisión

- `safe_http` usa **E2**: un *network backend* propio de httpcore que traduce el host a la IP validada.
- Para no depender del atributo privado de httpx, `safe_http` implementa **su propio transporte de httpx** (`httpx.AsyncBaseTransport`) sobre `httpcore.AsyncConnectionPool(network_backend=…)`, con interfaces públicas de ambas bibliotecas. Las versiones de httpx y httpcore quedan fijadas en `uv.lock` y la prueba de rechazo de certificados corre en la CI.
- **Defensa en profundidad:** cada cliente de `safe_http` queda atado a un solo host (el verificado del proyecto, o el de la URL en la importación de contratos). Aunque E2 ya evita el problema del hallazgo 3, un cliente nunca mezcla hosts.
- El plan B (Smokescreen) no es necesario. Sigue siendo posible agregarlo después sin cambiar los módulos.

### 2.7 Qué deben cubrir las pruebas de `safe_http` (tarea 2.1)

Los escenarios A–E se convierten en pruebas automáticas, sin depender de Internet: un servidor TLS local con certificados de prueba y resolvers falsos. Además:

- La conexión a un host sin IP fijada falla (no hay resolución implícita).
- Ninguna parte del código usa httpx directamente fuera de `safe_http` (regla de lint, ADR-008).
- Cada bloqueo queda registrado en la bitácora (RF-81) cuando exista el catálogo de acciones.

### 2.8 Limitaciones

- No se probó IPv6 de punta a punta ni HTTP/2. El backend en AWS sale por IPv4 (ADR-004) y la guardia rechaza si cualquiera de las IP resueltas está bloqueada, incluidas las IPv6.
- Los escenarios dependen de servicios públicos (`example.com`, `httpbin.org`, `badssl.com`), que pueden cambiar o fallar; por eso las pruebas definitivas serán locales.
- La IP propia de Hindama (ADR-008, paso 2) no se probó aquí porque aún no existe la IP elástica; `is_blocked` ya la contempla y tiene pruebas unitarias.

---

## 3. PT-02: Cola asíncrona, `arq` contra `SAQ` (ADR-012)

- **Fecha:** 2026-11-05
- **Entorno:** macOS, Python 3.12, Redis 7.4 en Docker (contenedor temporal), arq 0.28.0, SAQ 0.26.5, redis-py 5.3.1. Cada worker corrió en su propio proceso; los momentos de cada trabajo se anotaron en Redis con la hora del sistema para medir desde fuera.

### 3.1 Por qué se hizo

Cuando el analista pulsa «Ejecutar pruebas», la ejecución no puede correr dentro de la petición HTTP: dura minutos. Entra a una **cola** en Redis y la toma el **motor** (`scanner`), un proceso aparte. ADR-012 decidió un motor asíncrono que atiende varias ejecuciones a la vez en un solo proceso, porque la EC2 del backend tiene 2 GB y debe soportar 10 ejecuciones simultáneas (RNF-04). Dejó abierta la biblioteca de cola: `arq` o `SAQ`.

Los requerimientos que la cola debe cumplir son exigentes:

| Requerimiento | Qué pide |
| --- | --- |
| RNF-04 | 10 ejecuciones simultáneas en una máquina pequeña |
| RF-52 | Cancelar en menos de 5 s, aunque haya una petición HTTP esperando respuesta |
| RN-06 | Al cancelar, limpiar los recursos que la plataforma creó en la API probada |
| RF-47 | Tiempo máximo por ejecución |
| RNF-18, CU-23 | Si el motor se cae, ninguna ejecución queda «En curso» para siempre |

### 3.2 Qué resolvía

Ambas bibliotecas prometen estas funciones, pero la cancelación a mitad de una espera de red y la recuperación tras una caída son justo donde suelen fallar. Si se elegía mal, se descubriría con el motor y los 7 módulos ya escritos encima.

**Pregunta:** ¿cuál cumple cancelación en menos de 5 s con limpieza, tiempo máximo por trabajo, reintentos, 10 trabajos por proceso y recuperación tras una caída, con mantenimiento activo?

**Criterio de éxito:** los cinco escenarios dan el resultado esperado y la biblioteca tiene mantenimiento activo y sin vulnerabilidades conocidas.

### 3.3 Cómo se montó

Un trabajo simulado (`scan`) imita una ejecución de pruebas:

```python
async def scan_body(run_id, seconds, touch=None):
    await mark(run_id, "start")
    try:
        while not_finished:
            await asyncio.sleep(0.5)     # «esperando la respuesta HTTP de la API probada»
            if touch: await touch()      # latido / progreso (RF-51)
        await mark(run_id, "done")
    except asyncio.CancelledError:
        await mark(run_id, "cancelled")
        await asyncio.sleep(1.0)         # limpieza de recursos creados (RN-06)
        await mark(run_id, "cleanup_done")
        raise
```

`asyncio.sleep` representa la espera de red: para la cola es lo mismo que esperar a httpx, porque ambas son esperas asíncronas que se pueden cancelar. Un script externo encola trabajos, pide cancelaciones, mata el worker y lee los momentos anotados.

### 3.4 Escenarios y resultados

| Caso | Situación | Cómo se simuló | Esperado | arq 0.28.0 | SAQ 0.26.5 |
| --- | --- | --- | --- | --- | --- |
| S1 | Más ejecuciones que el límite | 12 trabajos de 4 s, límite 10 por proceso | 10 a la vez, 2 esperan; ≈8 s | ✅ máx. 10 a la vez; 12/12 en 8.6 s; worker 33 MB | ✅ máx. 10 a la vez; 12/12 en 8.1 s; worker 34 MB |
| S2 | El analista cancela una ejecución que espera una respuesta | Trabajo de 30 s, cancelado a los 2 s (3 repeticiones) | < 5 s y limpieza ejecutada | ✅ 0.45–0.49 s; limpieza completa en 1.5 s | ✅ 0.90–0.97 s; limpieza completa en 1.9–2.0 s; estado `aborted` |
| S3 | La ejecución excede su tiempo máximo | Trabajo de 30 s con máximo de 3 s | Corte ≈3 s, limpieza, estado fallido | ✅ corte a 3.0 s; limpieza; fallido | ✅ corte a 3.0 s; limpieza; fallido (ver hallazgo 4) |
| S4 | Falla transitoria | La 1.ª vez lanza una excepción, la 2.ª funciona | Se puede reintentar | ⚠️ Una excepción común **no** se reintenta; solo si el código lanza `arq.Retry` | ✅ Se reintenta cualquier excepción si `retries` lo permite (configurable por trabajo) |
| S5 | El motor se cae con una ejecución en curso | `SIGKILL` al worker y se levanta otro | Detectarla y dejarla en estado final, sin re-ejecución silenciosa | ⚠️ Fallida («max 1 retries exceeded») **310 s después**; no se re-ejecutó | ✅ Detectada por latido y barrido: `aborting` a los 5.6 s y `aborted` a los 10.6 s; no se re-ejecutó |

**Mantenimiento y seguridad**

| | arq | SAQ |
| --- | --- | --- |
| Última versión | 0.28.0 (2026-04-16) | 0.26.5 (2026-10-29) |
| Versiones en los últimos 2 años | 3 | 34 |
| Estado declarado | **«In maintenance only mode»** (aviso en su página de PyPI, issue #510) | Activo |
| redis-py admitido | `<6` (la versión actual es la 7) | `<8` |
| Vulnerabilidades conocidas (`pip-audit`) | Ninguna | Ninguna |

### 3.5 Incidencias durante el experimento

Se anotan porque afectaron mediciones y la forma correcta de usar las bibliotecas:

1. **Worker de arq mal construido.** La primera versión creaba `arq.Worker` antes de `asyncio.run()`. arq toma el *event loop* al construirse, así que los trabajos quedaban marcados «en curso» en Redis pero nunca se ejecutaban, sin ningún error. Se corrigió usando `worker.run()`, la forma documentada.
2. **Worker residual.** Ese worker defectuoso siguió vivo e ignoró `SIGTERM`, porque su manejador de señales estaba en el loop que nunca corrió. Siguió reclamando trabajos y contaminó dos corridas: algunos trabajos aparecían «en curso» sin ejecutarse nunca. Se terminó con `SIGKILL`, se verificó que no quedara ningún proceso ni cliente conectado a Redis, y todos los resultados de la tabla vienen de corridas limpias.
3. La espera de S5 en arq se amplió de 75 s a 150 s y después hasta que expiró la marca, para ver el desenlace final.

La lección para el motor real: un worker que no procesa pero sigue conectado puede «secuestrar» ejecuciones. El latido de SAQ y la reconciliación de CU-23 deben cubrirlo, y el despliegue debe vigilar que solo existan los workers esperados.

### 3.6 Hallazgos

1. **Las dos cumplen la concurrencia y la cancelación.** 10 trabajos por proceso con ~33 MB de memoria, y cancelación muy por debajo de 5 s, con la limpieza asíncrona completa. arq cancela más rápido (≈0.5 s contra ≈1 s) porque revisa cada 0.5 s; SAQ, cada segundo. Ambos tiempos cumplen RF-52 con margen.
2. **Recuperación tras una caída: la diferencia decisiva.** arq marca cada trabajo «en curso» durante el tiempo máximo **más largo de cualquier función registrada** más 10 s. Con ejecuciones que pueden durar 30 minutos, una ejecución huérfana quedaría «En curso» más de 30 minutos. SAQ usa un **latido**: el trabajo actualiza su marca y un barrido periódico detecta las que dejaron de latir. Lo detectó en 10 s, y el intervalo es configurable.
3. **Mantenimiento.** arq está oficialmente en modo solo mantenimiento y no admite redis-py 6 ni 7. Elegirlo ataría el proyecto a dependencias viejas.
4. **SAQ espera poco la limpieza al vencer el tiempo máximo.** En S3, SAQ avisó «did not finish cancellation in time»: por defecto solo espera 1 s (`cancellation_hard_deadline_s`) a que termine la limpieza. Aquí la limpieza alcanzó a completarse, pero una limpieza real (borrar recursos creados en la API probada, RN-06) puede tardar más. Al cancelar por el analista, SAQ sí espera a que termine.
5. **Reintentos.** Para Hindama, una ejecución **no** debe reintentarse sola: repetiría peticiones contra la API del usuario. Las dos lo permiten (`retries=1` en SAQ, `max_tries=1` en arq). SAQ además permite reintentar trabajos auxiliares cortos sin código especial.

### 3.7 Decisión

**Se elige SAQ.** Configuración inicial para el motor:

| Parámetro | Valor | Por qué |
| --- | --- | --- |
| `concurrency` | 10 | RNF-04 |
| `retries` de las ejecuciones | 1 (sin reintento) | Una ejecución no se repite sola contra la API del usuario |
| `timeout` | Tiempo máximo de la ejecución (RF-47) | Corte automático |
| `heartbeat` | 15–30 s, actualizado con cada avance de progreso (RF-51) | Detectar el motor caído en segundos, no en minutos |
| `timers.sweep` | 10–15 s (por defecto 60 s) | Igual |
| `cancellation_hard_deadline_s` | Suficiente para la limpieza (≈30 s; se ajusta en la semana 3) | Que la limpieza de RN-06 termine también al vencer el tiempo máximo |

La base de datos sigue siendo la fuente de verdad del estado de una ejecución. El estado de SAQ (`aborted`, `failed`, etc.) se traduce al de `runs`. La reconciliación de CU-23 revisa las ejecuciones «En curso» sin trabajo vivo, como respaldo del barrido.

### 3.8 Limitaciones

- La red se simuló con `asyncio.sleep`. La cancelación de una petición httpx real se probará con `safe_http` en la semana 3, aunque para asyncio es el mismo mecanismo.
- No se midió con 2 procesos de worker ni con la memoria de los módulos reales; la prueba de carga con 10 ejecuciones contra el laboratorio (tarea 3.5) lo cubre.
- No se probó la persistencia de Redis (AOF, ADR-003) ante un reinicio de Redis.

## 4. PT-03: OpenAPI 3.1 en `oasdiff` y Schemathesis (ADR-016)

- **Fecha:** 2026-11-05
- **Entorno:** oasdiff 1.35.0 (binario oficial, checksum SHA-256 verificado contra el publicado), Schemathesis 4.33.1, contrato `openapi.yaml` v0.2.0 (OpenAPI 3.1.0), backend en `develop` (`15aa9ea`). La API real corrió con PostgreSQL 16 (base `hindama_test`, usuario `hindama_api` con RLS) y con el User Pool y el DNS falsos de las pruebas del backend.

### 4.1 Por qué se hizo

El frontend y el backend se construyen en paralelo y se encuentran en el contrato (`openapi.yaml`). ADR-016 decidió verificar automáticamente que el backend cumpla el contrato con dos herramientas:

- **`oasdiff`**, verificación **estática**: compara el OpenAPI que genera FastAPI con el contrato.
- **Schemathesis**, verificación **dinámica**: genera cientos de peticiones a partir del contrato contra la API en ejecución y valida cada respuesta. Gracias a `additionalProperties: false`, también detecta si un endpoint devuelve un campo que no debe, como un dato interno o una credencial (RN-11).

Dejó una duda abierta: FastAPI genera **OpenAPI 3.1**, y no estaba confirmado que estas herramientas lo soporten bien. Mientras tanto, el backend usa una prueba de contrato propia en Python.

### 4.2 Qué resolvía

Esta prueba no afecta cómo Hindama evalúa las APIs de los usuarios: es control de calidad de la API **de la propia plataforma**. Si el backend se desvía del contrato, el frontend se rompe en silencio. Y si un endpoint devuelve datos de más, la plataforma de seguridad tendría una fuga propia.

**Preguntas:** ¿leen las dos herramientas OpenAPI 3.1? ¿Detectan desviaciones reales sin ahogarlas en falsos positivos? ¿Aportan algo frente a la prueba de contrato propia?

**Criterio de éxito:** cada herramienta lee el contrato, detecta desviaciones introducidas a propósito y su ruido se puede controlar con configuración.

### 4.3 Cómo se montó

1. **Estático.** Se exportó `app.openapi()` del backend y se comparó con el contrato usando `oasdiff diff` y `oasdiff breaking`. Después se introdujeron **7 desviaciones** a propósito en el OpenAPI generado (M1–M7) y se comprobó quién las detecta: `oasdiff` o la prueba propia (`tests/contract/test_openapi_contract.py`).
2. **Dinámico.** Se levantó la API real en `127.0.0.1:8765` con un token válido de un analista que ya aceptó los términos. Se corrió `schemathesis run openapi.yaml --checks all -n 25 --seed 20261105`, con todas sus fases (ejemplos, cobertura, *fuzzing* y pruebas con estado). Después se repitió con un *middleware* que agrega a `GET /me` un campo interno (`cognito_sub`), para simular una fuga.

### 4.4 Resultados: verificación estática

**Lectura de OpenAPI 3.1:** ✅ `oasdiff` lee el contrato y el documento generado, incluidos `type: [string, "null"]` y `const`.

**Comparación directa (sin mutaciones):** el código cumple el contrato, pero `oasdiff` reporta diferencias que son de representación, no de comportamiento:

| Tipo de diferencia | Cuántas | ¿Real? |
| --- | --- | --- |
| Títulos, descripciones y ejemplos | Cientos de líneas | No. Se filtran con `--exclude-elements description,examples,title,summary` |
| Respuestas de error que FastAPI no declara (401, 403, 429, 503…) | 27 | No. FastAPI solo documenta las respuestas que se declaran en el decorador |
| `anyOf: [x, null]` (Pydantic) frente a `type: [x, "null"]` (contrato) | 16 | No. Son equivalentes |
| `const: ok` frente a `enum: [ok]` | 1 | No. Equivalentes |
| 422 documentado con el formato por defecto de FastAPI (`application/json`, `detail: [...]`) en lugar de Problem Details | 6 operaciones | **Sí, en la documentación generada:** la API responde Problem Details (Schemathesis lo confirmó), pero su OpenAPI generado lo describe mal |
| 6 operaciones del contrato aún no implementadas | 6 | Esperado (contrato primero) |

`oasdiff breaking` marcó **83 errores**, todos derivados de los falsos positivos anteriores (por ejemplo, «se amplió la lista de tipos agregando `null`»).

**Desviaciones introducidas a propósito**

| Caso | Desviación | Prueba propia | `oasdiff` |
| --- | --- | --- | --- |
| M1 | Campo extra `cognito_sub` en la respuesta de `GET /me` (fuga) | ✅ Detecta | ✅ Detecta |
| M2 | Se quita el campo obligatorio `role` | ✅ | ✅ |
| M3 | `id` cambia de `string` a `integer` | ✅ | ✅ |
| M4 | `POST /projects` responde 200 en lugar de 201 | ✅ | ✅ |
| M5 | Endpoint no documentado `GET /debug/config` | ✅ | ✅ |
| M6 | `page_size` acepta hasta 1000 en lugar de 100 | ✅ | ✅ |
| M7 | Una respuesta 401 sin formato Problem Details | ❌ No detecta (solo compara respuestas 2xx) | ✅ |

### 4.5 Resultados: verificación dinámica (Schemathesis)

**Lectura de OpenAPI 3.1:** ✅ «Specification: Open API 3.1.0». Se probaron las 14 operaciones con **710 peticiones generadas en 3.2 s**. Schemathesis infirió 27 enlaces entre operaciones para las pruebas con estado (por ejemplo, crear un proyecto y luego consultarlo).

Encontró 10 fallas únicas, que se clasificaron así:

| Falla | Petición | Clasificación |
| --- | --- | --- |
| **500 en `GET /projects`** | `?page=9223372036854775808` | **Error real del backend.** El número de página se convierte en un `OFFSET` que no cabe en `int64` y PostgreSQL lo rechaza (`value out of int64 range`). El contrato no fija un máximo para `page` |
| **500 en `POST /projects`** | Nombre con el carácter NUL (`\u0000`) | **Error real del backend.** PostgreSQL no admite NUL en texto; la API debe rechazarlo con 422. Se confirmó con `curl` |
| **`Allow` incorrecto en 405** | `OPTIONS /projects` y `OPTIONS /projects/{id}` | **Error real menor.** La respuesta 405 envía `Allow: GET` aunque la ruta también acepta POST, PATCH o DELETE (RFC 9110 pide listar todos) |
| 422 a datos válidos según el esquema | Confirmación vacía al borrar, versión de términos arbitraria, URL con una etiqueta de más de 63 caracteres | **Esperado.** Son reglas de negocio que un esquema no expresa (RN-12, confirmación por nombre, RF-11). Se configuran como respuestas aceptadas. La confirmación vacía se puede expresar con `minLength: 1` en el contrato |
| Recurso recién creado no encontrado | `POST /projects` → `POST /projects/{id}/contracts` responde 404 | **Esperado.** La operación de contratos aún no está implementada |

**Fuga simulada:** con el campo interno `cognito_sub` agregado a `GET /me`, Schemathesis falló con `ST108 Response violates schema: Additional properties are not allowed ('cognito_sub' was unexpected)`. Detecta la fuga **en la respuesta real**, aunque el OpenAPI generado no cambie, algo que ninguna comparación estática puede ver.

### 4.6 Incidencias

- El lanzador del experimento hizo una petición inicial con `asyncio.run()` antes de arrancar uvicorn. Las conexiones de la base quedaron ligadas a ese primer *event loop* y la primera petición a `/health` respondió 503 («Event loop is closed»). Es un defecto del lanzador, no del backend; no afectó las mediciones posteriores.
- La primera versión de M6 buscaba un parámetro `limit`, que no existe: la paginación usa `page_size`. Se corrigió y se repitió.

### 4.7 Hallazgos

1. **Las dos herramientas leen OpenAPI 3.1.** El riesgo que planteaba ADR-016 no se materializó.
2. **`oasdiff` no sirve tal cual para comparar lo generado contra el contrato.** Detecta todo lo que detecta la prueba propia, y además los cambios en las respuestas de error. Pero mezcla las desviaciones reales con decenas de diferencias de representación entre Pydantic y el contrato. Para usarlo como compuerta de la CI habría que normalizar los documentos antes, que es exactamente lo que ya hace la prueba propia.
3. **`oasdiff` sí encaja en su uso original:** comparar **dos versiones del contrato** (por ejemplo, `main` contra el PR en `hindama-docs`) para avisar al frontend de cambios incompatibles. Ahí no hay diferencias de representación, porque los dos documentos están escritos a mano con las mismas reglas.
4. **Schemathesis aporta lo que ninguna comparación estática puede ver.** En 3 segundos encontró **tres errores reales** que las 247 pruebas del backend no habían detectado, y confirmó que detecta fugas de campos en respuestas reales (RN-11).
5. **La prueba propia tiene un punto ciego:** solo compara las respuestas 2xx. El 422 mal documentado y el formato de las respuestas de error pasan sin aviso.

### 4.8 Decisión

| Herramienta | Uso | Dónde |
| --- | --- | --- |
| Prueba de contrato propia | Se mantiene como compuerta estática. Se amplía para comparar también el tipo de contenido y el esquema de las respuestas de error declaradas | CI del backend |
| **Schemathesis** | **Se adopta.** Corre contra la API levantada con PostgreSQL, todas las fases y semilla fija. Las reglas de negocio (422 esperados) se configuran como respuestas aceptadas, y las operaciones aún no implementadas se excluyen hasta que existan | CI del backend (trabajo de integración) |
| `oasdiff` | No se usa para comparar lo generado contra el contrato. Se propone `oasdiff breaking` entre `main` y cada PR del contrato, para marcar cambios incompatibles para el frontend | CI de `hindama-docs` (propuesta) |

**Correcciones derivadas para el backend** (cada una con su prueba de regresión):

1. Fijar un máximo para `page` en el contrato y en la validación, o limitar el `OFFSET`, para que una página enorme responda 422 y no 500.
2. Rechazar con 422 los caracteres de control (al menos NUL) en los campos de texto.
3. Listar todos los métodos de la ruta en la cabecera `Allow` de las respuestas 405.
4. Documentar el 422 con Problem Details en el OpenAPI generado (`api/openapi.py`).
5. Agregar `minLength: 1` a `confirmation` en el contrato.

### 4.9 Limitaciones

- Schemathesis corrió con un solo usuario. El aislamiento entre propietarios (404 para recursos ajenos, RN-02) lo cubren las pruebas de integración del backend, no esta prueba.
- Con 6 operaciones sin implementar, las pruebas con estado no alcanzaron la lógica de contratos y verificación. Se repetirá cuando existan.
- `-n 25` es una muestra pequeña; en la CI conviene más ejemplos, con un tiempo acotado.
