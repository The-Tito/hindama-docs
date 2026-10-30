---
documento: Requerimientos de software
proyecto: Hindama
version: 1.0
fecha: 2026-10-30
estado: vigente
fuente_word: Documento_de_requerimientos_Hindama_v1.0.docx
---

# Documento de requerimientos de software — Hindama v1.0

## 1. Propósito

Este documento especifica los requerimientos de software de **Hindama** (palabra estonia que significa «evaluar»), versión 1.0: una plataforma web para verificar la seguridad de APIs REST a partir de su contrato OpenAPI 3 y dar seguimiento a cada falla encontrada hasta su corrección.

El documento cubre la totalidad de la versión 1.0: cuentas y roles, proyectos, verificación de propiedad, importación del contrato, identidades, recursos y política, los siete módulos de prueba, la ejecución y el seguimiento de hallazgos, los reportes, el panel de administración y la bitácora. Quedan fuera la capa de inteligencia artificial y el proyecto de demostración, que se especificarán en una versión posterior (sección 11).

## 2. Alcance del producto / Software

**Objetivo general.** Construir una aplicación web integrada con una API RESTful propia que permita a desarrolladores verificar los controles de autenticación, autorización, configuración, consumo de recursos e inyección SQL de sus APIs REST, con el fin de detectar, clasificar y dar seguimiento a sus vulnerabilidades hasta verificar su corrección.

**Beneficios.**

- Detección temprana de fallas de seguridad antes o después de publicar una API, cuando corregirlas cuesta menos.
- Pruebas guiadas por el contrato OpenAPI y por una política de acceso explícita, lo que permite detectar fallas de autorización que un escáner genérico no distingue.
- Evidencia accionable: cada hallazgo incluye la petición que lo reproduce, su clasificación OWASP y CWE, y una recomendación de corrección.
- Ciclo completo de gestión de vulnerabilidades: detección, corrección, re-testeo y cierre.

**Objetivos y metas medibles.**

- Reconocer el 100 % de las operaciones de los contratos de las APIs de laboratorio (VAmPI y mini API propia).
- Detectar al menos el 90 % de las fallas del catálogo de laboratorio en las versiones vulnerables, sin falsos positivos de severidad crítica o alta en las versiones seguras.
- Bloquear el 100 % de los intentos de probar destinos no verificados o direcciones internas.
- Producir resultados idénticos en dos ejecuciones consecutivas sobre el mismo estado de una API.
- Lograr que al menos 4 de 5 usuarios de prueba configuren un proyecto y completen una ejecución sin asistencia.

Este alcance se deriva de la propuesta de proyecto del 9 de octubre de 2026 y de la definición de funcionalidades del 30 de octubre de 2026 (sección 3), que amplía la propuesta de un laboratorio cerrado a APIs reales de los usuarios.

## 3. Referencias

| Título | Autor | Versión / fecha | Ubicación |
| --- | --- | --- | --- |
| Propuesta de proyecto: AuthzCheck | Equipo del proyecto | 9 de octubre de 2026 | Proyecto API-TESTER (authzcheck/propuesta_entrega_mvp_final.md, archivado) |
| Definición de funcionalidades — Hindama | Equipo del proyecto | 30 de octubre de 2026 | https://claude.ai/artifact/2P7XpKAW3C127ouy3wr1HH |
| OWASP API Security Top 10 | OWASP Foundation | 2023 | https://owasp.org/API-Security/editions/2023/en/0x11-t10/ |
| Common Weakness Enumeration (CWE) | MITRE | Versión vigente | https://cwe.mitre.org |
| OpenAPI Specification | OpenAPI Initiative | 3.0 y 3.1 | https://spec.openapis.org/oas/latest.html |
| Amazon Cognito Developer Guide | Amazon Web Services | Versión vigente | https://docs.aws.amazon.com/cognito/ |
| VAmPI: The Vulnerable API | erev0s | Versión vigente | https://github.com/erev0s/VAmPI |
| ISO/IEC/IEEE 29148: Requirements engineering | ISO/IEC/IEEE | 2018 | https://www.iso.org/standard/72089.html |

## 4. Funcionalidades del producto

La versión 1.0 se compone de quince funcionalidades. Su detalle y sus requerimientos funcionales se documentan en la sección 7.

| ID | Funcionalidad | Resumen |
| --- | --- | --- |
| F-01 | Gestión de cuentas y autenticación | Registro, inicio y cierre de sesión, verificación de correo y recuperación de contraseña mediante Amazon Cognito. |
| F-02 | Gestión de proyectos | Crear, consultar, editar y eliminar proyectos; cada proyecto agrupa todo lo relacionado con una API. |
| F-03 | Verificación de propiedad de la API | Comprobar que el analista controla el dominio de la API antes de permitir cualquier prueba. |
| F-04 | Importación y análisis del contrato OpenAPI | Cargar el contrato OpenAPI 3 y extraer operaciones, parámetros, esquemas y seguridad declarada. |
| F-05 | Gestión de identidades de prueba | Registrar las cuentas de prueba de la API del analista y la forma de autenticarse con cada una. |
| F-06 | Gestión de recursos por identidad | Descubrir y registrar qué objetos de la API pertenecen a cada identidad. |
| F-07 | Definición de la política de acceso | Declarar quién debería poder ejecutar cada operación de la API. |
| F-08 | Configuración y ejecución de pruebas | Ejecutar un módulo individual o la prueba completa con límites, progreso en tiempo real y cancelación. |
| F-09 | Módulos de prueba de seguridad | Siete módulos que detectan fallas de autenticación, configuración, autorización, consumo de recursos e inyección SQL. |
| F-10 | Visualización de resultados y hallazgos | Resumen de la ejecución, matriz de acceso, lista y detalle de hallazgos con evidencia. |
| F-11 | Seguimiento y re-testeo de hallazgos | Estados del hallazgo entre ejecuciones e historial del proyecto hasta concluirlo. |
| F-12 | Generación de reportes | Reporte imprimible a PDF y exportación de hallazgos a Excel. |
| F-13 | Panel de administración | Estadísticas agregadas y anónimas de uso y de fallas frecuentes. |
| F-14 | Bitácora de auditoría | Registro y consulta de las acciones sensibles realizadas en la plataforma. |
| F-15 | Autenticación de dos factores | Segundo factor con código TOTP para las cuentas de la plataforma. |

