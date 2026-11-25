# Identidad visual: logo de Hindama

> Estado: vigente v1.0 (2026-11-25). Aprobado el concepto «Nodo».

Este documento reúne el logo de Hindama, cómo usarlo y por qué se eligió. Aquí están los archivos que se usan en la interfaz, en presentaciones, en documentos y en redes.

## 1. El concepto

La «h» termina en un punto, como una petición que llega a su endpoint. Hindama evalúa una API recorriendo sus endpoints a partir del contrato, y el punto es el lugar donde cada prueba llega.

El logotipo «hindama» no usa una fuente: cada letra está dibujada con las mismas piezas que el símbolo (trazo de 40 unidades, arcos concéntricos, altura de las minúsculas de 144). El punto de la «i» repite el nodo.

## 2. Piezas

| Pieza | Archivo maestro | Cuándo usarla |
| --- | --- | --- |
| Logotipo | `svg/hindama-logotipo.svg` | Versión principal: encabezados, portadas, README, presentaciones |
| Símbolo | `svg/hindama-simbolo.svg` | Espacios cuadrados: avatar, barra lateral colapsada, sellos. Desde 24 px |
| Símbolo chico | `svg/hindama-simbolo-chico.svg` | De 16 a 48 px. Trazo de 48 y punto más grande para que no se pierdan |
| Ícono de app | `svg/hindama-icono-app.svg` | Cuadro naranja con la «h» en tinta. Usa el símbolo chico |
| Favicon | `svg/hindama-favicon.svg`, `iconos/favicon.ico` | Pestaña del navegador |

El logotipo ya contiene el símbolo, así que **nunca se ponen juntos** (no va el cuadro naranja al lado de «hindama»).

## 3. Archivos

```
04-ui/identidad/
├── svg/       maestros vectoriales (para cualquier uso nuevo, empieza aquí)
├── png/       con fondo transparente, listos para documentos y presentaciones
├── iconos/    favicon, íconos de app, manifest y el fragmento <head>
├── fuente/    build.py: genera el símbolo y el logotipo
└── ronda-1-conceptos.png
```

Variantes de color en `svg/` y `png/`: `negro`, `blanco`, `tinta`, `naranja`, `naranja-profundo`.

- Símbolo en PNG: 512 y 1024 px de lado.
- Logotipo en PNG: 1200 y 2400 px de ancho.
- Ícono de app en PNG: 1024 px.

Para un uso que no esté cubierto, exporta desde el SVG; no amplíes un PNG.

## 4. Color

| Nombre | HEX | RGB | CMYK | Pantone (aprox.) | Uso |
| --- | --- | --- | --- | --- | --- |
| Naranja Hindama | `#ff6b1a` | 255 107 26 | 0 70 95 0 | 1585 C | Fondo del ícono; logo sobre fondo oscuro |
| Naranja profundo | `#d24e08` | 210 78 8 | 0 75 100 10 | — | Logo en naranja sobre fondo claro |
| Tinta | `#16110d` | 22 17 13 | — | Black 6 C | Logo sobre claro; «h» dentro del cuadro naranja |
| Grafito | `#242528` | 36 37 40 | — | 433 C | Fondo oscuro de la interfaz |

Los valores Pantone son aproximados: confírmalos con un muestrario antes de imprimir. El naranja y el grafito son los mismos tokens de la interfaz (`--accent` en `globals.css`).

Contraste (WCAG 2.1; para gráficos se pide 3:1):

| Combinación | Contraste | Permitida |
| --- | --- | --- |
| Tinta sobre blanco | 18.8:1 | Sí |
| Tinta sobre naranja | 6.6:1 | Sí |
| Naranja sobre grafito `#242528` | 5.4:1 | Sí |
| Blanco sobre grafito | 15:1 | Sí |
| Naranja profundo sobre blanco | 4.3:1 | Sí |
| Naranja sobre blanco | 2.85:1 | **No** |
| Blanco sobre naranja | 2.85:1 | **No** |

## 5. Reglas de uso

- **Espacio libre:** alrededor del logo, al menos el diámetro del punto de la «h» por cada lado.
- **Tamaño mínimo:** logotipo, 72 px de ancho en pantalla o 18 mm impreso. Símbolo, 24 px; por debajo de 24 px, el símbolo chico (desde 16 px).
- **Fondos permitidos:** tinta sobre claro, blanco o naranja sobre grafito, tinta sobre naranja.
- **No hacer:**
  - blanco sobre naranja;
  - naranja `#ff6b1a` sobre blanco;
  - símbolo junto al logotipo;
  - escribir «Hindama» con una fuente en lugar del logotipo;
  - estirar, girar, recortar, agregar sombras, degradados o contornos.

## 6. Cómo se decidió (registro)

**Proceso.** Se partió de un brief corto con los adjetivos *preciso, riguroso, confiable, técnico, cálido*. Se revisaron los logos del rubro de seguridad. En la biblioteca de referencia usada, el 47 % usa contenedores (escudos, insignias) y el 35 % es rojo. Se dejaron fuera los clichés: escudo, candado, llave, lupa, ojo, check y `{}` literal.

**Ronda 1: tres direcciones** (`ronda-1-conceptos.png`), presentadas en gris para juzgar la forma antes que el color:

| Concepto | Idea | Por qué no / por qué sí |
| --- | --- | --- |
| A · Calibre | La H como calibre: evaluar es medir | La v1 tenía las marcas en el travesaño y parecía una almena; se rediseñó. A 16 px las marcas se pierden |
| B · Corchetes | Una H hecha con `[ – ]`, los corchetes del contrato | Era la que se recomendaba por resistencia en tamaño chico; se lee primero `[-]` y luego H |
| **C · Nodo** | Una «h» que llega a su endpoint | **Elegida**: la más cálida y cercana al estilo «vidrio cálido» de la interfaz. Su riesgo era ser poco distintiva; se resolvió dibujando el logotipo completo con el mismo sistema |

**Correcciones de la v2 a la v3:**

1. El arco cambiaba de grosor; ahora es concéntrico, con trazo constante.
2. El palo derecho bajaba hasta la base y se veían sus esquinas debajo del punto. Ahora termina donde el círculo alcanza el ancho del trazo, así el punto cierra limpio.
3. Se agregó el símbolo chico para 16 a 48 px.
4. El favicon negro sin fondo desaparecía en pestañas oscuras; se cambió por el cuadro naranja.

**Pruebas que pasó:**

- Auditoría automática de los SVG: sin texto vivo, sin imágenes incrustadas ni filtros, un solo color y centrado.
- Lectura a 64, 32 y 16 px, en un color, en negativo y desenfocado.
- Revisión en contexto: encabezado oscuro y claro, pestaña, ícono de app, inicio de sesión y README.

**Pendiente:** búsqueda de marcas registradas antes de un uso público. No se hizo y no se puede garantizar que no exista una marca parecida. Formatos de imprenta (PDF, AI o EPS) se exportan desde los SVG cuando hagan falta.
