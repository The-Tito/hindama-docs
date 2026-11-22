---
documento: Entorno local y conexiones del frontend
proyecto: Hindama
version: 1.0
fecha: 2026-11-22
estado: vigente; escrito para Windows, backend 080eaca (contrato 0.6.0) y frontend d031d0e
---

# Entorno local y conexiones del frontend

Cómo levantar Hindama en Windows para conectar el frontend con la API real (secciones 1 a 7) y qué tener en cuenta al conectar las vistas que faltan (sección 8). Los campos y errores de cada endpoint están en la [guía del frontend](guia-frontend.md), sección 5, y en el [contrato](openapi.yaml).

> **Alcance de lo comprobado.** Los scripts de Node, Docker Compose y las conexiones se probaron en macOS, simulando los saltos de línea de Windows. La sintaxis de PowerShell, el certificado de `mkcert` y el inicio de sesión con una cuenta real no se han probado: si un paso falla, avisa para corregir este documento.

## 1. Qué se conecta con qué

```
Navegador
   │  https://localhost:3000   (solo habla con Next.js)
   ▼
Next.js + BFF  (Windows) ──────────► Amazon Cognito hindama-dev  (Internet)
   │  http://127.0.0.1:8000                       ▲
   ▼                                              │ valida tokens y lee el perfil
API FastAPI  (Docker) ────────────────────────────┘
   ├──► PostgreSQL  (Docker)
   └──► Redis  (Docker) ──► motor `scanner`  (Docker) ──► API que se evalúa (URL pública)
```

| Conexión | Se configura en | Valor |
| --- | --- | --- |
| Navegador → Next.js | `HINDAMA_PUBLIC_ORIGIN` | `https://localhost:3000`, exacto |
| Next.js → API | `HINDAMA_API_URL` | `http://127.0.0.1:8000` |
| Next.js → Cognito | `COGNITO_REGION`, `COGNITO_CLIENT_ID`, `COGNITO_CLIENT_SECRET` | Los genera la sección 5 |
| Cookie de sesión | `HINDAMA_SESSION_KEY` | 32 bytes en base64, propios de tu máquina |
| API → Cognito | `HINDAMA_COGNITO_*` en el `.env` del backend | Región, pool y cliente; **sin secreto** |
| API y motor → PostgreSQL y Redis | Contraseñas del `.env` del backend | Compose arma las URL |

Cognito es lo único compartido: las cuentas son del pool de desarrollo y la base de datos es solo tuya.

## 2. Requisitos

- **Docker Desktop** con el motor de WSL 2, abierto.
- **Git**.
- **Node.js 22.12 o superior de la rama 22, o Node.js 24**.
- **AWS CLI v2**, con la llave que te dio el equipo de backend.
- **Puertos libres:** 3000, 8000, 5432 y 6379. Un PostgreSQL instalado en Windows suele ocupar el 5432: detén su servicio.

Todo se ejecuta en **PowerShell de Windows, no dentro de WSL**, para que el navegador confíe en el certificado de HTTPS. Los comandos usan `npm.cmd` y `npx.cmd` para no depender de la política de ejecución de scripts.

Configura AWS una sola vez (región `us-east-1`, formato `json`) y comprueba que responde con tu usuario:

```powershell
aws configure --profile hindama
aws sts get-caller-identity --profile hindama
```

Tu usuario solo puede leer el secreto del cliente de Cognito. Cualquier otro `AccessDenied` es normal.

## 3. Clonar sin cambiar los saltos de línea

Git en Windows convierte los archivos a CRLF, y eso rompe dos cosas: el script que crea los roles de la base y `npm test` del frontend, que compara el contrato byte por byte. Clona así, en una misma carpeta:

```powershell
git clone -c core.autocrlf=input -b develop https://github.com/The-Tito/hindama-backend.git
git clone -c core.autocrlf=input https://github.com/The-Tito/hindama-docs.git
git clone -c core.autocrlf=input -b dev https://github.com/lsprz2773/hindama-front.git
```

**Si ya los tenías clonados**, con tus cambios ya en un commit:

```powershell
cd hindama-backend
git config core.autocrlf input
Remove-Item docker/postgres/init/01-roles.sh
git checkout -- docker/postgres/init/01-roles.sh
git ls-files --eol docker/postgres/init/01-roles.sh

cd ../hindama-front
git config core.autocrlf input
Remove-Item contract/openapi.yaml, src/lib/api/schema.d.ts
git checkout -- contract/openapi.yaml src/lib/api/schema.d.ts
git ls-files --eol contract/openapi.yaml src/lib/api/schema.d.ts
cd ..
```