## 5. Clases y características de usuarios

La plataforma tiene dos clases de usuario registrado y una de visitante. El analista es quien usa la mayor parte del sistema y con más frecuencia.

| Clase | Características | Frecuencia de uso | Funcionalidades |
| --- | --- | --- | --- |
| Analista | Desarrollador o equipo que construyó una API REST y quiere verificar su seguridad. Conoce HTTP, autenticación con tokens y OpenAPI; no necesita experiencia en pruebas de penetración. Solo accede a sus propios proyectos. | Alta: varias sesiones por proyecto, una por cada ciclo de corrección y re-testeo. | F-01 a F-12 y F-15 |
| Administrador | Integrante del equipo de Hindama. Supervisa el uso de la plataforma y las fallas frecuentes. No accede al contenido de los proyectos de los analistas. | Baja: consultas periódicas. | F-01, F-13, F-14 y F-15 |
| Visitante | Persona sin cuenta. Solo puede ver la página de inicio, registrarse o iniciar sesión. | Ocasional. | F-01 |

## 6. Entorno operativo

**Cliente.** Aplicación web que funciona en las dos últimas versiones de Google Chrome, Mozilla Firefox, Microsoft Edge y Safari, en Windows, macOS y Linux. Resolución mínima recomendada: 1366 × 768. En teléfonos y tabletas se pueden consultar resultados; la configuración está optimizada para escritorio.

**Servidor.** Componentes en contenedores Docker sobre Linux, desplegados en Amazon Web Services (AWS). Tanto el frontend como el backend completo se alojan en AWS:

- Frontend: Next.js (React con TypeScript) ejecutado como servidor Node.js en su propio contenedor. Se encarga de la interfaz y de la sesión del usuario; no contiene lógica de negocio.
- API de la plataforma y motor de pruebas: Python 3.12 con FastAPI y el cliente HTTP asíncrono httpx. Solo es accesible desde el servidor de Next.js, dentro de la red privada en AWS.
- Trabajos en segundo plano: Redis con RQ.
- Base de datos: PostgreSQL 16, con SQLAlchemy y migraciones Alembic.
- Identidad: Amazon Cognito.

**Sistemas con los que coexiste.** Las APIs de los analistas, accesibles por Internet desde el servidor de la plataforma; los servidores DNS públicos, para la verificación de propiedad; y el laboratorio de validación (VAmPI y la mini API propia en modo seguro y vulnerable), que se levanta con Docker Compose en el equipo de desarrollo.

El laboratorio de validación es una herramienta interna del equipo de desarrollo para medir la detección y los falsos positivos de los módulos de prueba. No se despliega en AWS ni está disponible para los usuarios en la versión 1.0.

## 7. Requerimientos funcionales

Los requerimientos se organizan por funcionalidad (sección 4). Cada uno tiene un identificador único RF-nn para su trazabilidad en el diseño y las pruebas.

### 7.1 Gestión de cuentas y autenticación (F-01)

**Descripción:** Permite a cualquier persona crear una cuenta de analista y acceder a la plataforma. La identidad de los usuarios se gestiona con Amazon Cognito; la plataforma no almacena contraseñas.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. El visitante elige «Crear cuenta» e introduce nombre, correo y contraseña.
2. El sistema envía un código de verificación al correo; el usuario lo introduce y la cuenta queda activa con rol de analista.
3. El usuario inicia sesión con correo y contraseña; el sistema lo dirige a su lista de proyectos.
4. Si olvida su contraseña, solicita recuperación y recibe un código por correo para definir una nueva.

**Requerimientos funcionales:**

- **RF-01.** El sistema permitirá registrar cuentas con nombre, correo electrónico y contraseña, y asignará el rol de analista a toda cuenta nueva.
- **RF-02.** El sistema exigirá verificar el correo con un código antes de permitir el primer inicio de sesión.
- **RF-03.** El sistema aplicará la política de contraseñas configurada en Cognito: mínimo 12 caracteres con mayúsculas, minúsculas, números y símbolos.
- **RF-04.** El sistema permitirá iniciar y cerrar sesión; al cerrar sesión eliminará la cookie de sesión y revocará los tokens en Cognito.
- **RF-05.** El sistema permitirá recuperar la contraseña mediante un código enviado al correo registrado.
- **RF-06.** Ante credenciales incorrectas, el sistema mostrará un mensaje genérico que no revele si el correo existe, y Cognito bloqueará temporalmente la cuenta tras intentos fallidos repetidos.
- **RF-07.** La API de la plataforma validará el token emitido por Cognito en cada petición y rechazará con código 401 las peticiones sin token o con token vencido o inválido.
- **RF-08.** El servidor de Next.js guardará los tokens de Cognito en una cookie de sesión cifrada con los atributos HttpOnly, Secure y SameSite=Lax, y los renovará antes de que venzan; el JavaScript del navegador nunca tendrá acceso a ellos.
- **RF-09.** El rol de administrador solo podrá asignarse desde la consola de Cognito por el equipo de Hindama; no existirá autoasignación desde la interfaz.

### 7.2 Gestión de proyectos (F-02)

