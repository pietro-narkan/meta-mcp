# Conector web (claude.ai) de Meta Ads — solo lectura — Diseño

- **Fecha:** 2026-06-25
- **Estado:** Aprobado (diseño) — pendiente plan de implementación
- **Autor:** Pietro + Claude
- **Relación:** Variante **remota** del MCP local ya publicado (`pietro-narkan/meta-mcp`, ver `2026-06-25-meta-ads-mcp-readonly-design.md`). El build local (stdio, para Claude Code) **queda intacto**; esto es un servicio adicional para usarlo desde **claude.ai en el navegador**.

## 1. Contexto

Los trabajadores de Narkan quieren consultar Meta Ads desde **claude.ai (navegador/móvil)**, no solo desde Claude Code. claude.ai no puede lanzar un proceso local: requiere un **servidor MCP remoto** sobre HTTPS (transporte Streamable HTTP) añadido como "conector personalizado", con **OAuth**. Se reutiliza el VPS con Dokploy (dominio propio `plasa.cl`, HTTPS automático vía Traefik) y el mismo **System User token de Meta de solo lectura** (`ads_read`).

## 2. Objetivos y No-objetivos

**Objetivos**
- Servidor MCP **remoto** (Streamable HTTP) en `mcp.plasa.cl`, desplegado como servicio Docker en Dokploy.
- **Solo lectura**: las mismas 11 tools de reporting que el build local.
- **OAuth** compatible con claude.ai, delegando el login a **Google**, restringido a **una sola cuenta** (`agencia.narkan@gmail.com`).
- El **token de Meta vive solo en el servidor** (env de Dokploy); nunca se reparte ni pasa por el navegador.
- **Cero instalación** para el trabajador.

**No-objetivos (YAGNI)**
- Sin tools de escritura/gestión (el servicio remoto NO contiene código de escritura).
- Sin identidad/auditoría por persona (una sola cuenta compartida, decisión del usuario).
- Sin SaaS de auth externo (WorkOS/Auth0): se hace self-hosted con Google directo.
- No se modifica el build local ya publicado.
- Sin réplicas múltiples/escala horizontal (servicio pequeño, stateless basta).

## 3. Arquitectura

```
Trabajador en claude.ai (navegador/móvil)
   │  1) OAuth: login con Google (cuenta agencia.narkan)
   │  2) consultas MCP (Authorization: Bearer <token>)
   ▼ HTTPS
mcp.plasa.cl → Traefik (TLS Let's Encrypt) → contenedor Docker
                                              FastMCP · Streamable HTTP · stateless
   │  META_ACCESS_TOKEN read-only (env de Dokploy)
   ▼
Meta Graph API v25.0  (graph.facebook.com)
```

- **Paquete:** `fastmcp` (gofastmcp.com, ≥2.12) — elegido por su `OAuthProxy`, `JWTVerifier` y `http_app()` (ASGI), que el `mcp` SDK base no trae. (El build local sigue con el `mcp` SDK base; son repos/servicios distintos.)
- **Transporte:** Streamable HTTP en `/mcp`, **stateless** (`stateless_http=True`) — apto para datos de solo lectura y sin estado de sesión en memoria.
- **Servido por:** `uvicorn` sobre `mcp.http_app()`.

## 4. Estructura del repo

El servicio vive en el **mismo repo** `meta-mcp`, en un subdirectorio aislado `remote/` (su propio `pyproject`/`uv.lock`/`Dockerfile`), del que Dokploy hace build. No comparte dependencias con el paquete local `meta_ads_mcp/`.

