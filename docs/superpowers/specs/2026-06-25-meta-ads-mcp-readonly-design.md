# Meta Ads MCP (solo-lectura) para trabajadores de Narkan — Diseño

- **Fecha:** 2026-06-25
- **Estado:** Aprobado (diseño) — pendiente plan de implementación
- **Autor:** Pietro + Claude
- **Base:** fork/vendor de [`brandu-mos/konquest-meta-ads-mcp`](https://github.com/brandu-mos/konquest-meta-ads-mcp) (open-core, MIT)

## 1. Contexto

Narkan es una agencia publicitaria que gestiona ~7 cuentas de Meta Ads de clientes
(Bellas Todas, Phy Waters, NeoKodex, Fiorenza, Spa Infinity, Futuro Sin Deudas; "Narkan
publicitaria" está cerrada). Se quiere que los **trabajadores consulten datos de Meta Ads
en lenguaje natural desde Claude Code**, sin entrar al Administrador de Anuncios.

Existe ya un **System User token de Meta** (app "plasa") con scope `ads_read` +
`public_profile`, no expira, con acceso a las 7 cuentas. Vive en el VPS, en las variables
de entorno del backend del proyecto Dokploy `plaza` (`META_SYSTEM_USER_TOKEN`,
`META_APP_ID`, `META_APP_SECRET`). El token es **de solo-lectura**: no puede crear, editar
ni gastar.

Verificado en vivo (v25.0): `campaigns`, `adsets`, `ads` e `insights` devuelven datos
reales con ese token. Las tools de píxeles/catálogos/audiencias/identidades requieren
permisos más amplios que el token no tiene y quedan fuera.

## 2. Objetivos y No-objetivos

**Objetivos**
- MCP **local** que cada trabajador corre en su propio Claude Code (transporte stdio).
- **Solo lectura**: reporting de campañas, ad sets, ads e insights de las cuentas.
- **Onboarding de 1 comando**: clonar → `./setup.sh` → abrir Claude Code → preguntar.
- Distribución como **repo privado** de la org con colaboradores de confianza.
- El **token jamás entra a git**.

**No-objetivos (YAGNI)**
- Sin servidor HTTP/SSE ni multi-tenant; cada trabajador es autónomo.
- Sin tools de gestión/escritura (crear/editar/pausar/borrar/duplicar/subir).
- Sin píxeles, catálogos, audiencias personalizadas ni identidades de página (requieren
  scopes que el token no tiene).
- Sin despliegue en Dokploy: el VPS solo fue la fuente del token, no es runtime.
- Sin tokens por trabajador (un único token compartido de solo-lectura). Auditoría/rotación
  por persona queda como posible fase futura.

## 3. Arquitectura

```
Trabajador en Claude Code
   │  "¿cuánto gastó Spa Infinity este mes?"
   ▼
MCP konquest recortado (local, stdio, Python 3.11/3.12 + uv)
   │  token SOLO-LECTURA cargado desde .env (python-dotenv)
   ▼
Meta Graph API v25.0  →  graph.facebook.com
```

- **Transporte:** stdio (`mcp.run(transport="stdio")`), framework FastMCP del SDK oficial
  de MCP. konquest open-core es stdio-only.
- **Selección de cuenta:** por argumento de llamada (`account_id`), auto-descubiertas desde
  el token. No hay cuenta fija; el trabajador puede consultar cualquiera de las 7.
- **Versión Graph:** constante `v25.0` en konquest (`api.py`). Verificado que el token
  funciona en v25.0. No requiere cambios.

## 4. Estructura del repo

```
meta-mcp/                     (privado, cuenta GitHub personal de Pietro — esta carpeta)
├── meta_ads_mcp/             # código konquest vendorizado (MIT, atribución intacta)
│   ├── server.py             # + parche allowlist solo-lectura
│   └── ... (core/*, api.py, auth.py, etc. sin cambios)
├── .mcp.json                 # registro del server para Claude Code — SIN secretos
├── .env.example              # plantilla: META_ACCESS_TOKEN=...
├── .gitignore                # incluye .env  ← el token nunca entra a git
├── setup.sh                  # onboarding 1 comando (macOS/Linux)
├── setup.ps1                 # onboarding 1 comando (Windows / PowerShell)
├── pyproject.toml / uv.lock  # deps konquest + python-dotenv
├── LICENSE                   # MIT original + atribución a konquest/AgentStack
└── README.md                 # guía del trabajador (español)
```

El repo es **esta carpeta** (`meta-mcp`), privada, en la **cuenta personal de GitHub** de
Pietro (`pietro-narkan`) — **sin organización**. Los trabajadores se añaden como
**colaboradores**. Se vendoriza konquest (MIT lo permite, conservando copyright/aviso) en
vez de un fork público, para distribuirlo en privado y aplicar el recorte.

## 5. Garantía de solo-lectura (doble candado)

1. **Allowlist en `server.py`** (parche ~15 líneas): se reemplaza `mcp.tool` antes de
   importar los módulos `core/*`, de modo que solo se registran las tools de la allowlist;
   las de escritura simplemente no se registran. Enfoque independiente de la versión de
   FastMCP (no toca internals privados). Cambiar de solo-lectura a gestión en el futuro =
   editar el set.
2. **El token es `ads_read`**: aunque una tool de escritura se colara, Meta rechaza toda
   mutación. Imposible gastar/crear/borrar.

### 5.1 Allowlist de tools

**Núcleo confirmado (probado en vivo con el token o lectura del mismo objeto):**
`check_token_status`, `get_ad_accounts`, `discover_all_accounts`, `get_campaigns`,
`get_campaign_details`, `get_adsets`, `get_adset_details`, `get_ads`, `get_ad_details`,
`get_ad_creatives`, `get_creative_details`, `get_insights`, `get_bulk_insights`,
`get_account_info`.

**Candidatas (se incluyen solo si pasan una prueba en vivo con el token durante la
implementación; pueden requerir scopes mayores):** `search_interests`, `search_behaviors`,
`search_geo_locations`, `get_interest_suggestions`, `search_demographics`,
`estimate_audience_size`, `get_account_pages`, `get_instagram_identities`, `get_ad_image`,
`poll_video_processing`.

**Helpers locales (sin llamada a Meta, opcionales):** `run_setup_check`, `generate_names`,
`diagnose_pixel_on_site`.

**Excluidas (requieren scopes que el token no tiene):** todas las de píxeles
(`get_pixel_info`, `get_pixel_events`, `get_event_stats`, `run_tracking_diagnostic`),
catálogos (`get_catalog_info`, `get_catalog_products`, `get_product_sets`,
`validate_catalog_connections`), `list_custom_audiences`, `resolve_page_identity` (escribe
archivo local) y **todas las 19 de escritura/gestión**.

## 6. Configuración y manejo de secretos

- konquest lee `META_ACCESS_TOKEN` de `os.environ` y **no** carga `.env` por sí solo. Se
  añade `python-dotenv` + `load_dotenv()` al arranque del servidor para cargar `.env`.
- `.env` (gitignored) contiene `META_ACCESS_TOKEN=<token solo-lectura compartido>`.
- `.mcp.json` (commiteado, **sin** secretos) registra el server:
  `uv --directory <ruta> run python -m meta_ads_mcp`. Este comando es **multiplataforma**
  (uv corre igual en macOS y Windows); cada script de setup (`setup.sh`/`setup.ps1`) escribe
  la ruta correcta para su SO. Cargar `.env` con `python-dotenv` evita un launcher de bash,
  lo que mantiene el arranque idéntico en ambos sistemas.
- `META_APP_SECRET` (appsecret_proof) y `META_APP_ID` quedan **opcionales**, fuera del MVP
  por simplicidad; se documentan como endurecimiento opcional.
- El token se entrega a cada trabajador **fuera de banda** (gestor de contraseñas) y
  `setup.sh` lo pega en `.env`. Nunca por git ni en `.mcp.json`.

## 7. Onboarding del trabajador

```
# macOS / Linux:               # Windows (PowerShell):
git clone <repo-privado>        git clone <repo-privado>
cd meta-mcp                     cd meta-mcp
./setup.sh                      .\setup.ps1
# luego: abrir Claude Code en la carpeta → preguntar
```

`setup.sh` (macOS/Linux) y `setup.ps1` (Windows) hacen lo mismo:
1. Verifica/instala `uv` si falta (instalador oficial por SO).
2. `uv sync` (instala deps + python-dotenv).
3. Si no existe `.env`, lo crea desde `.env.example` y pide el token una vez (lo pega).
4. Genera/ajusta `.mcp.json` con la ruta correcta del repo para ese SO.
5. **Health-check**: corre `check_token_status` y lista las cuentas accesibles; si el token
   es inválido, avisa claramente.

README explica además: qué se puede preguntar (ejemplos), que es solo-lectura, y cómo el
admin rota el token compartido si un trabajador se va.

## 8. Seguridad

- Token **solo-lectura** → una fuga implica, como máximo, lectura de datos; jamás gasto,
  edición ni borrado.
- Token **nunca en git** (`.env` gitignored; `.mcp.json` sin secretos).
- Repo **privado** con colaboradores de confianza.
- **Acciones del admin (Pietro):**
  - Rotar la **API key de Dokploy** compartida en el chat de planificación.
  - Rotación del token Meta compartido cuando un trabajador se va (procedimiento en README).
- Endurecimiento opcional futuro: `appsecret_proof`, o tokens por trabajador para
  auditoría/revocación individual.

## 9. Verificación / pruebas

- Durante la implementación, probar cada tool **candidata** con una llamada real contra una
  cuenta activa; incluir en la allowlist solo las que devuelven 200.
- Smoke test del MCP arrancado: `check_token_status` OK, `get_campaigns`/`get_insights` de
  una cuenta devuelven datos.
- Confirmar que ninguna tool de escritura aparece en la lista de tools del MCP (allowlist
  efectiva).

## 10. Parámetros del entorno (confirmados)

- **SO de los trabajadores:** **macOS y Windows nativo** (un trabajador en cada uno). Se
  incluyen ambos scripts: `setup.sh` (macOS) y `setup.ps1` (Windows). uv y python-dotenv son
  multiplataforma, así que el server y `.mcp.json` son idénticos en ambos.
- **Repo destino:** **esta carpeta** (`meta-mcp`), privada, en la **cuenta personal de
  GitHub** de Pietro (`pietro-narkan`) — sin organización. Trabajadores como colaboradores.

## 11. Fase 2 (futuro, no ahora)

Si más adelante se quiere **gestión** (crear/editar/pausar campañas): nuevo token con
`ads_management`, posible revisión de la app en Meta, ampliar la allowlist con tools de
escritura y apoyarse en las "safety tiers" de konquest (confirmación humana antes de
escribir). Diseño separado.