**Descripción:** Un proyecto representa una API del analista y almacena su configuración, contrato, identidades, ejecuciones, hallazgos y reportes. Un analista puede tener varios proyectos.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. El analista elige «Nuevo proyecto».
2. Acepta los términos de uso responsable (solo la primera vez).
3. Introduce nombre, descripción y URL base de su API.
4. El sistema crea el proyecto en estado «Pendiente de verificación» y lo lleva a cargar el contrato y verificar la propiedad.
5. Desde la lista de proyectos puede abrir, editar o eliminar cualquiera de los suyos.

**Requerimientos funcionales:**

- **RF-10.** El sistema permitirá crear proyectos con nombre (obligatorio, máximo 100 caracteres), descripción (opcional, máximo 500 caracteres) y URL base (obligatoria).
- **RF-11.** El sistema validará que la URL base tenga formato válido, use HTTP o HTTPS, y no apunte a direcciones IP privadas, de loopback, de enlace local o de metadatos de nube; si no cumple, rechazará el registro indicando el motivo.
- **RF-12.** El sistema mostrará al analista únicamente sus propios proyectos, con nombre, estado de verificación, fecha de la última ejecución y número de hallazgos abiertos.
- **RF-13.** El sistema permitirá editar nombre y descripción en cualquier momento; si se cambia el dominio de la URL base, el proyecto volverá a «Pendiente de verificación».
- **RF-14.** El sistema permitirá eliminar un proyecto previa confirmación escrita del nombre; la eliminación borrará de forma permanente su contrato, identidades, credenciales, ejecuciones, hallazgos y reportes.
- **RF-15.** El sistema mostrará un dashboard por proyecto con el estado de verificación, los módulos disponibles según la configuración, la última ejecución y los hallazgos abiertos por severidad.
- **RF-16.** El sistema exigirá aceptar los términos de uso responsable antes de crear el primer proyecto y registrará la fecha de aceptación.

### 7.3 Verificación de propiedad de la API (F-03)

**Descripción:** Antes de enviar cualquier petición a una API, el sistema comprueba que el analista controla su dominio. Evita que la plataforma se use para atacar APIs de terceros.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. El sistema genera un código de verificación único para el proyecto.
2. El analista elige el método: publicar un archivo en una ruta conocida de su dominio o crear un registro DNS TXT.
3. El analista pulsa «Verificar»; el sistema consulta el archivo o el registro DNS.
4. Si el código coincide, el proyecto pasa a «Verificado» y se habilitan las pruebas; si no, se muestra qué se encontró y cómo corregirlo.

**Requerimientos funcionales:**

- **RF-17.** El sistema generará un código de verificación aleatorio y único por proyecto.
- **RF-18.** El sistema aceptará dos métodos de verificación: un archivo de texto publicado en «/.well-known/hindama-verificacion.txt» del dominio, o un registro DNS TXT en el dominio de la URL base.
- **RF-19.** El sistema no permitirá ejecutar ningún módulo de prueba mientras el proyecto no esté verificado.
- **RF-20.** El sistema volverá a comprobar la verificación antes de cada ejecución; si el código ya no está publicado, cancelará la ejecución y devolverá el proyecto a «Pendiente de verificación».
- **RF-21.** Si la verificación falla, el sistema indicará la causa: archivo no encontrado, contenido distinto, registro DNS ausente o error de conexión.

### 7.4 Importación y análisis del contrato OpenAPI (F-04)

**Descripción:** El contrato OpenAPI 3 es la fuente de conocimiento sobre la API: a partir de él se generan las pruebas.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. El analista sube un archivo JSON o YAML, o indica la URL donde se publica el contrato.
2. El sistema valida el documento y extrae sus operaciones.
3. El sistema muestra la lista de operaciones encontradas (método, ruta, parámetros y seguridad declarada) y los avisos de lo que no pudo interpretar.
4. Cuando la API cambia, el analista importa una nueva versión y el sistema muestra las operaciones agregadas, modificadas y eliminadas.

**Requerimientos funcionales:**

- **RF-22.** El sistema permitirá importar contratos OpenAPI 3.0 y 3.1 en formato JSON o YAML, por archivo (máximo 5 MB) o por URL.
- **RF-23.** El sistema resolverá las referencias internas «$ref» del contrato; no seguirá referencias a archivos o URLs externos.
- **RF-24.** El sistema extraerá de cada operación: método, ruta, parámetros de ruta, consulta, cabecera y cuerpo, esquemas de petición y de respuesta, y esquemas de seguridad declarados.
- **RF-25.** Si el documento no es OpenAPI 3 válido, el sistema rechazará la importación e indicará la línea o el campo con error. Si es Swagger 2, indicará que esa versión no está soportada.
- **RF-26.** El sistema conservará cada versión importada del contrato y mostrará las diferencias de operaciones respecto a la versión anterior.
- **RF-27.** El sistema advertirá si los servidores declarados en el contrato no coinciden con la URL base del proyecto, y siempre usará la URL base del proyecto para las pruebas.

### 7.5 Gestión de identidades de prueba (F-05)

**Descripción:** Las identidades son cuentas que el analista crea en su propia API, de preferencia en un entorno de pruebas. Permiten probar la API como distintas personas. La identidad anónima, sin credenciales, existe siempre.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. El analista elige «Agregar identidad» e indica un nombre (por ejemplo, «Usuario A») y el rol que tiene en su API.
2. Elige la forma de autenticación e introduce los datos correspondientes.
3. El sistema prueba la credencial con una petición a una operación protegida y muestra si funcionó.
4. La identidad queda guardada con la credencial cifrada y enmascarada.

**Requerimientos funcionales:**