```
meta-mcp/
├── meta_ads_mcp/             # build LOCAL ya publicado (no se toca)
├── remote/                   # NUEVO servicio remoto
│   ├── app/
│   │   ├── server.py         # FastMCP + auth + CORS + /health + arranque ASGI
│   │   ├── auth.py           # OAuthProxy→Google + JWTVerifier + allowlist de email
│   │   ├── meta.py           # cliente Graph v25.0 (httpx) — GET only
│   │   └── tools.py          # las 11 tools @mcp.tool de solo lectura
│   ├── tests/
│   ├── pyproject.toml / uv.lock
│   ├── Dockerfile
│   ├── .env.example
│   └── README.md
└── docs/ ...
```

## 5. Autenticación (OAuth → Google, una sola cuenta)

**Roles:** claude.ai = cliente OAuth; nuestro servidor = Authorization Server (vía `OAuthProxy`) + Resource Server.

- **`OAuthProxy`** presenta a claude.ai una interfaz OAuth 2.1 + PKCE con DCR (lo que claude.ai espera), y por detrás **delega a Google**:
  - `upstream_authorization_endpoint = https://accounts.google.com/o/oauth2/v2/auth`
  - `upstream_token_endpoint = https://oauth2.googleapis.com/token`
  - `upstream_client_id/secret` = app OAuth de Google (la crea el usuario).
  - `base_url = https://mcp.plasa.cl`.
- **`JWTVerifier`** valida el **ID token** de Google: `jwks_uri = https://www.googleapis.com/.well-known/jwks.json`, `issuer = https://accounts.google.com`, `audience = <GOOGLE_CLIENT_ID>`.
- **Allowlist (clave):** tras validar el ID token, se comprueba que `email == agencia.narkan@gmail.com` **y** `email_verified == true`; cualquier otra cuenta se rechaza (403). El email permitido es configurable por env (`ALLOWED_EMAILS`).
- **Redirect URIs:**
  - En la app de Google se registra el callback de NUESTRO servidor: `https://mcp.plasa.cl/auth/callback` (el que use `OAuthProxy`).
  - `OAuthProxy` acepta el redirect de claude.ai: `https://claude.ai/api/mcp/auth_callback`.
- **Metadata obligatoria** (la sirve `fastmcp` automáticamente al configurar el provider): protected-resource metadata cuyo `resource` debe coincidir **byte a byte** con la URL que el trabajador escribe en claude.ai (`https://mcp.plasa.cl`), y AS metadata con `code_challenge_methods_supported: ["S256"]`.
- `initialize` del MCP va **sin auth**; `tools/list` y `tools/call` requieren Bearer válido (401 si falta, no bloquear el handshake).

## 6. Transporte HTTP y CORS

- Endpoint único `/mcp` (POST JSON-RPC + GET SSE para mensajes del servidor). Headers: `Mcp-Session-Id`, `MCP-Protocol-Version` (manejar `2025-11-25` y `2025-03-26`). Validar `Origin` (403 si inválido) — anti DNS-rebinding.
- **CORS** (Starlette `CORSMiddleware`): `allow_origins=["https://claude.ai"]`, `allow_methods=["GET","POST","OPTIONS","DELETE"]`, `allow_headers=["Content-Type","Authorization","Mcp-Session-Id","MCP-Protocol-Version"]`, **`expose_headers=["Mcp-Session-Id"]`** (crítico para el navegador), `allow_credentials=True`.
- `stateless_http=True` evita estado de sesión en memoria.

## 7. Tools (11, solo lectura)

Mismas que el build local, **reimplementadas como funciones async finas** sobre Graph v25.0 en `remote/app/tools.py` (el servicio remoto **no contiene código de escritura** — seguridad por construcción, más fuerte que filtrar):
`check_token_status, get_ad_accounts, discover_all_accounts, get_campaigns, get_campaign_details, get_adsets, get_adset_details, get_ads, get_ad_details, get_insights, get_bulk_insights`.

- Cada tool toma `account_id` (las que aplican) como argumento; auto-descubre las 7 cuentas del token.
- Selección de campos espejo de konquest para paridad de salida (p. ej. `get_campaigns` devuelve `total`, `status_counts`, `campaigns[...]`).
- El token se lee de `META_ACCESS_TOKEN` (env); nunca como argumento ni hardcodeado.