Los tres archivos deben decir `w/lf`.

## 4. Backend

Desde `hindama-backend`, genera el `.env` con contraseñas y llave propias. Copia el bloque completo, incluida la última línea:

```powershell
@'
const fs = require('fs');
const { randomBytes } = require('crypto');
if (fs.existsSync('.env')) {
  console.error('Ya existe .env: no se toco.');
  process.exit(1);
}
const env = fs.readFileSync('.env.example', 'utf8')
  .replace(/\r\n/g, '\n')
  .replace(/=cambia-esto$/gm, () => '=' + randomBytes(24).toString('base64url'))
  .replace('cambia-esto-por-32-bytes-en-base64', randomBytes(32).toString('base64'))
  .replace('us-east-1_cambiaEsto', 'us-east-1_8qQxmtXn1')
  .replace('=cambiaesto', '=f8oiqpgmhhlv9ineppp8a2mbl');
fs.writeFileSync('.env', env, { flag: 'wx', mode: 0o600 });
console.log('Listo: .env del backend creado.');
'@ | node -
```

Levántalo:

```powershell
docker compose up -d --build --wait
docker compose ps -a
```

| Servicio | Estado esperado |
| --- | --- |
| `db`, `redis`, `api` | `Up … (healthy)` |
| `scanner` | `Up`, sin `Restarting`. `--wait` lo da por bueno aunque esté fallando: míralo aquí |
| `migrations` | `Exited (0)`. Es normal: aplica las migraciones y termina |

- **Si ya tenías un `.env`** que no funcionaba, renómbralo a `.env.anterior`, genera el nuevo y ejecuta `docker compose down -v` antes de levantar. **Borra tu base local.** Hace falta porque PostgreSQL solo toma las contraseñas la primera vez que crea su volumen.
- **No cambies `HINDAMA_CREDENTIAL_KEYS`** después: las credenciales de identidades ya guardadas quedarían ilegibles.

## 5. Frontend

Desde `hindama-front`, genera `.env.local`. El script lee el secreto de SSM sin mostrarlo y no escribe nada si AWS falla:

```powershell
@'
const fs = require('fs');
const { randomBytes } = require('crypto');
const { execFileSync } = require('child_process');
if (fs.existsSync('.env.local')) {
  console.error('Ya existe .env.local: renombralo y repite.');
  process.exit(1);
}
let secret = '';
try {
  secret = execFileSync('aws', [
    'ssm', 'get-parameter', '--profile', 'hindama', '--region', 'us-east-1',
    '--name', '/hindama/dev/frontend/cognito-client-secret',
    '--with-decryption', '--query', 'Parameter.Value', '--output', 'text',
  ], { encoding: 'utf8', stdio: ['ignore', 'pipe', 'inherit'] }).trim();
} catch {
  // El error de AWS ya se mostro.
}
if (!secret || secret === 'None') {
  console.error('No se pudo leer el secreto: no se escribio nada.');
  process.exit(1);
}
fs.writeFileSync('.env.local', [
  'COGNITO_REGION=us-east-1',
  'COGNITO_CLIENT_ID=f8oiqpgmhhlv9ineppp8a2mbl',
  'COGNITO_CLIENT_SECRET=' + secret,
  'HINDAMA_API_URL=http://127.0.0.1:8000',
  'HINDAMA_PUBLIC_ORIGIN=https://localhost:3000',
  'HINDAMA_SESSION_KEY=' + randomBytes(32).toString('base64'),
  '',
].join('\n'), { flag: 'wx', mode: 0o600 });
console.log('Listo: .env.local creado.');
'@ | node -
```

- No copies `.env.example`: el script ya pone todo lo necesario.
- No definas `HINDAMA_SESSION_KEY_PARAMETER` en local: tiene prioridad y haría que el BFF busque la llave en AWS.
- No uses el prefijo `NEXT_PUBLIC_` en ninguna de estas variables: llegarían al navegador.

Instala y arranca con HTTPS:

```powershell
npm.cmd ci
npx.cmd next dev -H localhost -p 3000 --experimental-https
```