- **RF-28.** El sistema permitirá registrar identidades con nombre, rol declarado (administrador, usuario u otro texto libre) y forma de autenticación.
- **RF-29.** El sistema soportará cuatro formas de autenticación: login automático (usuario y contraseña con el endpoint de login del contrato), token Bearer, cookie de sesión y cabecera personalizada (nombre y valor).
- **RF-30.** En el login automático, el sistema propondrá el endpoint de login detectado en el contrato, obtendrá el token y lo renovará automáticamente cuando venza durante una ejecución.
- **RF-31.** El sistema cifrará las credenciales antes de almacenarlas y nunca las volverá a mostrar completas; solo mostrará los últimos 4 caracteres.
- **RF-32.** El sistema permitirá probar una identidad; si la autenticación falla, mostrará el código de estado recibido sin exponer la credencial.
- **RF-33.** Si un token Bearer o una cookie vence durante una ejecución, el sistema marcará la identidad como «Credencial vencida», omitirá sus pruebas restantes y lo informará en el resultado.
- **RF-34.** El sistema incluirá siempre una identidad anónima que no envía credenciales.

### 7.6 Gestión de recursos por identidad (F-06)

**Descripción:** Registra qué objetos de la API pertenecen a cada identidad (por ejemplo, el pedido 101 es del usuario A). Es lo que permite comprobar si una identidad accede a objetos ajenos.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. El analista pulsa «Descubrir recursos».
2. El sistema llama a las operaciones de listado de solo lectura como cada identidad y registra los identificadores devueltos.
3. El sistema muestra los recursos encontrados por identidad; el analista los confirma, corrige o agrega a mano.

**Requerimientos funcionales:**

- **RF-35.** El sistema identificará en el contrato los parámetros de ruta que representan identificadores de recursos y permitirá al analista corregir esa selección.
- **RF-36.** El sistema descubrirá recursos ejecutando únicamente operaciones GET de listado como cada identidad.
- **RF-37.** El sistema permitirá registrar, editar y eliminar recursos a mano, indicando tipo, identificador e identidad propietaria.
- **RF-38.** Si una identidad no tiene recursos, el sistema advertirá que el módulo de acceso a objetos no podrá probarla.

### 7.7 Definición de la política de acceso (F-07)

**Descripción:** Para cada operación se declara quién debería poder ejecutarla. La política es la referencia contra la que se compara lo que realmente ocurre.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. El sistema propone una plantilla para cada operación a partir de la seguridad declarada en el contrato y de la forma de la ruta.
2. El analista revisa la tabla de operaciones y acepta o cambia la plantilla de cada una.
3. Cuando aplica, indica qué campo identifica al propietario del recurso.
4. Guarda la política; los módulos de autorización quedan disponibles.

**Requerimientos funcionales:**

- **RF-39.** El sistema ofrecerá cinco plantillas de política por operación: pública, cualquier autenticado, solo propietario, propietario o administrador, y solo administrador.
- **RF-40.** El sistema propondrá una plantilla inicial por operación, que el analista deberá confirmar; las propuestas no confirmadas no se usarán en las pruebas.
- **RF-41.** Para las plantillas que involucran propiedad, el sistema permitirá indicar el parámetro o campo que identifica al propietario.
- **RF-42.** El sistema permitirá editar la política en bloque, por ejemplo aplicar una plantilla a todas las operaciones de una misma ruta.
- **RF-43.** El sistema guardará quién y cuándo modificó la política.

### 7.8 Configuración y ejecución de pruebas (F-08)

**Descripción:** El analista ejecuta un módulo individual o la prueba completa con los módulos que deje activos. La ejecución corre en segundo plano.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. Desde el dashboard, el analista elige un módulo o «Prueba completa».
2. En la prueba completa, activa o desactiva módulos; los de riesgo medio y alto aparecen desactivados y requieren confirmación explícita.
3. Ajusta los límites si lo desea y pulsa «Ejecutar».
4. El sistema muestra el progreso en tiempo real; el analista puede cancelar en cualquier momento.
5. Al terminar, el sistema muestra el resumen y los hallazgos.

**Requerimientos funcionales:**

- **RF-44.** El sistema permitirá ejecutar un solo módulo o una prueba completa con cualquier combinación de módulos.
- **RF-45.** El sistema deshabilitará los módulos cuyos requisitos no se cumplan (por ejemplo, identidades insuficientes) e indicará qué falta.
- **RF-46.** Los módulos de riesgo medio y alto estarán desactivados por defecto; activarlos requerirá confirmar una advertencia en cada ejecución.
- **RF-47.** El sistema aplicará límites por ejecución: peticiones por segundo (5 por defecto, máximo 20), concurrencia (máximo 5), total de peticiones (máximo 5,000) y duración (máximo 30 minutos).
- **RF-48.** El sistema ejecutará las pruebas en solo lectura por defecto; las pruebas que escriben solo actuarán sobre recursos creados por la propia plataforma, que se eliminarán al terminar.
- **RF-49.** El sistema ordenará las operaciones para evitar interferencias: crear, leer, modificar y eliminar.
- **RF-50.** Antes de cada petición, el sistema resolverá el destino y bloqueará direcciones privadas, de loopback, de enlace local y de metadatos de nube, así como redirecciones fuera del dominio verificado.
- **RF-51.** El sistema mostrará el progreso en tiempo real: módulo en curso, peticiones enviadas, porcentaje y hallazgos encontrados.
- **RF-52.** El sistema permitirá cancelar una ejecución; se detendrá en menos de 5 segundos, conservará los resultados parciales y eliminará los recursos que haya creado.
- **RF-53.** El sistema permitirá una sola ejecución activa por proyecto.

### 7.9 Módulos de prueba de seguridad (F-09)

**Descripción:** Conjunto de siete módulos. Los dos primeros solo requieren la URL y el contrato; los de autorización requieren identidades, recursos y política.

