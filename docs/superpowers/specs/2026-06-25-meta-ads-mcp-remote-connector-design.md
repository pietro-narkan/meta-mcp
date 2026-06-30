# Conector web (claude.ai) de Meta Ads — solo lectura — Diseño

- **Fecha:** 2026-06-25
- **Estado:** Aprobado (diseño) — pendiente plan de implementación
- **Autor:** Pietro + Claude
- **Relación:** Variante **remota** del MCP local ya publicado (`pietro-narkan/meta-mcp`). El build local (stdio, Claude Code) **queda intacto**; esto es un servicio adicional para usarlo desde **claude.ai en el navegador**.

## 1. Contexto

Los trabajadores de Narkan quieren consultar Meta Ads desde **claude.ai (navegador/móvil)**. claude.ai no lanza procesos locales: requiere un **servidor MCP remoto** sobre HTTPS (Streamable HTTP) añadido como "conector personalizado". Se reutiliza el VPS con Dokploy (dominio `plasa.cl`, HTTPS automático vía Traefik) y el mismo **System User token de Meta de solo lectura** (`ads_read`).

**Decisión de acceso:** en vez de OAuth/login, el conector se sirve en una **URL con un secreto** (`https://mcp.plasa.cl/<MCP_SECRET>/mcp`). Ese secreto **es** la contraseña compartida del equipo: se pega una vez en claude.ai, sin pantalla de login, sin Google, sin OAuth. (Se descartó montar un servidor OAuth propio por ser un patrón que `fastmcp` marca como "extremadamente avanzado, a evitar".)

## 2. Objetivos y No-objetivos

**Objetivos**
- Servidor MCP **remoto** (Streamable HTTP) en `mcp.plasa.cl`, como servicio Docker en Dokploy.
- **Solo lectura**: las mismas 11 tools de reporting que el build local.
- **Acceso por URL secreta** (`MCP_SECRET` en la ruta); cero login para el trabajador.
- El **token de Meta vive solo en el servidor** (env de Dokploy); nunca se reparte ni pasa por el navegador.
- **Despliegue y verificación automatizados por la API de Dokploy** (sin SSH).

**No-objetivos (YAGNI)**
- Sin tools de escritura (el servicio remoto NO contiene código de escritura).
- Sin OAuth, sin Google, sin servidor de autorización propio.
- Sin identidad/auditoría por persona (un secreto compartido, decisión del usuario).
- No se modifica el build local ya publicado.
- Sin réplicas múltiples (stateless basta).

## 3. Arquitectura

```
Trabajador en claude.ai (navegador/móvil)
   │  conector = https://mcp.plasa.cl/<MCP_SECRET>/mcp  (el secreto es la "contraseña")
   ▼ HTTPS
mcp.plasa.cl → Traefik (TLS Let's Encrypt) → contenedor Docker
                                              FastMCP · Streamable HTTP · stateless
   │  META_ACCESS_TOKEN read-only (env de Dokploy)
   ▼
Meta Graph API v25.0  (graph.facebook.com)
```

- **Paquete:** `fastmcp` (gofastmcp.com, ≥2.12) — por `http_app()` (ASGI) y la facilidad de montar/CORS. El build local sigue con el `mcp` SDK base; son servicios distintos.
- **Transporte:** Streamable HTTP, **stateless** (`stateless_http=True`).
- **Servido por:** `uvicorn`.

## 4. Estructura del repo

El servicio vive en `remote/` (subdir aislado del repo `meta-mcp`, con su propio `pyproject`/`uv.lock`/`Dockerfile`), del que Dokploy hace build. No comparte deps con `meta_ads_mcp/`.

```
meta-mcp/
├── meta_ads_mcp/             # build LOCAL ya publicado (no se toca)
├── remote/                   # NUEVO servicio remoto
│   ├── app/
│   │   ├── config.py         # env: META_ACCESS_TOKEN, MCP_SECRET
│   │   ├── meta.py           # cliente Graph v25.0 (httpx) — GET only
│   │   ├── tools.py          # las 11 tools de solo lectura
│   │   └── server.py         # FastMCP + monta MCP en /<secreto>/mcp + CORS + /health + `app`
│   ├── tests/
│   ├── pyproject.toml / uv.lock / Dockerfile / .env.example / README.md / DEPLOY.md
└── docs/ ...
```

## 5. Acceso por URL secreta

- `MCP_SECRET` = cadena aleatoria larga (≥32 chars url-safe), en el env de Dokploy.
- El endpoint MCP se sirve en la ruta **`/<MCP_SECRET>/mcp`**. Cualquier otra ruta → **404** (el "candado" es el routing: sin el secreto no hay endpoint).
- `/health` se sirve en la raíz (sin secreto) para el healthcheck de Dokploy/Traefik.
- La URL del conector que se pega en claude.ai: `https://mcp.plasa.cl/<MCP_SECRET>/mcp`.
- **Seguridad:** el secreto va en la URL (queda en la config del conector de claude.ai). Datos de solo-lectura → fuga = como mucho lectura. Rotación = cambiar `MCP_SECRET` y repartir la URL nueva. (No hay login por persona — secreto compartido, aceptado.)