- La primera vez, Next descarga `mkcert` y Windows pide instalar una autoridad certificadora local: **acepta**.
- **La terminal debe decir `https://localhost:3000`.** Si la instalación del certificado falla, Next sigue en HTTP con solo un aviso, y todo formulario responde 403. Borra la carpeta `certificates` y vuelve a arrancar.
- Abre siempre `https://localhost:3000`. Ni `http://` ni `127.0.0.1`: el BFF exige ese origen exacto, y la cookie `__Host-` necesita HTTPS en Safari.
- Next puede agregar `certificates` al `.gitignore`. Es correcto; nunca subas esa carpeta.

## 6. Comprobar cada conexión

Hazlo en orden; el primero que falle es el tramo roto.

**1. Next.js → API.** Debe imprimir `200`:

```powershell
node -e "fetch('http://127.0.0.1:8000/health').then(r => console.log(r.status))"
```

**2. API → Cognito.** Desde `hindama-backend`, debe imprimir `200`:

```powershell
docker compose exec api python -c "import urllib.request as u; print(u.urlopen('https://cognito-idp.us-east-1.amazonaws.com/us-east-1_8qQxmtXn1/.well-known/jwks.json').status)"
```

**3. Configuración del BFF.** Abre `https://localhost:3000/api/auth/session` sin sesión. Debe responder 401 `auth.required`. Un 500 indica una variable faltante o inválida: el nombre sale en la terminal de Next.

**4. Las tres piezas juntas.** Deja abierto `docker compose logs -f api` y en el navegador:

1. Crea tu cuenta en `/sign-up` con un correo real y confirma el código. El pool envía **50 correos al día entre todos**: reutiliza tus cuentas.
2. Inicia sesión. En el log debe aparecer `path=/me` con `status=200`.
3. Acepta los términos y crea un proyecto con una URL pública, por ejemplo `https://example.com`. Debe aparecer `POST` a `/projects` con `status=201`.

**El login puede funcionar aunque la API esté apagada**, porque solo depende de Cognito. Por eso la prueba es el `GET /me` en el log, no haber entrado.

Para el rol de administrador, pide al equipo de backend que agregue tu cuenta al grupo y vuelve a iniciar sesión. Las vistas de administración todavía no tienen API.

## 7. Uso diario

| Necesito | Comando, desde `hindama-backend` |
| --- | --- |
| Levantar | `docker compose up -d --wait` |
| Traer cambios del backend | `git pull` y después `docker compose up -d --build --wait` |
| Aplicar un cambio del `.env` | `docker compose up -d` (`restart` no lo relee) |
| Ver errores | `docker compose logs -f api scanner` |
| Apagar sin perder datos | `docker compose stop` |
| Empezar con la base vacía | `docker compose down -v` (borra todo lo local) |

- Si cambias `.env.local`, reinicia Next: el BFF guarda la configuración al arrancar.
- La documentación interactiva de la API está en `http://127.0.0.1:8000/docs`. Es solo para consulta: el código del navegador nunca llama al puerto 8000.
- Las pruebas e2e usan su propio Next por HTTP contra el simulador. Detén tu servidor de desarrollo antes de correrlas.

## 8. Conectar las vistas que faltan

### 8.1 Estado en `dev` (d031d0e)

| Grupo | Operaciones | Estado |
| --- | --- | --- |
| Cuenta | `getMe`, `acceptTerms` | Conectado |
| Proyectos | listar, crear, consultar, editar, eliminar | Conectado |
| Progreso | `streamRunEvents` | Relevo en el BFF; falta la vista |
| Verificación | `getVerification`, `verifyOwnership` | Falta; ver 8.3 C |
| Contrato | `importContract`, `listContracts`, `getContract`, `listOperations` | Falta; ver 8.3 A y D |
| Política | `updateOperation`, `applyPolicy` | Falta |
| Identidades | listar, crear, editar, eliminar, probar | Falta; ver 8.3 B |
| Recursos | listar, crear, editar, eliminar | Falta |
| Descubrir recursos | `discoverResources` | **No existe todavía en el backend**: no la conectes |
| Ejecuciones | crear, listar, consultar, cancelar, volver a probar, matriz | Falta; ver 8.3 B, D y E |
| Hallazgos | listar, detalle, ocurrencias, aceptar, revertir | Falta; ver 8.3 D |
| Administración, 2FA, baja de cuenta | — | Sin contrato |