**Prioridad:** Alta para Autenticación, Configuración, Acceso a objetos y Acceso a funciones; media para Propiedades, Consumo de recursos e Inyección SQL.

**Acciones iniciadoras y comportamiento esperado:**

1. El analista ejecuta uno o varios módulos (F-08).
2. Cada módulo envía sus peticiones, compara la respuesta con el comportamiento esperado y registra un hallazgo por cada discrepancia.

**Requerimientos funcionales:**

- **RF-54.** Módulo Autenticación (API2): el sistema detectará operaciones protegidas que responden con éxito sin credenciales o con credenciales vacías, vencidas o con firma alterada.
- **RF-55.** Módulo Configuración (API8): el sistema detectará cabeceras de seguridad ausentes, políticas CORS que aceptan cualquier origen con credenciales, y respuestas de error que exponen detalles internos.
- **RF-56.** Módulo Acceso a objetos (API1): el sistema detectará cuando una identidad obtiene con éxito un recurso que pertenece a otra identidad, en operaciones cuya política exige propiedad. Requiere al menos dos identidades autenticadas con recursos.
- **RF-57.** Módulo Acceso a funciones (API5): el sistema detectará cuando una identidad sin rol de administrador ejecuta con éxito una operación cuya política es «solo administrador». Requiere una identidad normal y una administradora.
- **RF-58.** Módulo Propiedades (API3): el sistema detectará campos presentes en las respuestas que no están declarados en el esquema del contrato, y campos protegidos que la API acepta modificar.
- **RF-59.** Módulo Consumo de recursos (API4): el sistema detectará la ausencia de límite de peticiones mediante una ráfaga corta y acotada, y la ausencia de límite de tamaño de cuerpo mediante envíos de tamaño creciente con tope; ambas pruebas se detendrán en cuanto la API responda con el límite esperado.
- **RF-60.** Módulo Inyección SQL (CWE-89): el sistema detectará indicios de inyección SQL en los parámetros declarados en el contrato, usando exclusivamente técnicas de detección que no modifican datos.
- **RF-61.** Para decidir si hay una falla, el sistema considerará la política declarada y el contenido de la respuesta, no solo el código de estado.
- **RF-62.** Cada hallazgo registrará: módulo, operación, identidad, severidad (crítica, alta, media, baja o informativa), categoría OWASP, CWE, evidencia y recomendación de corrección.

### 7.10 Visualización de resultados y hallazgos (F-10)

**Descripción:** Muestra lo que encontró cada ejecución con la evidencia necesaria para reproducir y corregir cada falla.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. Al terminar una ejecución, el sistema muestra su resumen.
2. El analista revisa la matriz de acceso y la lista de hallazgos, y filtra por módulo, severidad o estado.
3. Abre un hallazgo para ver su detalle y la recomendación de corrección.

**Requerimientos funcionales:**

- **RF-63.** El sistema mostrará el resumen de cada ejecución: módulos ejecutados, peticiones enviadas, duración, estado final y número de hallazgos por severidad.
- **RF-64.** El sistema mostrará la matriz identidad × operación con el resultado esperado y el observado en cada celda, marcando visualmente las discrepancias.
- **RF-65.** El sistema mostrará la lista de hallazgos con filtros por módulo, severidad y estado, y ordenada por severidad.
- **RF-66.** El detalle del hallazgo mostrará la petición y la respuesta que lo reproducen, con credenciales y tokens enmascarados, la explicación de la falla y la recomendación de corrección.
- **RF-67.** El sistema truncará los cuerpos de respuesta almacenados como evidencia a 10 KB.

### 7.11 Seguimiento y re-testeo de hallazgos (F-11)

**Descripción:** Tras corregir su API, el analista vuelve a ejecutar las pruebas y el sistema indica qué se resolvió, qué persiste y qué volvió a aparecer, hasta concluir el proyecto.

**Prioridad:** Alta.

**Acciones iniciadoras y comportamiento esperado:**

1. El analista corrige su API y pulsa «Volver a probar».
2. El sistema repite los mismos módulos y compara los hallazgos con los de la ejecución anterior.
3. El sistema asigna a cada hallazgo su nuevo estado y actualiza el historial.
4. Cuando no quedan hallazgos abiertos, el proyecto se marca como «Concluido».

**Requerimientos funcionales:**

- **RF-68.** El sistema identificará un mismo hallazgo entre ejecuciones mediante una huella formada por operación, identidad, módulo y tipo de falla.
- **RF-69.** El sistema asignará a cada hallazgo uno de estos estados: nuevo, persistente, resuelto, regresión o riesgo aceptado.
- **RF-70.** El sistema permitirá marcar un hallazgo como riesgo aceptado o falso positivo con una justificación obligatoria; podrá revertirse.
- **RF-71.** El sistema permitirá repetir la última ejecución con la misma configuración en un solo paso.
- **RF-72.** El sistema conservará el historial de todas las ejecuciones del proyecto y la evolución de estados de cada hallazgo.
- **RF-73.** El sistema marcará el proyecto como «Concluido» cuando no tenga hallazgos en estado nuevo, persistente o regresión, y lo reabrirá si una ejecución posterior encuentra alguno.

### 7.12 Generación de reportes (F-12)

**Descripción:** Permite entregar los resultados a personas que no usan la plataforma.

**Prioridad:** Media.

**Acciones iniciadoras y comportamiento esperado:**

1. El analista elige «Reporte» desde una ejecución o desde el proyecto.
2. El sistema muestra una vista imprimible.
3. El analista la imprime o la guarda como PDF desde el navegador, o descarga los hallazgos en Excel.

**Requerimientos funcionales:**