## 6. Transporte HTTP y CORS

- Endpoint Streamable HTTP en `/<MCP_SECRET>/mcp` (POST JSON-RPC + GET SSE). Headers `Mcp-Session-Id`, `MCP-Protocol-Version`. Validar `Origin` (anti DNS-rebinding).
- **CORS** (Starlette `CORSMiddleware`): `allow_origins=["https://claude.ai"]`, `allow_methods=["GET","POST","OPTIONS","DELETE"]`, `allow_headers=["Content-Type","Mcp-Session-Id","MCP-Protocol-Version"]`, **`expose_headers=["Mcp-Session-Id"]`**, `allow_credentials=True`.
- `stateless_http=True`.

## 7. Tools (11, solo lectura)

Mismas que el build local, **reimplementadas finas** sobre Graph v25.0 en `remote/app/tools.py` (el servicio remoto **no contiene código de escritura**): `check_token_status, get_ad_accounts, discover_all_accounts, get_campaigns, get_campaign_details, get_adsets, get_adset_details, get_ads, get_ad_details, get_insights, get_bulk_insights`. Cada una toma `account_id` cuando aplica; auto-descubre las 7 cuentas del token; campos espejo de konquest. El token se lee de `META_ACCESS_TOKEN`.

## 8. Despliegue (Dokploy API / Docker / Traefik)

- **Dockerfile** `python:3.12-slim`, instala deps, expone 8000, `HEALTHCHECK` a `/health`, arranca `uvicorn app.server:app`.
- **Servicio creado por la API de Dokploy** (sin SSH): app desde el repo `pietro-narkan/meta-mcp`, build path `remote/`, Dockerfile. Variables de entorno (no en git): `META_ACCESS_TOKEN`, `MCP_SECRET`. Dominio `mcp.plasa.cl` (HTTPS on → Traefik/Let's Encrypt). Deploy.
- **DNS:** registro `A: mcp.plasa.cl → 173.249.49.22` — **único paso del usuario** (su panel de DNS; no accesible por la API de Dokploy).
- **Firewall:** opcional (hardening) permitir entrada de `160.79.104.0/21`. No bloqueante (el endpoint ya está tras el secreto + TLS).

## 9. Experiencia del trabajador

claude.ai → Ajustes → Conectores → "Añadir conector personalizado" → pegar `https://mcp.plasa.cl/<MCP_SECRET>/mcp` → conectar. **Sin login, sin instalar nada.** Luego preguntar en cualquier chat.

## 10. Pasos del usuario (mínimos)

1. **Un registro DNS:** `A` `mcp` → `173.249.49.22` en el panel de DNS de `plasa.cl` (~2 min). Único paso manual.
2. Pegar la URL del conector (con el secreto) en claude.ai.

Todo lo demás (crear el servicio, variables, dominio, deploy, verificación) lo hace el controlador por la **API de Dokploy** + `curl`.

## 11. Verificación (por API/curl, la hace el controlador)

- Unit: `meta.py` (URLs/errores), `tools.*` (shaping, 11 tools, sin escritura).
- Local: arrancar el contenedor; `/health` 200; `/<secreto>/mcp` responde al handshake MCP; `/mcp` (sin secreto) y rutas erróneas → 404.
- Integración con token real (controlador, vía API de Dokploy para obtener el token): `tools/list` lista 11; `get_campaigns` devuelve datos reales.
- Tras el deploy: `curl https://mcp.plasa.cl/health` 200; `curl https://mcp.plasa.cl/<secreto>/mcp` (POST initialize) responde; ruta sin secreto → 404.
- Único paso E2E manual: el usuario añade el conector en claude.ai y pregunta.

## 12. Seguridad y riesgos (aceptados)

- Acceso por **secreto en URL** (datos solo-lectura; token `ads_read` solo en el servidor). Fuga del secreto = lectura; se rota cambiando `MCP_SECRET`.
- Sin auditoría por persona (secreto compartido).
- TLS por Traefik; firewall al rango de Anthropic opcional.
- Rotar la API key de Dokploy (pendiente heredado).

## 13. Gotchas a respetar (de la investigación)

- `expose_headers` debe incluir `Mcp-Session-Id` o el navegador no mantiene sesión.
- Traefik pasa headers por defecto; no meter un nginx que los recorte.
- Streamable HTTP (no SSE, deprecado); `stateless_http=True` evita estado en memoria.
- El healthcheck `/health` debe dar 200 **antes** de añadir el dominio en Dokploy (si no, Traefik no crea el router).
- `MCP_SECRET` no debe loguearse; el cliente Graph no debe loguear el `access_token` (subir logger httpx a WARNING).

## 14. Fase futura (no ahora)

Si se quiere login real por persona: OAuth con Google (app OAuth + OAuthProxy de fastmcp) o WorkOS AuthKit. Escritura/gestión: token `ads_management` + tools de escritura (otro diseño).