Las vistas sin conectar muestran datos de ejemplo mezclados con el proyecto real (`toLegacyProject`). Lo que se ve ahí no viene de la API.

El orden que pide la API es: **proyecto → verificación → contrato → identidades → recursos → política → ejecución → hallazgos**. Conectarlas en ese orden te da datos reales para la siguiente.

### 8.2 El patrón para una operación normal

Una operación JSON necesita cuatro piezas:

1. Esquemas de entrada y respuesta en `src/lib/api/schemas/`.
2. Una entrada en `src/server/bff/specs.ts`.
3. Un route handler con la misma ruta de la API bajo `/api`.
4. La llamada desde la vista con `useHttpClient()`, que ya agrega el token CSRF.

Ejemplo con `deleteIdentity`:

```ts
// src/server/bff/specs.ts, dentro de SPECS
deleteIdentity: { path: [...project, "identities", { param: "identityId" }] },
```

```ts
// src/app/api/projects/[projectId]/identities/[identityId]/route.ts
import { apiRoute } from "@/server/bff/route";
import { SPECS } from "@/server/bff/specs";

export const DELETE = apiRoute(SPECS.deleteIdentity);
```

El nombre de `param` debe ser idéntico al de la carpeta (`identityId`); si no, responde 404 sin llegar a la API. El BFF también rechaza todo parámetro de consulta que el esquema no declare.

### 8.3 Donde el patrón actual no alcanza

**A. `importContract` es multipart.** `apiRoute` responde 400 a todo lo que no sea JSON y el cliente HTTP convierte un `FormData` en `{}`. Necesita su propio handler:

```ts
// src/app/api/projects/[projectId]/contracts/route.ts
import { contractVersionSchema } from "@/lib/api/schemas/contracts"; // por crear
import { isUuid } from "@/lib/api/zod";
import { apiPath, getDeps, proxyToApi } from "@/server/bff";
import { problem } from "@/server/bff/problem";
import { transformWith } from "@/server/bff/route";

const MAX_UPLOAD = 5 * 1024 * 1024 + 64 * 1024; // el mismo límite que la API

export async function POST(request: Request, ctx: { params: Promise<{ projectId: string }> }) {
  const { projectId } = await ctx.params;
  if (!isUuid(projectId)) return problem(404, "resource.not_found");
  return proxyToApi(request, apiPath("projects", projectId, "contracts"), await getDeps(), {
    prepare: async (incoming) => {
      const size = Number(incoming.headers.get("content-length"));
      if (!size || size > MAX_UPLOAD) return problem(413, "contract.too_large");
      const form = await incoming.formData().catch(() => null);
      if (!form) return problem(400, "request.malformed");
      const clean = new FormData();
      for (const name of ["file", "url"]) {
        for (const value of form.getAll(name)) clean.append(name, value);
      }
      return { body: clean, search: "" }; // sin contentType: fetch pone el boundary
    },
    transform: transformWith(contractVersionSchema),
  });
}
```

Y en `attempt`, de `src/lib/http/client.ts`, no serialices el formulario:

```ts
const isForm = body instanceof FormData;
if (body !== undefined && !isForm) finalHeaders["Content-Type"] = "application/json";
// …y al llamar a doFetch:
body: body === undefined ? undefined : isForm ? body : JSON.stringify(body),
```

Responde 201 si creó una versión y 200 si el documento no cambió.

**B. Cuerpos opcionales.** `testIdentity` admite no llevar cuerpo, pero `apiRoute` responde 400 si declaras `body` y llega vacío, aunque el esquema sea opcional. Envía siempre `{}`. `rerunRun` sí exige cuerpo. `cancelRun` no lleva: no declares `body`.

**C. El campo `found` de la verificación se pierde.** `verifyOwnership` lo incluye en sus 422, pero lo descartan `sanitizeProblem` (`src/server/bff/problem.ts`) y `toApiError` (`src/lib/http/client.ts`). Agrégalo en ambos y en `ApiError`, y muéstralo como texto: viene del servidor evaluado.

**D. Filtros de consulta.** Un filtro repetible con un solo valor llega como texto, no como lista. Y `z.coerce.boolean()` convierte `"false"` en `true`:

```ts
const list = <T extends z.ZodType>(item: T) =>
  z.preprocess((value) => (typeof value === "string" ? [value] : value), z.array(item));

status: list(runStatusSchema).optional(),
include_retired: z.stringbool().optional(),
page: z.coerce.number().int().min(1).max(10_000).optional(),
```