- **RF-74.** El sistema generará un reporte por ejecución y uno del estado actual del proyecto.
- **RF-75.** El reporte incluirá: nombre del proyecto, fecha, módulos ejecutados, resumen por severidad y estado, matriz de acceso y cada hallazgo con evidencia enmascarada, clasificación y recomendación.
- **RF-76.** El reporte tendrá una hoja de estilos de impresión que lo haga legible en tamaño carta y A4.
- **RF-77.** El sistema permitirá exportar la lista de hallazgos a un archivo de Excel (.xlsx).

### 7.13 Panel de administración (F-13)

**Descripción:** Permite al equipo de Hindama conocer el uso de la plataforma y las fallas más comunes sin acceder a información de los analistas ni de sus APIs.

**Prioridad:** Baja.

**Acciones iniciadoras y comportamiento esperado:**

1. El administrador inicia sesión y abre el panel.
2. Elige un periodo y consulta los indicadores.

**Requerimientos funcionales:**

- **RF-78.** El sistema mostrará al administrador: número de usuarios, proyectos y ejecuciones por periodo; fallas más frecuentes por módulo y categoría OWASP; y tiempo promedio entre la detección y la resolución de un hallazgo.
- **RF-79.** Las estadísticas serán agregadas; el panel no mostrará URLs, contratos, credenciales, evidencias ni datos que identifiquen a un analista o a su API.
- **RF-80.** El sistema negará con código 403 el acceso de un administrador al contenido de cualquier proyecto.

### 7.14 Bitácora de auditoría (F-14)

**Descripción:** Registro inalterable de las acciones sensibles, útil para investigar incidentes o usos indebidos.

**Prioridad:** Media.

**Acciones iniciadoras y comportamiento esperado:**

1. El sistema registra cada acción sensible en el momento en que ocurre.
2. El administrador consulta la bitácora y filtra por fecha, tipo de acción o usuario.

**Requerimientos funcionales:**

- **RF-81.** El sistema registrará: alta y baja de cuentas, creación, verificación y eliminación de proyectos, alta y baja de identidades, ejecuciones lanzadas y canceladas con sus módulos y límites, aceptación de riesgos y bloqueos por destino no permitido.
- **RF-82.** Cada registro incluirá fecha y hora, usuario, acción, proyecto afectado (por identificador) y dirección IP de origen.
- **RF-83.** Los registros no podrán editarse ni eliminarse desde la plataforma y no contendrán credenciales.
- **RF-84.** El administrador podrá consultar la bitácora con filtros por fecha, tipo de acción y usuario.

### 7.15 Autenticación de dos factores (F-15)

**Descripción:** Segundo factor opcional para las cuentas de la plataforma, con códigos TOTP generados por una aplicación como Google Authenticator. Se implementa en la fase final.

**Prioridad:** Baja.

**Acciones iniciadoras y comportamiento esperado:**

1. El usuario abre su perfil y elige «Activar 2FA».
2. El sistema muestra un código QR; el usuario lo escanea y confirma con un código de 6 dígitos.
3. En los siguientes inicios de sesión, el sistema pide el código además de la contraseña.

**Requerimientos funcionales:**

- **RF-85.** El sistema permitirá activar y desactivar el segundo factor TOTP desde el perfil, usando la funcionalidad nativa de Cognito.
- **RF-86.** El sistema exigirá el segundo factor a los administradores.
- **RF-87.** Desactivar el segundo factor requerirá un código TOTP válido.

## 8. Reglas de negocio

Las siguientes reglas aplican a todo el sistema, no a una funcionalidad específica.

- **RN-01.** Ninguna petición se envía a una API cuyo proyecto no esté verificado como propiedad del analista.
- **RN-02.** Un analista solo puede ver, modificar o eliminar sus propios proyectos y todo lo que contienen.
- **RN-03.** El administrador no accede al contenido de los proyectos; solo a estadísticas agregadas y a la bitácora.
- **RN-04.** El rol de administrador solo lo asigna el equipo de Hindama desde Cognito.
- **RN-05.** Los módulos de riesgo medio y alto (Propiedades, Consumo de recursos e Inyección SQL) están desactivados por defecto y su activación se confirma en cada ejecución.
- **RN-06.** Las pruebas solo modifican recursos creados por la propia plataforma, que se eliminan al terminar o al cancelar la ejecución.
- **RN-07.** Un proyecto solo puede tener una ejecución activa a la vez.
- **RN-08.** Una propuesta automática de política no se usa en las pruebas hasta que el analista la confirma.
- **RN-09.** Aceptar un riesgo o marcar un falso positivo exige una justificación y queda registrado en la bitácora.
- **RN-10.** Un proyecto se considera concluido cuando no tiene hallazgos en estado nuevo, persistente o regresión.
- **RN-11.** Las credenciales de las identidades nunca se muestran completas después de guardarse, ni aparecen en registros, evidencias o reportes.
- **RN-12.** El analista acepta los términos de uso responsable antes de crear su primer proyecto, comprometiéndose a probar solo APIs propias o con autorización por escrito.

## 9. Requerimientos de interfaces externas

### 9.1 Interfaces de usuario

La interfaz se divide en tres áreas:

- **Pública:** página de inicio, registro, inicio de sesión y recuperación de contraseña.
- **Analista:** lista de proyectos, asistente de creación de proyecto, dashboard del proyecto, configuración (contrato, verificación, identidades, recursos y política), ejecución con progreso, resultados, detalle de hallazgo, historial y reporte imprimible.
- **Administrador:** panel de estadísticas y consulta de la bitácora.

**Estándares de la interfaz.**

