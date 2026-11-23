---
documento: Pruebas del frontend en el navegador integrado
proyecto: Hindama
version: 1.0
fecha: 2026-11-23
estado: informe de una pasada manual; hallazgos por revisar, nada corregido
---

# Pruebas del frontend en el navegador integrado (23/11/2026)

Recorrido manual de la aplicación como lo haría un analista nuevo, en escritorio: de la página pública al asistente de proyecto, el contrato, la verificación, las identidades, los recursos, la política y los ajustes. Se hizo en el navegador integrado de la app de escritorio de Claude, con una cuenta de analista nueva y con permiso para aceptar los términos y crear datos de prueba. **Nada se corrigió**: este documento solo registra lo que se vio, con su evidencia, para decidir qué arreglar.

Las capturas están en [`capturas-pruebas-2026-11-23/`](capturas-pruebas-2026-11-23/).

## 1. Qué se probó y con qué

| Dato | Valor |
| --- | --- |
| Frontend | `dev` 31f23d6 (PR #14, #15 y #16 mergeados), en `next dev` sobre `https://localhost:3000` |
| Backend | API local en Docker, contrato 0.7.0 |
| Cuenta | Analista nueva (`perezaguilera2773`), sin proyectos al empezar |
| Navegador | Panel del navegador integrado, escritorio (≈1222×897) y móvil emulado (375×812), tema oscuro y claro, español e inglés |
| Datos creados | Un proyecto «Prueba QA navegador», un contrato importado por URL (Petstore, 19 operaciones), una identidad «Usuario A» y un recurso |

### Limitaciones de la prueba (leerlas antes de los hallazgos)

1. **Panel oculto al principio.** Mientras el panel estuvo oculto, las animaciones no avanzaban (`document.getAnimations()` en `running` con tiempo 0 y `hasFocus` falso). Las capturas salían atenuadas y algunas vistas se quedaban en «Cargando…». Las capturas de este documento son las tomadas con el panel visible; las atenuadas se descartaron.
2. **`next dev` es lento en la primera visita.** Cada ruta tardó entre 5 y 15 s en pasar del esqueleto al contenido (ver F-11). Es compilación en caliente, no el comportamiento de producción.
3. **Otra sesión editaba el mismo árbol de trabajo.** A mitad de la prueba aparecieron cambios sin commitear en `Frontend/` (contrato 0.10.0, mensajes y vistas de ejecuciones). El servidor de desarrollo los recargó en vivo, así que lo visto después puede incluir ese trabajo en curso. Un caso concreto está en F-16.
4. **No se pudo ejecutar una prueba de seguridad.** Verificar la propiedad exige publicar un archivo en un host público; `example.com` no se puede verificar, así que el proyecto quedó «Pendiente de verificación» y no hubo ejecuciones, matriz, hallazgos ni reporte con datos reales. Esas vistas se cubren con las pruebas e2e, no con esta pasada.
5. **No se probó el éxito del inicio de sesión** (no hay contraseña de la cuenta) ni el cierre de sesión, para no perder la sesión.

## 2. Resumen de hallazgos

| ID | Severidad | Dónde | Resumen |
| --- | --- | --- | --- |
| F-01 | Descartado | Todo el marco con sesión, en móvil | La barra lateral ocupa la pantalla y deja el contenido más de 1000 px abajo |
| F-02 | Media | `/profile/two-factor` | Muestra una clave TOTP fija y un QR de relleno; acepta cualquier código |
| F-03 | Media | 403, 404 y públicas, con sesión | El encabezado ofrece «Iniciar sesión» y «Crear cuenta» a quien ya entró |
| F-04 | Media | `/projects/[id]` | «Recursos» aparece bloqueado en la barra lateral, pero la vista funciona sin verificar |
| F-05 | Baja | `/sign-in`, `/sign-up` | Con sesión abierta muestran el formulario en vez de llevar a proyectos |
| F-06 | Descartado | Móvil, `/sign-in` | El formulario queda debajo del panel de presentación |
| F-07 | Baja | Contrato por URL | El error termina con dos puntos: «desde esa URL..» |
| F-08 | Baja | Avisos persistentes | El mismo mensaje sale dos veces (traducido y de la API) |
| F-09 | Baja | Contrato importado | El aviso «Revisa los avisos…» sale aunque no hay ningún aviso |
| F-10 | Baja | 404 | El título de la pestaña queda en «Hindama» |
| F-11 | Informativa | Todas las rutas en desarrollo | Primera visita de 5 a 15 s con esqueleto |
| F-12 | Baja | Páginas largas | La barra lateral se desplaza con la página y se pierde de vista |
| F-13 | Baja | 404 de un hallazgo | El texto habla del «proyecto» aunque falta un hallazgo |
| F-14 | Informativa | Idioma | Una URL sin prefijo redirige a `/en` si antes se visitó `/en` |
| F-15 | Informativa | `/profile/two-factor` | La barra lateral de esa pantalla solo trae «Proyectos» |
| F-16 | Resuelto en cambios sin commitear | Eliminar identidad | El texto decía solo «sus hallazgos se conservan» |

## 3. Hallazgos

### F-01 · Móvil: la barra lateral empuja el contenido más de 1000 px hacia abajo (descartado)

- **Decisión (Luis, 23/11/2026):** la aplicación no debe funcionar en móvil, así que esto no es un defecto. Se deja registrado porque el requerimiento RNF-15 sigue diciendo «diseño responsive»; conviene ajustar ese requerimiento o el diseño para que no se contradigan.

- **Dónde:** cualquier vista con el marco de la aplicación (`/projects/…`), con ancho de 375 px.
- **Pasos:** emular un móvil (375×812) y abrir `/projects/<id>`.
- **Qué pasa:** la barra lateral ocupa casi todo el ancho (≈250 px) y todo su alto; el contenido (`<main>`) empieza en `y ≈ 1073` y hay que desplazarse más de una pantalla para llegar a él. Al contraer el menú, la barra baja a ≈100 px de ancho pero sigue ocupando la primera fila.
- **Esperado:** en móvil, una barra superior o un menú desplegable, con el contenido a la vista.
- **Evidencia:** [esqueleto](capturas-pruebas-2026-11-23/19-movil-esqueleto.jpg), [barra lateral](capturas-pruebas-2026-11-23/20-movil-barra-lateral.jpg), [contraída](capturas-pruebas-2026-11-23/21-movil-barra-contraida.jpg), [contenido abajo](capturas-pruebas-2026-11-23/22-movil-contenido-abajo.jpg). Medición con JS: `main.y = 1073`, `main.h = 2137`.

### F-02 · El 2FA que se ofrece a cualquier usuario es una simulación (Media)

- **Dónde:** `/profile` («Activar 2FA») y `/profile/two-factor`.
- **Qué pasa:** la pantalla muestra un QR de relleno y la clave fija `JBSW Y3DP EHPK 3PXP`, y «Confirmar» acepta cualquier código. El perfil dice «Desactivado. Te recomendamos activarlo.». Un usuario real podría creer que activó el segundo factor.
- **Contexto:** es la limitación conocida de V-05, V-10 y V-11 (no hay MFA en el contrato; el pool de Cognito lo tiene desactivado). Aquí se anota por su efecto de cara al usuario.
- **Sugerencia:** ocultar el botón o marcarlo «Próximamente» hasta que exista el flujo real.
- **Evidencia:** [2FA simulado](capturas-pruebas-2026-11-23/29-2fa-simulado.jpg).

### F-03 · Con sesión abierta, el 403 y el 404 muestran «Iniciar sesión» y «Crear cuenta» (Media)

- **Dónde:** `/admin` (403 para un analista), rutas inexistentes (404), y otras páginas de error fuera del marco de proyecto.
- **Pasos:** con la sesión abierta, abrir `/admin`.
- **Qué pasa:** el encabezado es el público (logotipo, idioma, «Iniciar sesión», «Crear cuenta») y no hay barra lateral ni menú de usuario. Medido con JS: los botones del encabezado son `Hindama`, `Español`, `Iniciar sesión`, `Crear cuenta`.
- **Esperado:** el marco del usuario con sesión, o al menos sin ofrecer registrarse a quien ya lo hizo. El botón «Ir a mis proyectos» sí existe.
- **Evidencia:** [403 con sesión](capturas-pruebas-2026-11-23/30-403-admin-con-sesion.jpg).

### F-04 · «Recursos» bloqueado en la barra lateral, pero la vista funciona (Media)

- **Dónde:** barra lateral de un proyecto sin verificar.
- **Qué pasa:** el elemento dice «Disponible tras verificar» y no es un enlace (en el árbol de accesibilidad no existe como enlace). Sin embargo `/projects/<id>/resources` abre y permite agregar y confirmar recursos; solo «Descubrir recursos» exige verificar (y lo explica). El inventario (§8 #8) ya dice que la vista no se bloquea.
- **Esperado:** que la barra lateral enlace a la vista y deje el bloqueo solo en el botón de descubrir.
- **Evidencia:** [recursos](capturas-pruebas-2026-11-23/14-recursos-descubrir-bloqueado.jpg), [recurso agregado](capturas-pruebas-2026-11-23/15-recurso-agregado.jpg).

### F-05 · Con sesión abierta, `/sign-in` y `/sign-up` no redirigen (Baja)

- **Pasos:** con la sesión abierta, abrir `/sign-in`.
- **Qué pasa:** se muestra el formulario de inicio de sesión (igual con `/sign-up`).
- **Esperado:** llevar a `/projects`, o a la pantalla que corresponda por rol.
- **Evidencia:** [iniciar sesión con error](capturas-pruebas-2026-11-23/25-iniciar-sesion-error.jpg) (tomada con sesión abierta) y [reglas de contraseña](capturas-pruebas-2026-11-23/26-crear-cuenta-reglas.jpg).

### F-06 · Móvil: el formulario de inicio de sesión queda debajo del panel de presentación (descartado)

- **Decisión (Luis, 23/11/2026):** igual que F-01, móvil queda fuera de alcance.

- **Qué pasa:** a 375 px el panel «Evalúa tu API antes de publicarla» ocupa la primera pantalla y el formulario queda abajo.
- **Evidencia:** [móvil, iniciar sesión](capturas-pruebas-2026-11-23/23-movil-iniciar-sesion.jpg).

### F-07 · Doble punto en el error de importar un contrato por URL (Baja)

- **Pasos:** en `/projects/<id>/contract`, «Desde URL», escribir una URL que responde 404 e importar.
- **Qué pasa:** el mensaje dice «No pudimos descargar el contrato desde esa URL..».
- **Evidencia:** [error por URL](capturas-pruebas-2026-11-23/08-contrato-url-error.jpg).

### F-08 · El aviso persistente de HTTP repite el mismo texto (Baja)

- **Dónde:** asistente de proyecto, resumen y ajustes cuando la URL base usa HTTP.
- **Qué pasa:** el recuadro trae el texto traducido («Las credenciales de prueba viajarían sin protección…») y debajo, en monoespaciado, el mensaje de la API («La URL usa HTTP; el tráfico y las credenciales de prueba viajarán sin cifrar.»), con el mismo sentido.
- **Evidencia:** [aviso en el asistente](capturas-pruebas-2026-11-23/06-proyecto-creado-aviso-http.jpg), [resumen](capturas-pruebas-2026-11-23/10-resumen-proyecto.jpg).

### F-09 · «Revisa los avisos» sin avisos (Baja)

- **Qué pasa:** al importar el contrato de Petstore, el aviso emergente dice «Contrato importado. Revisa los avisos y confirma la política de acceso.», pero la respuesta de la API trae `warnings: []`.
- **Sugerencia:** mencionar los avisos solo si hay alguno.
- **Evidencia:** [contrato importado](capturas-pruebas-2026-11-23/09-contrato-importado.jpg).

### F-10 · La pestaña de la página 404 se llama solo «Hindama» (Baja)

- **Qué pasa:** el resto de las páginas usa «X · Hindama»; la 404 deja el título genérico.

### F-11 · Rendimiento en desarrollo: 5 a 15 s en la primera visita de cada ruta (Informativa)

- **Medición** en `/en/projects/<id>/policy`: el documento carga en ≈1,0 s (`domContentLoaded`) pero la primera petición a la API sale a los 7,4 s. Es el tiempo de compilar e hidratar la ruta en `next dev`; durante ese tiempo se ve el esqueleto de carga.
- **Matiz:** una sesión que editaba el mismo árbol de trabajo provocó recargas en caliente que pueden haberlo agravado.
- **Sugerencia:** repetir esta pasada con `next build` y `next start` sobre HTTPS para medir tiempos reales.
- **Evidencia:** [esqueleto de «Nueva ejecución»](capturas-pruebas-2026-11-23/19-movil-esqueleto.jpg) (misma pantalla de carga en móvil).

### F-12 · La barra lateral se desplaza con la página (Baja)

- **Qué pasa:** en páginas largas (contrato con 19 operaciones, recursos) al bajar se pierden de vista las secciones del proyecto y «Perfil» y «Cerrar sesión»; hay que subir para navegar.
- **Sugerencia:** barra lateral fija (`sticky`) con su propio desplazamiento.
- **Evidencia:** [contrato, desplazado](capturas-pruebas-2026-11-23/09-contrato-importado.jpg) y [recursos](capturas-pruebas-2026-11-23/15-recurso-agregado.jpg).

### F-13 · Un hallazgo inexistente dice «el proyecto ya no existe» (Baja)

- **Pasos:** abrir `/projects/<id>/findings/<uuid>` con un hallazgo que no existe.
- **Qué pasa:** 404 con el texto genérico «El enlace puede estar mal escrito, o el proyecto ya no existe o no es tuyo.».

### F-14 · El idioma recordado redirige las URL sin prefijo (Informativa)

- **Qué pasa:** después de abrir una URL con `/en`, abrir una URL sin prefijo (español) redirige a `/en/…`, porque el idioma se recuerda en una cookie. Es el comportamiento esperado de la configuración, pero desconcierta al probar enlaces.

### F-15 · La barra lateral de la pantalla de 2FA solo trae «Proyectos» (Informativa)

- **Evidencia:** [2FA simulado](capturas-pruebas-2026-11-23/29-2fa-simulado.jpg): sin «Perfil» ni «Cerrar sesión» a la vista.

### F-16 · Texto al eliminar una identidad (resuelto en cambios sin commitear)

- **Observado al inicio:** «Al eliminar una identidad se borran su credencial y sus recursos; sus hallazgos se conservan.» (versión en español de `dev` 31f23d6).
- **Observado después:** el texto ya decía «…sus hallazgos se conservan, pero los abiertos pasan a resueltos» en español e inglés, por un cambio sin commitear de otra sesión que coincide con la corrección D1 de los pendientes (contrato 0.8.0).
- **Evidencia:** [identidades, en inglés](capturas-pruebas-2026-11-23/27-identidades-en.jpg) y [diálogo de eliminar](capturas-pruebas-2026-11-23/28-eliminar-identidad-dialogo.jpg).

## 4. Lo que funcionó

| Área | Resultado | Evidencia |
| --- | --- | --- |
| Páginas públicas (inicio, entrar, crear cuenta, recuperar contraseña, términos, privacidad) | Cargan sin errores de consola; textos coherentes | — |
| Reglas de contraseña al registrarse | Se marcan en vivo (mayúscula, minúscula, número cumplidos; longitud y símbolo pendientes) | [26](capturas-pruebas-2026-11-23/26-crear-cuenta-reglas.jpg) |
| Iniciar sesión con datos incorrectos | Mensaje genérico «El correo o la contraseña no son correctos.» (no revela si el correo existe, RF-06) | [25](capturas-pruebas-2026-11-23/25-iniciar-sesion-error.jpg) |
| Términos de uso responsable | Se piden antes del primer proyecto; «Aceptar y continuar» lleva al asistente y avisa «Términos aceptados» | [02](capturas-pruebas-2026-11-23/02-terminos-primer-proyecto.jpg), [03](capturas-pruebas-2026-11-23/03-asistente-terminos-aceptados.jpg) |
| Asistente de proyecto | Valida campos vacíos; rechaza `http://localhost:8000` con «No se aceptan direcciones locales»; crea con una URL pública y avisa de HTTP sin cifrar | [04](capturas-pruebas-2026-11-23/04-asistente-validacion-vacio.jpg), [05](capturas-pruebas-2026-11-23/05-url-local-rechazada.jpg), [06](capturas-pruebas-2026-11-23/06-proyecto-creado-aviso-http.jpg) |
| Contrato | Importa por URL (Petstore: 19 operaciones, OpenAPI 3.0.4); una URL que no responde da un error legible; sin archivo pide elegir uno | [07](capturas-pruebas-2026-11-23/07-contrato-sin-importar.jpg), [09](capturas-pruebas-2026-11-23/09-contrato-importado.jpg) |
| Verificación | Muestra código, URL del archivo y registro DNS; un intento fallido explica «no encontramos el archivo» con `HTTP 404` y cómo corregirlo | [11](capturas-pruebas-2026-11-23/11-verificacion-fallida.jpg) |
| Identidades | Alta con token (se muestra «••••7898»); avisa lo que necesita cada módulo; el diálogo de eliminar explica qué pasa y se cierra con Esc devolviendo el foco | [12](capturas-pruebas-2026-11-23/12-identidad-formulario.jpg), [13](capturas-pruebas-2026-11-23/13-identidades-lista.jpg), [28](capturas-pruebas-2026-11-23/28-eliminar-identidad-dialogo.jpg) |
| Recursos | Agrega un recurso a mano; «Descubrir recursos» queda deshabilitado con su motivo («Verifica la propiedad del host antes de descubrir recursos») | [14](capturas-pruebas-2026-11-23/14-recursos-descubrir-bloqueado.jpg), [15](capturas-pruebas-2026-11-23/15-recurso-agregado.jpg) |
| Política | Propone una plantilla por operación; confirmar una (`POST /pet`) actualiza el contador a «1 de 19 confirmadas» | [16](capturas-pruebas-2026-11-23/16-politica.jpg) |
| Ajustes | Guardar el cambio de host funciona; el diálogo de eliminar pide escribir el nombre y se cierra con Esc | [17](capturas-pruebas-2026-11-23/17-ajustes-guardados.jpg), [18](capturas-pruebas-2026-11-23/18-eliminar-proyecto-dialogo.jpg) |
| Historial, Hallazgos y «Ejecución en curso» sin datos | Estados vacíos claros con «Nueva ejecución» | — |
| Administración con rol de analista | 403 «Esta sección no es para tu rol» en `/admin` y `/admin/audit-log` | [30](capturas-pruebas-2026-11-23/30-403-admin-con-sesion.jpg) |
| Tema claro | Se ve bien en la lista de proyectos | [24](capturas-pruebas-2026-11-23/24-tema-claro-proyectos.jpg) |
| Idioma | El cambio ES/EN conserva la página; las pantallas probadas existen en los dos idiomas | [27](capturas-pruebas-2026-11-23/27-identidades-en.jpg) |
| Consola y red | Solo errores esperados (404 de la ruta inexistente y 422 de las validaciones del servidor); `GET /api/me` se repite en cada vista y deja peticiones abortadas (`ERR_ABORTED`) duplicadas al navegar, sin fallos visibles | — |

Capturas de contexto: [proyectos vacío](capturas-pruebas-2026-11-23/01-proyectos-vacio.jpg) y [resumen del proyecto](capturas-pruebas-2026-11-23/10-resumen-proyecto.jpg).

## 5. Pendiente de probar

- Ejecuciones, progreso, matriz, hallazgos, detalle de un hallazgo y reporte con datos reales: requieren un proyecto verificado, es decir, una API con URL pública donde publicar el archivo de verificación (por ejemplo con un túnel, `entorno-local.md` §8.4).
- Las vistas de administración con una cuenta de administrador (estadísticas y bitácora).
- Inicio de sesión correcto, cierre de sesión y recuperación de contraseña de punta a punta.
- La misma pasada sobre un build de producción (`next build` y `next start` con HTTPS), para medir tiempos y comprobar F-11.
- Teclado y lector de pantalla con más detalle: aquí solo se comprobó el cierre con Esc y el regreso del foco, y que las etiquetas de los campos estén asociadas (se verificó en el DOM en inicio de sesión y registro).