- Repetibles: `status` en ejecuciones; `module` y `verdict` en la matriz; `module`, `severity` y `status` en hallazgos.
- `page_size` máximo: 500 en operaciones y matriz, 20 en ocurrencias, 100 en lo demás.

**E. Progreso por SSE.** La ruta del BFF termina en `/progress`; la de la API, en `/events`.

- Escucha con `addEventListener` los eventos `snapshot`, `progress` y `end`; `onmessage` no los recibe.
- En `end`, llama a `close()`.
- El servidor cierra a los 15 minutos y `EventSource` reconecta solo.
- **Ante una respuesta distinta de 200 (401, 429, 503) no reconecta:** queda en `CLOSED`. En `onerror`, si `readyState` es `EventSource.CLOSED`, consulta `getRun` y vuelve a abrir el stream si sigue activa.

### 8.4 Reglas de la API que afectan a las vistas

- **`localhost` no sirve como URL base de un proyecto**, tampoco `host.docker.internal` ni una IP privada: la guardia SSRF los bloquea. Para conectar verificación y ejecuciones hace falta una API con URL pública donde puedas publicar el archivo de verificación. Si la tienes en tu máquina, un túnel sirve: `cloudflared tunnel --url http://localhost:<puerto>`. Expón solo APIs de prueba y cierra el túnel al terminar.
- **Esperas largas:** verificar y probar una identidad tardan hasta 20 s; importar, hasta 30 s. Deshabilita el botón mientras tanto.
- **Lanzar, cancelar y volver a probar responden 202**: la operación sigue en segundo plano.
- **100 peticiones por minuto por usuario**, y los reintentos de los `GET` cuentan. No consultes en bucle lo que ya llega por SSE.
- **El contrato está fijado por hash** en el frontend. Si cambia en `hindama-docs`, actualiza la copia, el hash de `scripts/check-contract.mjs` y los tipos.

## 9. Si algo falla

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| `credential key 1 is not valid base64` | Quedó el valor de ejemplo | Genera el `.env` (sección 4) |
| `password authentication failed for user "hindama_…"` | El volumen se creó con otras contraseñas, o el script de roles tenía CRLF | Sección 3 y después `docker compose down -v` |
| `port is already allocated` o `bind` | Puerto ocupado | `Get-NetTCPConnection -LocalPort 5432` muestra el proceso |
| `scanner` en `Restarting` | `.env` inválido | `docker compose logs scanner` |
| `AccessDenied` o `ParameterNotFound` al generar `.env.local` | Permiso, región o nombre | Avisa al equipo de backend |
| `InvalidClientTokenId` o `SignatureDoesNotMatch` | Llaves de AWS mal copiadas | Repite `aws configure --profile hindama` |
| 500 en todo `/api/*` | Falta una variable del BFF o es inválida | Terminal de Next; sección 5 |
| 403 `csrf.invalid` al enviar un formulario | Next cayó a HTTP o abriste otra URL | `https://localhost:3000` exacto |
| 401 `auth.invalid_credentials` con la contraseña correcta | Secreto del cliente equivocado: se ve igual | Regenera `.env.local` |
| Entras y regresas a `/sign-in` | Cookie descartada por usar HTTP, o la API rechaza el token | HTTPS; si sigue, busca `invalid_token` en el log de la API y compara el pool y el cliente |
| Entras, pero todo da 503 | La API está apagada o `HINDAMA_API_URL` está mal | Sección 6, paso 1 |
| 403 `terms.not_accepted` | Faltan los términos | `/projects/new/terms` |
| 422 `url.destination_not_allowed` | URL base local o privada | Sección 8.4 |
| 429 al registrarte o pedir un código | Límite de Cognito | Espera, o reutiliza una cuenta |
| 429 `rate_limit.exceeded` ya con sesión | Más de 100 peticiones por minuto | Espera lo que indique `Retry-After` |
| 502 `response.invalid` | La respuesta no cumple tu esquema de Zod | Compara con el contrato; si la API no lo cumple, repórtalo |
| `contract:check` falla sin haber tocado el contrato | CRLF | Sección 3 |

Al reportar un error del backend, incluye el `request_id` y la línea del log. Nunca pegues tokens, cookies ni el contenido de `.env` o `.env.local`.