## 8. Despliegue (Dokploy / Docker / Traefik)

- **Dockerfile** `python:3.12-slim`, instala deps, expone 8000, `HEALTHCHECK` a `/health`, arranca `uvicorn app.server:app --host 0.0.0.0 --port 8000`.
- **Servicio en Dokploy** apuntando al repo + path `remote/`. Variables en el **env de Dokploy** (no en git): `META_ACCESS_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `MCP_BASE_URL=https://mcp.plasa.cl`, `ALLOWED_EMAILS=agencia.narkan@gmail.com`.
- **Dominio** `mcp.plasa.cl` (tab Domains, HTTPS on → Traefik + Let's Encrypt). El **health-check debe responder 200 antes** de añadir el dominio (si falla, Traefik no crea el router).
- **Endpoint `/health`** simple (200 `{"status":"ok"}`).
- **Firewall:** permitir entrada del rango de Anthropic **`160.79.104.0/21`** al puerto del servicio.
- **DNS:** registro A `mcp.plasa.cl` → IP del VPS (`173.249.49.22`).

## 9. Experiencia del trabajador

claude.ai → Ajustes → Conectores → "Añadir conector personalizado" → URL `https://mcp.plasa.cl` → "Iniciar sesión con Google" con `agencia.narkan@gmail.com` → consultar. Sin instalar nada.

## 10. Setup que hace el usuario (guiado)

1. **App OAuth de Google** (Google Cloud Console, proyecto de la cuenta agencia.narkan): tipo "Web application", redirect `https://mcp.plasa.cl/auth/callback`, scopes `openid email profile`. Copiar client ID/secret.
2. **DNS** `mcp.plasa.cl` → `173.249.49.22`.
3. **Servicio en Dokploy** desde el repo (path `remote/`) + variables de entorno + dominio + firewall.

## 11. Verificación / pruebas

- Unit: `auth` rechaza emails fuera de la allowlist y tokens inválidos; `tools.format_*` con datos simulados; `meta.py` construye URLs/campos correctos.
- Local: arrancar el contenedor, `/health` 200, `initialize` sin auth OK, `tools/list` sin token → 401.
- Integración: el MCP Inspector o `curl` con un Bearer de prueba lista 11 tools; una llamada real (`get_campaigns`) con el token devuelve datos.
- E2E: añadir el conector en claude.ai, login Google con la cuenta permitida, preguntar y recibir datos reales; confirmar que otra cuenta Google es rechazada.

## 12. Seguridad y riesgos (aceptados)

- Endpoint **público** protegido por OAuth + allowlist de un solo email + firewall al rango de Anthropic.
- Token Meta es `ads_read` (imposible gastar/editar) y vive solo en el servidor.
- **Aceptado por el usuario:** compartir la cuenta Google (posibles 2FA/bloqueos de Google al entrar varios) y sin auditoría por persona.
- Rotar la API key de Dokploy (pendiente del trabajo anterior). El `GOOGLE_CLIENT_SECRET` y el token Meta solo en env de Dokploy.

## 13. Gotchas a respetar (de la investigación)

- `resource` de la metadata = URL exacta (`https://mcp.plasa.cl`, sin barra final si así se añade en claude.ai).
- Google no soporta DCR → por eso `OAuthProxy` (fachada DCR). No exponer Google como AS directo.
- `expose_headers` debe incluir `Mcp-Session-Id` o el navegador no mantiene sesión.
- Traefik pasa headers por defecto; no meter un nginx que los recorte.
- `initialize` sin auth; 401 (no bloqueo) en `tools/*`.

## 14. Fase futura (no ahora)

Identidad por persona (si crecen): cuentas Google individuales o WorkOS AuthKit con allowlist por org. Escritura/gestión: token `ads_management` + revisión de app + tools de escritura (otro diseño).
