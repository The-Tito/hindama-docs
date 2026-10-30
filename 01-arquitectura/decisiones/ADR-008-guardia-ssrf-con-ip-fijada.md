# ADR-008: Guardia SSRF única con resolución previa e IP fijada

- **Estado:** aceptada (revisada el 2026-10-30: verificación por host exacto e IPs propias bloqueadas)
- **Fecha:** 2026-10-30
- **Relacionado con:** RN-01, RF-11, RF-20, RF-22, RF-50, RF-81

## Contexto

Hindama envía peticiones a URLs que controla el usuario: la URL base, la verificación de propiedad y la importación de contratos por URL. La red del backend permite salir a cualquier destino (ADR-004), así que la aplicación es la principal barrera contra SSRF. Validar la URL solo al registrarla no basta: el DNS puede cambiar entre la validación y la conexión (*DNS rebinding*), y una redirección puede apuntar a la red interna.

## Decisión

Todas las peticiones salientes, de FastAPI y del worker, pasan por **un único cliente HTTP** (`safe_http`) construido sobre httpx. Ningún otro código usa httpx directamente; una regla de lint lo verifica.

Por cada petición, el cliente:

1. Comprueba que el host sea exactamente el host verificado del proyecto (no su dominio padre ni otros subdominios). La excepción es la importación por URL, que valida destino sin exigir propiedad.
2. Resuelve A y AAAA y **rechaza si cualquiera** de las IPs está en los rangos prohibidos:
   - Privadas: `10/8`, `172.16/12`, `192.168/16`, `fc00::/7`.
   - Loopback: `127/8`, `::1`.
   - Enlace local: `169.254/16`, `fe80::/10`.
   - Metadatos de nube: `169.254.169.254`, `169.254.169.253`, `fd00:ec2::254`.
   - Otros: `0.0.0.0/8`, `100.64/10` (CGNAT), multicast y reservadas. También las IPv4 mapeadas en IPv6.
   - Las IP elásticas propias de Hindama (frontend y backend), para que nadie use la plataforma contra sí misma.
3. **Fija la conexión a la IP validada**, conservando el `Host` y el SNI originales, para que no haya una segunda resolución.
4. No sigue redirecciones automáticamente: cada `Location` se valida con los mismos pasos y solo se sigue si permanece en el host verificado, hasta un máximo de 3 saltos.
5. Aplica tiempos de espera (5 s para conectar y 15 s para leer) y un tamaño máximo de respuesta. El cuerpo se lee como stream y se corta.
6. Envía el `User-Agent` `Hindama-Scanner/1.0 (+https://<subdominio>/acerca-del-trafico)` (sección 5.4 de la arquitectura).
7. Registra cada bloqueo en la bitácora como «bloqueo por destino no permitido» (RF-81).

## Alternativas consideradas

| Alternativa | Por qué no |
| --- | --- |
| Validar solo al registrar la URL | Vulnerable a DNS rebinding y a redirecciones. |
| Proxy de salida (por ejemplo, Smokescreen) | Muy buena contención, pero es otro servicio que operar. Se puede agregar después sin cambiar los módulos, porque todos usan `safe_http`. |
| Restringir la salida en el security group | Las APIs de los analistas pueden estar en cualquier IP y puerto, así que el SG no puede expresar la regla. |

## Consecuencias

- **Positivas:**
  - Un solo punto que probar y auditar.
  - Los módulos nuevos heredan la protección (RNF-24).
  - El catálogo de laboratorio puede incluir casos de SSRF contra la propia guardia.
- **Negativas:**
  - Fijar la IP complica TLS: hay que conectar a la IP pero validar el certificado contra el nombre original. Esto requiere un transporte personalizado de httpx con pruebas dedicadas.
  - Las APIs que solo resuelven a IPs privadas no se pueden probar. Es el comportamiento deseado y se explica en la interfaz.