- Barra de navegación superior en todas las pantallas autenticadas, con acceso a proyectos, perfil y cierre de sesión.
- Ruta de navegación (por ejemplo, Proyectos › Mi API › Ejecución 3) en las pantallas internas de un proyecto.
- Colores fijos por severidad (crítica, alta, media, baja e informativa), siempre acompañados de su texto para no depender solo del color.
- Botón principal único por pantalla; las acciones destructivas o de riesgo piden confirmación.
- Mensajes de error junto al campo que los causa, en lenguaje claro y con la acción para corregirlos.
- Idioma español en la versión 1.0.

Los prototipos de pantalla se documentarán en el documento de diseño.

### 9.2 Interfaces de hardware

- El sistema no requiere hardware especial: se usa desde computadoras de escritorio o portátiles con navegador web, y para consulta desde tabletas y teléfonos.
- La impresión del reporte se realiza con cualquier impresora configurada en el sistema operativo, a través del diálogo de impresión del navegador.
- No existen interacciones directas de datos o control entre el software y dispositivos de hardware.

### 9.3 Interfaces de software

- **Servidor de Next.js:** renderiza la interfaz, gestiona la sesión con Cognito y reenvía las peticiones del usuario a la API de la plataforma, agregando el token de Cognito.
- **Amazon Cognito:** registro, inicio de sesión, verificación de correo, recuperación de contraseña, segundo factor TOTP y emisión de tokens JWT que la API de la plataforma valida.
- **PostgreSQL 16:** almacenamiento de usuarios, proyectos, contratos, identidades, recursos, políticas, ejecuciones, resultados, hallazgos y bitácora.
- **Redis y RQ:** cola de ejecuciones en segundo plano y canal de progreso hacia la interfaz.
- **APIs de los analistas:** el motor de pruebas les envía peticiones HTTP según su contrato OpenAPI, con las credenciales de cada identidad.
- **Servidores DNS públicos:** consulta de registros TXT para la verificación de propiedad y resolución de destinos antes de cada petición.
- **Librería de análisis de OpenAPI** (openapi-core o prance): validación del contrato y resolución de referencias internas.

### 9.4 Interfaces de comunicación

- Toda comunicación entre el navegador y la plataforma usa HTTPS con TLS 1.2 o superior.
- El navegador se comunica únicamente con el servidor de Next.js. La sesión viaja en una cookie HttpOnly, Secure y SameSite=Lax; las peticiones que modifican datos llevan además un token anti-CSRF.
- El servidor de Next.js consume exclusivamente la API REST de la plataforma, con mensajes JSON y el token JWT de Cognito en la cabecera Authorization.
- El progreso de las ejecuciones se transmite con Server-Sent Events (SSE) desde la API de la plataforma, a través del servidor de Next.js.
- Las peticiones hacia las APIs de los analistas usan HTTPS; si la URL base usa HTTP, el sistema muestra una advertencia de que el tráfico, incluidas las credenciales de prueba, viaja sin cifrar.
- Los correos de verificación y recuperación los envía Cognito.
- Las credenciales de las identidades se cifran en reposo con AES-256-GCM; la clave se guarda fuera de la base de datos.

## 10. Requerimientos no funcionales

Los siguientes criterios permiten evaluar la operación del sistema. Las metas están dimensionadas para la versión 1.0 y el uso académico inicial.

#### Eficiencia

- **RNF-01.** Las pantallas y operaciones de la API de la plataforma, excepto las ejecuciones de prueba, responderán en menos de 2 segundos en el 95 % de los casos.
- **RNF-02.** La importación de un contrato de hasta 500 operaciones tardará menos de 10 segundos.
- **RNF-03.** El progreso de una ejecución se actualizará en la interfaz con un retraso máximo de 2 segundos.
- **RNF-04.** El sistema soportará 50 usuarios con sesión concurrente y 10 ejecuciones simultáneas sin degradar RNF-01.

#### Seguridad lógica y de datos

- **RNF-05.** Todo recurso de la API de la plataforma aplicará control por rol y por propietario; un analista que intente acceder a un proyecto ajeno recibirá un código 404.
- **RNF-06.** Las credenciales de las identidades y demás secretos se cifrarán en reposo con AES-256-GCM.
- **RNF-07.** El servidor de Next.js enviará cabeceras de seguridad (HSTS, Content-Security-Policy, X-Content-Type-Options) y protegerá contra CSRF las peticiones que modifican datos; la API de la plataforma no aceptará tráfico público y devolverá errores sin detalles internos.
- **RNF-08.** Toda decisión de autenticación y autorización la toma la API de la plataforma; el servidor de Next.js no contendrá lógica de negocio ni de permisos.
- **RNF-09.** La plataforma limitará las peticiones a su propia API a 100 por minuto por usuario.
- **RNF-10.** Antes de la entrega, la plataforma no tendrá hallazgos abiertos de severidad crítica o alta según Bandit, pip-audit, npm audit, Trivy, OWASP ZAP y sus propios módulos de prueba.

#### Usabilidad

- **RNF-11.** Un usuario nuevo podrá crear un proyecto, verificarlo y ejecutar los módulos de Autenticación y Configuración en menos de 15 minutos sin ayuda.
- **RNF-12.** Al menos 4 de 5 usuarios de prueba completarán una ejecución de principio a fin sin asistencia.
- **RNF-13.** El sistema mostrará mensajes de error informativos y orientados al usuario final, con la acción para corregirlos.
- **RNF-14.** Cada pantalla de configuración incluirá ayuda contextual que explique qué se pide y para qué sirve.
- **RNF-15.** La aplicación tendrá diseño responsive y cumplirá los criterios de contraste del nivel AA de WCAG 2.1.

#### Dependibilidad

- **RNF-16.** El sistema tendrá una disponibilidad mensual del 99 %.
- **RNF-17.** La base de datos tendrá respaldo automático diario con retención de 7 días; la pérdida máxima de datos ante una falla será de 24 horas.
- **RNF-18.** Si una ejecución se interrumpe por una falla del servidor, quedará marcada como «Fallida», conservará sus resultados parciales y no dejará recursos creados en la API del analista.
- **RNF-19.** Dos ejecuciones consecutivas sobre el mismo estado de una API producirán los mismos hallazgos.
- **RNF-20.** El sistema completo podrá reiniciarse en menos de 5 minutos.

#### Mantenibilidad

- **RNF-21.** El motor de pruebas tendrá una cobertura de pruebas unitarias de al menos 70 %.
- **RNF-22.** La API de la plataforma publicará su documentación OpenAPI generada automáticamente.
- **RNF-23.** Los cambios en la base de datos se aplicarán mediante migraciones versionadas.
- **RNF-24.** Agregar un nuevo módulo de prueba no requerirá modificar los módulos existentes.

## 11. Otros requerimientos

- **Base de datos:** los datos de un proyecto se conservan mientras exista; al eliminar el proyecto o la cuenta se borran de forma permanente en un plazo máximo de 30 días, incluidos los respaldos.
- **Legales:** la plataforma publicará términos de uso y un aviso de privacidad conforme a la Ley Federal de Protección de Datos Personales en Posesión de los Particulares. Los términos prohíben probar APIs sin autorización de su dueño.
- **Internacionalización:** la versión 1.0 se publica en español; los textos de la interfaz se mantienen separados del código para permitir agregar inglés.
- **Despliegue:** todo el sistema y el laboratorio de validación se levantan con Docker Compose para que cualquier integrante los reproduzca en su equipo.
- **Reutilización:** los módulos de prueba comparten una interfaz común; el laboratorio (VAmPI y la mini API propia) se reutiliza en las pruebas automatizadas de cada módulo.
- **Versiones futuras:** fuera de la versión 1.0 se contemplan (1) una capa de inteligencia artificial que proponga la política de acceso, identifique los campos de propiedad y explique los hallazgos; y (2) un proyecto de demostración: una API de prueba basada en el laboratorio, desplegada en AWS de forma aislada y preconfigurada, para que un usuario pruebe Hindama sin registrar una API propia.

## 12. Glosario

Términos y siglas usados en este documento, en orden alfabético.

| Término | Definición |
| --- | --- |
| AES-256-GCM | Algoritmo de cifrado simétrico con clave de 256 bits que además garantiza la integridad de los datos cifrados. |
| Amazon Cognito | Servicio de AWS para registro, inicio de sesión y gestión de usuarios. |
| Analista | Usuario registrado que prueba sus propias APIs en la plataforma. |
| API | Interfaz de programación de aplicaciones: conjunto de operaciones que un sistema expone para que otros lo usen. |
| API REST | API que usa HTTP y sus métodos (GET, POST, PUT, DELETE) para operar sobre recursos. |
| BFLA | Broken Function Level Authorization (API5): un usuario ejecuta funciones que su rol no permite. |
| BOLA | Broken Object Level Authorization (API1): un usuario accede a objetos que pertenecen a otro. |
| Contrato OpenAPI | Documento que describe las operaciones, parámetros, respuestas y seguridad de una API según la especificación OpenAPI. |
| Cookie HttpOnly | Cookie que el navegador envía al servidor pero que el JavaScript de la página no puede leer. |
| CORS | Cross-Origin Resource Sharing: mecanismo que controla qué sitios web pueden llamar a una API desde el navegador. |
| CSRF | Cross-Site Request Forgery: ataque que hace que el navegador de un usuario envíe, sin que lo sepa, una petición a un sitio donde tiene sesión. |
| CWE | Common Weakness Enumeration: catálogo de tipos de debilidades de software mantenido por MITRE. |
| Ejecución | Corrida de uno o varios módulos de prueba sobre un proyecto. |
| Hallazgo | Falla de seguridad detectada en una ejecución, con su evidencia, severidad y recomendación. |
| Hindama | Nombre de la plataforma especificada en este documento; en estonio significa «evaluar». |
| Huella | Combinación de operación, identidad, módulo y tipo de falla que identifica un mismo hallazgo entre ejecuciones. |
| Identidad | Cuenta de prueba en la API del analista que la plataforma usa para enviar peticiones como esa persona. |
| Inyección SQL | Falla que permite alterar las consultas a la base de datos de una aplicación mediante datos de entrada. |
| JWT | JSON Web Token: token firmado que transporta la identidad de un usuario entre sistemas. |
| Módulo de prueba | Conjunto de pruebas que verifica un tipo de falla específico. |
| Next.js | Framework de React para aplicaciones web que se ejecuta con un servidor Node.js. |
| OWASP | Open Worldwide Application Security Project: fundación que publica, entre otros, el Top 10 de riesgos de seguridad en APIs. |
| Payload | Cuerpo de datos que se envía en una petición. |
| Política de acceso | Declaración de quién debería poder ejecutar cada operación de la API. |
| Proyecto | Espacio de la plataforma que agrupa todo lo relacionado con una API del analista. |
| Rate limit | Límite de peticiones que una API acepta de un mismo cliente en un periodo. |
| Re-testeo | Nueva ejecución tras corregir la API, para comprobar si los hallazgos se resolvieron. |
| Recurso | Objeto de la API del analista (por ejemplo, un pedido) que pertenece a una identidad. |
| SSE | Server-Sent Events: tecnología que permite al servidor enviar actualizaciones al navegador en tiempo real. |
| SSRF | Server-Side Request Forgery: ataque que usa un servidor para enviar peticiones a destinos internos o no autorizados. |
| Staging | Entorno de pruebas de una aplicación, separado del entorno de producción. |
| TOTP | Time-based One-Time Password: código temporal de un solo uso para el segundo factor de autenticación. |
