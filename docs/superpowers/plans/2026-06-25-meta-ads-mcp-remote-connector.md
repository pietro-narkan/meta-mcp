# Conector web remoto (claude.ai) de Meta Ads — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir un servidor MCP remoto de solo lectura (Streamable HTTP, paquete `fastmcp`) con OAuth (Google, un solo email permitido), desplegable en Dokploy en `mcp.plasa.cl`, usable como conector personalizado desde claude.ai en el navegador.

**Architecture:** Servicio Python independiente bajo `remote/` (su propio uv/pyproject), distinto del build local. `fastmcp` expone las 11 tools de reporting sobre la Graph API v25.0, en transporte Streamable HTTP stateless. `OAuthProxy` presenta OAuth 2.1+PKCE a claude.ai y delega el login a Google; un verificador JWT valida el ID token y exige que el email esté en una allowlist. Se despliega como contenedor Docker tras Traefik (TLS automático).

**Tech Stack:** Python 3.12, uv, `fastmcp` (gofastmcp.com) ≥2.12, `uvicorn`, `httpx`, `starlette` (CORS), `pytest`/`pytest-asyncio`/`respx`. Docker + Dokploy + Traefik.

## Global Constraints

- **Ubicación:** todo el servicio vive en `remote/` (subdir del repo `meta-mcp`), con su propio `pyproject.toml`/`uv.lock`/`.python-version` (3.12). NO se toca el paquete local `meta_ads_mcp/`.
- **Paquete:** `fastmcp` (de gofastmcp.com), NO el `mcp` SDK base. Import: `from fastmcp import FastMCP`.
- **Solo lectura:** el servicio contiene ÚNICAMENTE las 11 tools de lectura; no existe código de escritura.
- **Tools (exactas, 11):** `check_token_status, get_ad_accounts, discover_all_accounts, get_campaigns, get_campaign_details, get_adsets, get_adset_details, get_ads, get_ad_details, get_insights, get_bulk_insights`.
- **Transporte:** Streamable HTTP, endpoint `/mcp`, `stateless_http=True`.
- **Graph API:** `https://graph.facebook.com/v25.0` (constante).
- **Auth:** `OAuthProxy` → Google. `JWTVerifier`: `jwks_uri=https://www.googleapis.com/.well-known/jwks.json`, `issuer=https://accounts.google.com`, `audience=$GOOGLE_CLIENT_ID`. Allowlist por `ALLOWED_EMAILS` (default `agencia.narkan@gmail.com`); exigir `email_verified==true`. `base_url=$MCP_BASE_URL` (`https://mcp.plasa.cl`). Redirect de claude.ai aceptado: `https://claude.ai/api/mcp/auth_callback`. Redirect de Google (en la app de Google): `https://mcp.plasa.cl/auth/callback`.
- **CORS:** `allow_origins=["https://claude.ai"]`, `expose_headers=["Mcp-Session-Id"]`, `allow_headers` incluye `Authorization, Content-Type, Mcp-Session-Id, MCP-Protocol-Version`.
- **Secretos solo en env (Dokploy), nunca en git:** `META_ACCESS_TOKEN`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_CLIENT_ID`, `MCP_BASE_URL`, `ALLOWED_EMAILS`. `.env` ya está gitignored globalmente.
- **Dominio:** `mcp.plasa.cl`, TLS por Traefik/Let's Encrypt. Endpoint `/health` → 200.
- README/mensajes en español.

## File Structure

```
remote/
├── app/
│   ├── __init__.py
│   ├── config.py     # lee env: token, google creds, base_url, allowed_emails
│   ├── meta.py       # MetaClient: GET async a Graph v25.0
│   ├── tools.py      # las 11 funciones async + TOOLS + get_client()
│   ├── auth.py       # is_email_allowed() + build_auth() (OAuthProxy→Google)
│   └── server.py     # FastMCP + registra tools + auth + CORS + /health + `app` ASGI
├── tests/
│   ├── conftest.py
│   ├── test_meta.py
│   ├── test_tools_accounts.py
│   ├── test_tools_hierarchy.py
│   ├── test_tools_insights.py
│   └── test_auth.py
├── pyproject.toml / uv.lock / .python-version
├── Dockerfile
├── .env.example
└── README.md
```

---

### Task 1: Scaffold del servicio `remote/`

**Files:**
- Create: `remote/pyproject.toml`, `remote/.python-version`, `remote/app/__init__.py`, `remote/app/config.py`, `remote/tests/__init__.py`
- Test: (verificación de import)

**Interfaces:**
- Produces: proyecto uv instalable en `remote/`; `app.config` con constantes/lectura de env.

- [ ] **Step 1: Crear `remote/.python-version`**

Contenido exacto: `3.12`

- [ ] **Step 2: Crear `remote/pyproject.toml`**

```toml
[project]
name = "narkan-meta-remote"
version = "0.1.0"
requires-python = ">=3.12,<3.13"
dependencies = [
    "fastmcp>=2.12",
    "uvicorn>=0.30",
    "httpx>=0.28",
    "starlette>=0.40",
]

[dependency-groups]
dev = ["pytest>=8", "pytest-asyncio>=0.24", "respx>=0.21"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
pythonpath = ["."]
```

- [ ] **Step 3: Crear archivos vacíos del paquete**

`remote/app/__init__.py` (vacío) y `remote/tests/__init__.py` (vacío).

- [ ] **Step 4: Crear `remote/app/config.py`**

```python
"""Configuración leída del entorno (sin secretos hardcodeados)."""
import os

GRAPH_VERSION = "v25.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
MCP_BASE_URL = os.environ.get("MCP_BASE_URL", "https://mcp.plasa.cl")
ALLOWED_EMAILS = {
    e.strip().lower()
    for e in os.environ.get("ALLOWED_EMAILS", "agencia.narkan@gmail.com").split(",")
    if e.strip()
}
```

- [ ] **Step 5: Instalar y verificar import**

Run (desde `remote/`): `cd remote && uv sync && uv run python -c "import app.config; print('config ok', app.config.GRAPH_BASE)"`
Expected: instala deps e imprime `config ok https://graph.facebook.com/v25.0`.

- [ ] **Step 6: Commit**

```bash
git add remote/pyproject.toml remote/uv.lock remote/.python-version remote/app/__init__.py remote/app/config.py remote/tests/__init__.py
git commit -m "feat(remote): scaffold del servicio MCP remoto (uv + fastmcp)"
```

---

### Task 2: Cliente Graph (`remote/app/meta.py`)

**Files:**
- Create: `remote/app/meta.py`
- Test: `remote/tests/test_meta.py`, `remote/tests/conftest.py`

**Interfaces:**
- Consumes: `app.config.GRAPH_BASE`.
- Produces: `class MetaClient` con `__init__(self, token: str)` y `async def get(self, path: str, params: dict | None = None) -> dict`. Lanza `MetaError(message)` en respuesta no-200.

- [ ] **Step 1: Crear `remote/tests/conftest.py`**

```python
import os
os.environ.setdefault("META_ACCESS_TOKEN", "TEST_DUMMY_TOKEN")
```

- [ ] **Step 2: Escribir el test que falla**

```python
# remote/tests/test_meta.py
import httpx
import pytest
import respx

from app.meta import MetaClient, MetaError


@respx.mock
async def test_get_builds_url_and_returns_json():
    route = respx.get("https://graph.facebook.com/v25.0/act_123/campaigns").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "1"}]})
    )
    client = MetaClient("TOK")
    out = await client.get("act_123/campaigns", {"fields": "id"})
    assert out == {"data": [{"id": "1"}]}
    assert route.called
    sent = route.calls.last.request
    assert sent.url.params["access_token"] == "TOK"
    assert sent.url.params["fields"] == "id"


@respx.mock
async def test_get_raises_metaerror_on_http_error():
    respx.get("https://graph.facebook.com/v25.0/me").mock(
        return_value=httpx.Response(400, json={"error": {"message": "Bad token"}})
    )
    client = MetaClient("TOK")
    with pytest.raises(MetaError) as exc:
        await client.get("me")
    assert "Bad token" in str(exc.value)
```

- [ ] **Step 3: Ejecutar el test y verificar que falla**

Run: `cd remote && uv run pytest tests/test_meta.py -v`
Expected: FAIL con `ModuleNotFoundError: app.meta`.

- [ ] **Step 4: Crear `remote/app/meta.py`**

```python
"""Cliente HTTP mínimo de solo lectura para la Meta Graph API."""
from __future__ import annotations

import httpx

from app.config import GRAPH_BASE


class MetaError(Exception):
    """Error devuelto por la Graph API o de red."""


class MetaClient:
    def __init__(self, token: str):
        self._token = token

    async def get(self, path: str, params: dict | None = None) -> dict:
        query = dict(params or {})
        query["access_token"] = self._token
        url = f"{GRAPH_BASE}/{path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url, params=query)
        except httpx.HTTPError as exc:  # red
            raise MetaError(f"Error de red: {exc}") from exc
        if resp.status_code != 200:
            try:
                msg = resp.json().get("error", {}).get("message", resp.text[:200])
            except Exception:
                msg = resp.text[:200]
            raise MetaError(f"Graph API {resp.status_code}: {msg}")
        return resp.json()
```

- [ ] **Step 5: Ejecutar el test y verificar que pasa**

Run: `cd remote && uv run pytest tests/test_meta.py -v`
Expected: PASS (2 tests).

- [ ] **Step 6: Commit**

```bash
git add remote/app/meta.py remote/tests/test_meta.py remote/tests/conftest.py
git commit -m "feat(remote): cliente Graph v25.0 de solo lectura (MetaClient)"
```

---

### Task 3: Tools de cuenta/token (`remote/app/tools.py` — parte 1)

**Files:**
- Create: `remote/app/tools.py`
- Test: `remote/tests/test_tools_accounts.py`

**Interfaces:**
- Consumes: `app.meta.MetaClient`, `app.config`.
- Produces:
  - `def get_client() -> MetaClient` (singleton desde `config.META_ACCESS_TOKEN`; los tests lo monkeypatchean).
  - `async def check_token_status() -> dict`
  - `async def get_ad_accounts() -> dict`
  - `async def discover_all_accounts() -> dict`
  - `TOOLS: list` (acumula las funciones-tool; al final tendrá 11).

- [ ] **Step 1: Escribir el test que falla**

```python
# remote/tests/test_tools_accounts.py
import pytest
from app import tools


class FakeClient:
    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    async def get(self, path, params=None):
        self.calls.append((path, params))
        return self._responses[path]


@pytest.fixture
def fake(monkeypatch):
    def _install(responses):
        client = FakeClient(responses)
        monkeypatch.setattr(tools, "get_client", lambda: client)
        return client
    return _install


async def test_get_ad_accounts_shapes_output(fake):
    fake({"me/adaccounts": {"data": [
        {"account_id": "111", "name": "Bellas Todas", "account_status": 1, "currency": "CLP"},
    ]}})
    out = await tools.get_ad_accounts()
    assert out["total"] == 1
    assert out["accounts"][0]["id"] == "act_111"
    assert out["accounts"][0]["name"] == "Bellas Todas"
    assert out["accounts"][0]["active"] is True


async def test_check_token_status_reports_valid(fake):
    fake({"me": {"id": "123", "name": "plasa-backend"}})
    out = await tools.check_token_status()
    assert out["valid"] is True
    assert out["name"] == "plasa-backend"


async def test_discover_all_accounts_lists_ids(fake):
    fake({"me/adaccounts": {"data": [
        {"account_id": "111", "name": "A", "account_status": 1, "currency": "CLP"},
        {"account_id": "222", "name": "B", "account_status": 101, "currency": "CLP"},
    ]}})
    out = await tools.discover_all_accounts()
    assert {a["id"] for a in out["accounts"]} == {"act_111", "act_222"}
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd remote && uv run pytest tests/test_tools_accounts.py -v`
Expected: FAIL (`ModuleNotFoundError: app.tools`).

- [ ] **Step 3: Crear `remote/app/tools.py`**

```python
"""Las 11 tools de solo lectura sobre la Meta Graph API.

Funciones async simples; el servidor las registra con @mcp.tool. El cliente Graph
se obtiene de get_client() (los tests lo sustituyen).
"""
from __future__ import annotations

from app import config
from app.meta import MetaClient

_client: MetaClient | None = None


def get_client() -> MetaClient:
    global _client
    if _client is None:
        _client = MetaClient(config.META_ACCESS_TOKEN)
    return _client


def _acct(account_id: str) -> str:
    return account_id if account_id.startswith("act_") else f"act_{account_id}"


def _shape_accounts(data: list[dict]) -> list[dict]:
    out = []
    for a in data:
        out.append({
            "id": _acct(str(a.get("account_id", ""))),
            "name": a.get("name"),
            "account_status": a.get("account_status"),
            "active": a.get("account_status") == 1,
            "currency": a.get("currency"),
        })
    return out


async def check_token_status() -> dict:
    """Valida el token actual y devuelve el usuario del System User."""
    me = await get_client().get("me", {"fields": "id,name"})
    return {"valid": True, "id": me.get("id"), "name": me.get("name")}


async def get_ad_accounts() -> dict:
    """Lista las cuentas publicitarias accesibles por el token."""
    res = await get_client().get(
        "me/adaccounts",
        {"fields": "account_id,name,account_status,currency", "limit": "200"},
    )
    accounts = _shape_accounts(res.get("data", []))
    return {"total": len(accounts), "accounts": accounts}


async def discover_all_accounts() -> dict:
    """Igual que get_ad_accounts (alias de descubrimiento)."""
    return await get_ad_accounts()


TOOLS = [check_token_status, get_ad_accounts, discover_all_accounts]
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd remote && uv run pytest tests/test_tools_accounts.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add remote/app/tools.py remote/tests/test_tools_accounts.py
git commit -m "feat(remote): tools de cuenta/token (check_token_status, get_ad_accounts, discover_all_accounts)"
```

---

### Task 4: Tools de jerarquía (`remote/app/tools.py` — parte 2)

**Files:**
- Modify: `remote/app/tools.py`
- Test: `remote/tests/test_tools_hierarchy.py`

**Interfaces:**
- Produces (añade a `tools.py` y a `TOOLS`):
  - `async def get_campaigns(account_id: str) -> dict`
  - `async def get_campaign_details(campaign_id: str) -> dict`
  - `async def get_adsets(account_id: str) -> dict`
  - `async def get_adset_details(adset_id: str) -> dict`
  - `async def get_ads(account_id: str) -> dict`
  - `async def get_ad_details(ad_id: str) -> dict`

- [ ] **Step 1: Escribir el test que falla**

```python
# remote/tests/test_tools_hierarchy.py
import pytest
from app import tools


class FakeClient:
    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    async def get(self, path, params=None):
        self.calls.append((path, params))
        return self._responses[path]


@pytest.fixture
def fake(monkeypatch):
    def _install(responses):
        client = FakeClient(responses)
        monkeypatch.setattr(tools, "get_client", lambda: client)
        return client
    return _install


async def test_get_campaigns_counts_statuses(fake):
    c = fake({"act_111/campaigns": {"data": [
        {"id": "1", "name": "C1", "status": "ACTIVE", "effective_status": "ACTIVE", "objective": "OUTCOME_SALES"},
        {"id": "2", "name": "C2", "status": "PAUSED", "effective_status": "PAUSED", "objective": "OUTCOME_SALES"},
    ]}})
    out = await tools.get_campaigns("111")  # acepta sin act_
    assert out["total"] == 2
    assert out["status_counts"] == {"ACTIVE": 1, "PAUSED": 1}
    assert out["campaigns"][0]["name"] == "C1"
    assert c.calls[0][0] == "act_111/campaigns"


async def test_get_campaign_details_returns_node(fake):
    fake({"120": {"id": "120", "name": "Camp", "status": "ACTIVE", "objective": "OUTCOME_SALES"}})
    out = await tools.get_campaign_details("120")
    assert out["id"] == "120" and out["name"] == "Camp"


async def test_get_adsets_and_ads(fake):
    fake({
        "act_9/adsets": {"data": [{"id": "a1", "name": "AS", "status": "PAUSED", "daily_budget": "2000"}]},
        "act_9/ads": {"data": [{"id": "d1", "name": "AD", "status": "ACTIVE"}]},
    })
    asets = await tools.get_adsets("act_9")
    ads = await tools.get_ads("act_9")
    assert asets["adsets"][0]["daily_budget"] == "2000"
    assert ads["ads"][0]["id"] == "d1"
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd remote && uv run pytest tests/test_tools_hierarchy.py -v`
Expected: FAIL (`AttributeError: ... get_campaigns`).

- [ ] **Step 3: Añadir a `remote/app/tools.py` (antes de la línea `TOOLS = [...]`)**

```python
_CAMPAIGN_FIELDS = "id,name,status,effective_status,objective,daily_budget,lifetime_budget,start_time,stop_time,created_time,updated_time"
_ADSET_FIELDS = "id,name,status,effective_status,daily_budget,lifetime_budget,optimization_goal,billing_event"
_AD_FIELDS = "id,name,status,effective_status,created_time,updated_time"


def _status_counts(rows: list[dict]) -> dict:
    counts: dict[str, int] = {}
    for r in rows:
        s = r.get("status", "UNKNOWN")
        counts[s] = counts.get(s, 0) + 1
    return counts


async def get_campaigns(account_id: str) -> dict:
    """Lista las campañas de una cuenta (con conteo por estado)."""
    res = await get_client().get(f"{_acct(account_id)}/campaigns", {"fields": _CAMPAIGN_FIELDS, "limit": "100"})
    rows = res.get("data", [])
    return {"total": len(rows), "status_counts": _status_counts(rows), "campaigns": rows}


async def get_campaign_details(campaign_id: str) -> dict:
    """Detalle de una campaña por id."""
    return await get_client().get(campaign_id, {"fields": _CAMPAIGN_FIELDS})


async def get_adsets(account_id: str) -> dict:
    """Lista los conjuntos de anuncios de una cuenta."""
    res = await get_client().get(f"{_acct(account_id)}/adsets", {"fields": _ADSET_FIELDS, "limit": "100"})
    rows = res.get("data", [])
    return {"total": len(rows), "status_counts": _status_counts(rows), "adsets": rows}


async def get_adset_details(adset_id: str) -> dict:
    """Detalle de un conjunto de anuncios por id."""
    return await get_client().get(adset_id, {"fields": _ADSET_FIELDS})


async def get_ads(account_id: str) -> dict:
    """Lista los anuncios de una cuenta."""
    res = await get_client().get(f"{_acct(account_id)}/ads", {"fields": _AD_FIELDS, "limit": "100"})
    rows = res.get("data", [])
    return {"total": len(rows), "status_counts": _status_counts(rows), "ads": rows}


async def get_ad_details(ad_id: str) -> dict:
    """Detalle de un anuncio por id."""
    return await get_client().get(ad_id, {"fields": _AD_FIELDS})
```

Y actualizar la línea de `TOOLS`:

```python
TOOLS = [
    check_token_status, get_ad_accounts, discover_all_accounts,
    get_campaigns, get_campaign_details, get_adsets, get_adset_details,
    get_ads, get_ad_details,
]
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd remote && uv run pytest tests/test_tools_hierarchy.py -v`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add remote/app/tools.py remote/tests/test_tools_hierarchy.py
git commit -m "feat(remote): tools de jerarquía (campañas/adsets/ads)"
```

---

### Task 5: Tools de insights (`remote/app/tools.py` — parte 3)

**Files:**
- Modify: `remote/app/tools.py`
- Test: `remote/tests/test_tools_insights.py`

**Interfaces:**
- Produces:
  - `async def get_insights(account_id: str, date_preset: str = "last_30d") -> dict`
  - `async def get_bulk_insights(account_id: str, level: str = "campaign", date_preset: str = "last_30d") -> dict`
  - `TOOLS` queda con las 11.

- [ ] **Step 1: Escribir el test que falla**

```python
# remote/tests/test_tools_insights.py
import pytest
from app import tools


class FakeClient:
    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    async def get(self, path, params=None):
        self.calls.append((path, params))
        return self._responses[path]


@pytest.fixture
def fake(monkeypatch):
    def _install(responses):
        client = FakeClient(responses)
        monkeypatch.setattr(tools, "get_client", lambda: client)
        return client
    return _install


async def test_get_insights_passes_date_preset(fake):
    c = fake({"act_5/insights": {"data": [{"spend": "184908", "impressions": "42178", "clicks": "1740", "ctr": "4.12"}]}})
    out = await tools.get_insights("5", date_preset="last_7d")
    assert out["data"][0]["spend"] == "184908"
    assert c.calls[0][1]["date_preset"] == "last_7d"


async def test_get_bulk_insights_uses_level(fake):
    c = fake({"act_5/insights": {"data": [{"campaign_name": "C", "spend": "10"}]}})
    out = await tools.get_bulk_insights("act_5", level="adset", date_preset="maximum")
    assert out["level"] == "adset"
    assert c.calls[0][1]["level"] == "adset"
    assert c.calls[0][1]["date_preset"] == "maximum"


def test_tools_has_exactly_eleven():
    names = [f.__name__ for f in tools.TOOLS]
    assert len(names) == 11
    assert "get_insights" in names and "get_bulk_insights" in names
    # ninguna de escritura
    assert not any(n.startswith(("create_", "update_", "delete_", "upload_", "duplicate_")) for n in names)
```

- [ ] **Step 2: Ejecutar y verificar que falla**

Run: `cd remote && uv run pytest tests/test_tools_insights.py -v`
Expected: FAIL (`AttributeError: get_insights`).

- [ ] **Step 3: Añadir a `remote/app/tools.py` (antes de `TOOLS`)**

```python
_INSIGHT_FIELDS = "spend,impressions,clicks,ctr,cpc,cpm,reach,frequency"


async def get_insights(account_id: str, date_preset: str = "last_30d") -> dict:
    """Métricas agregadas de una cuenta para un periodo (date_preset)."""
    res = await get_client().get(
        f"{_acct(account_id)}/insights",
        {"fields": _INSIGHT_FIELDS, "date_preset": date_preset},
    )
    return {"date_preset": date_preset, "data": res.get("data", [])}


async def get_bulk_insights(account_id: str, level: str = "campaign", date_preset: str = "last_30d") -> dict:
    """Métricas desglosadas por nivel (campaign|adset|ad) para un periodo."""
    res = await get_client().get(
        f"{_acct(account_id)}/insights",
        {
            "fields": f"{level}_name,{_INSIGHT_FIELDS}",
            "level": level,
            "date_preset": date_preset,
            "limit": "200",
        },
    )
    return {"level": level, "date_preset": date_preset, "data": res.get("data", [])}
```

Y dejar `TOOLS` con las 11:

```python
TOOLS = [
    check_token_status, get_ad_accounts, discover_all_accounts,
    get_campaigns, get_campaign_details, get_adsets, get_adset_details,
    get_ads, get_ad_details, get_insights, get_bulk_insights,
]
```

- [ ] **Step 4: Ejecutar y verificar que pasa**

Run: `cd remote && uv run pytest tests/ -v`
Expected: PASS (toda la suite, incl. `test_tools_has_exactly_eleven`).

- [ ] **Step 5: Commit**

```bash
git add remote/app/tools.py remote/tests/test_tools_insights.py
git commit -m "feat(remote): tools de insights y verificación de 11 tools solo-lectura"
```

---

### Task 6: Autenticación (`remote/app/auth.py`)

**Files:**
- Create: `remote/app/auth.py`
- Test: `remote/tests/test_auth.py`

**Interfaces:**
- Consumes: `app.config` (GOOGLE_*, MCP_BASE_URL, ALLOWED_EMAILS).
- Produces:
  - `def is_email_allowed(claims: dict, allowed: set[str]) -> bool` (pura, testeable).
  - `def build_auth()` → instancia de auth de fastmcp lista para pasar a `FastMCP(auth=...)`.

- [ ] **Step 1: Descubrir la API instalada de fastmcp (evita adivinar firmas)**

Run: `cd remote && uv run python -c "import fastmcp, inspect; from fastmcp.server.auth import OAuthProxy; from fastmcp.server.auth.providers.jwt import JWTVerifier; print('fastmcp', fastmcp.__version__); print('OAuthProxy', inspect.signature(OAuthProxy.__init__)); print('JWTVerifier', inspect.signature(JWTVerifier.__init__))"`
Expected: imprime la versión y las firmas reales. **Usa esas firmas**; si difieren de las de abajo (nombres de parámetros), ajusta `build_auth()` en consecuencia y anótalo en el reporte. Si los imports fallan (ruta del módulo cambió), localiza la correcta con `uv run python -c "import fastmcp.server.auth as a; print(dir(a))"`.

- [ ] **Step 2: Escribir el test que falla (solo la política de allowlist, que es pura)**

```python
# remote/tests/test_auth.py
from app.auth import is_email_allowed

ALLOWED = {"agencia.narkan@gmail.com"}


def test_allows_exact_verified_email():
    assert is_email_allowed({"email": "agencia.narkan@gmail.com", "email_verified": True}, ALLOWED) is True


def test_rejects_other_email():
    assert is_email_allowed({"email": "otro@gmail.com", "email_verified": True}, ALLOWED) is False


def test_rejects_unverified_email():
    assert is_email_allowed({"email": "agencia.narkan@gmail.com", "email_verified": False}, ALLOWED) is False


def test_is_case_insensitive_and_handles_missing():
    assert is_email_allowed({"email": "Agencia.Narkan@Gmail.com", "email_verified": True}, ALLOWED) is True
    assert is_email_allowed({}, ALLOWED) is False
```

- [ ] **Step 3: Ejecutar y verificar que falla**

Run: `cd remote && uv run pytest tests/test_auth.py -v`
Expected: FAIL (`ModuleNotFoundError: app.auth`).

- [ ] **Step 4: Crear `remote/app/auth.py`**

```python
"""OAuth para claude.ai: OAuthProxy delega a Google; allowlist por email."""
from __future__ import annotations

from app import config


def is_email_allowed(claims: dict, allowed: set[str]) -> bool:
    """True solo si el email está verificado y en la allowlist (case-insensitive)."""
    email = (claims.get("email") or "").strip().lower()
    if not email or not claims.get("email_verified"):
        return False
    return email in {a.strip().lower() for a in allowed}


def build_auth():
    """Construye el proveedor de auth de fastmcp (OAuthProxy → Google).

    Ajusta los nombres de parámetros a la firma real descubierta en el Step 1
    de esta tarea si difieren.
    """
    from fastmcp.server.auth import OAuthProxy
    from fastmcp.server.auth.providers.jwt import JWTVerifier

    class _AllowlistVerifier(JWTVerifier):
        async def verify_token(self, token: str):
            result = await super().verify_token(token)
            if result is None:
                return None
            claims = getattr(result, "claims", None) or {}
            return result if is_email_allowed(claims, config.ALLOWED_EMAILS) else None

    verifier = _AllowlistVerifier(
        jwks_uri="https://www.googleapis.com/.well-known/jwks.json",
        issuer="https://accounts.google.com",
        audience=config.GOOGLE_CLIENT_ID,
    )
    return OAuthProxy(
        upstream_authorization_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
        upstream_token_endpoint="https://oauth2.googleapis.com/token",
        upstream_client_id=config.GOOGLE_CLIENT_ID,
        upstream_client_secret=config.GOOGLE_CLIENT_SECRET,
        token_verifier=verifier,
        base_url=config.MCP_BASE_URL,
    )
```

- [ ] **Step 5: Ejecutar y verificar que pasa**

Run: `cd remote && uv run pytest tests/test_auth.py -v`
Expected: PASS (4 tests). (Nota: `build_auth()` no se ejecuta en estos tests; se valida en el smoke/despliegue.)

- [ ] **Step 6: Commit**

```bash
git add remote/app/auth.py remote/tests/test_auth.py
git commit -m "feat(remote): auth OAuthProxy->Google con allowlist de email"
```

---

### Task 7: Ensamblado del servidor (`remote/app/server.py`)

**Files:**
- Create: `remote/app/server.py`

**Interfaces:**
- Consumes: `tools.TOOLS`, `auth.build_auth`.
- Produces: objeto ASGI `app` (servible por uvicorn) que monta el MCP Streamable HTTP en `/mcp`, CORS para claude.ai, y `/health`.

- [ ] **Step 1: Descubrir la API de http_app/stateless de la versión instalada**

Run: `cd remote && uv run python -c "import inspect; from fastmcp import FastMCP; print('http_app', inspect.signature(FastMCP.http_app))"`
Expected: imprime la firma de `http_app`. Si admite `stateless_http`, pásalo; si no, busca el parámetro equivalente con `print([p for p in inspect.signature(FastMCP.http_app).parameters])` y úsalo. Anota lo que encuentres.

- [ ] **Step 2: Crear `remote/app/server.py`**

```python
"""Servidor MCP remoto Streamable HTTP para claude.ai (solo lectura)."""
from __future__ import annotations

from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import tools
from app.auth import build_auth

mcp = FastMCP("Narkan Meta Ads (solo lectura)", auth=build_auth())

for _fn in tools.TOOLS:
    mcp.tool(_fn)


@mcp.custom_route("/health", methods=["GET"])
async def _health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# ASGI app con el MCP en /mcp (stateless). Ajusta el kwarg si el Step 1 mostró otro nombre.
app = mcp.http_app(stateless_http=True)

# CORS para claude.ai
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://claude.ai"],
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "Mcp-Session-Id", "MCP-Protocol-Version"],
    expose_headers=["Mcp-Session-Id"],
    allow_credentials=True,
)
```

- [ ] **Step 3: Verificar import y arranque básico (sin credenciales reales)**

Run: `cd remote && env GOOGLE_CLIENT_ID=test GOOGLE_CLIENT_SECRET=test uv run python -c "from app.server import app; print('app ok', type(app).__name__)"`
Expected: imprime `app ok ...` sin excepción. Si `build_auth()` exige red al construir y falla, captúralo y repórtalo (puede requerir mover la construcción del verifier a lazy); de lo contrario, OK.

- [ ] **Step 4: Verificar `/health` y que `/mcp` exige auth**

```bash
cd remote && env GOOGLE_CLIENT_ID=test GOOGLE_CLIENT_SECRET=test META_ACCESS_TOKEN=dummy \
  uv run uvicorn app.server:app --host 127.0.0.1 --port 8011 &
sleep 3
curl -s -o /dev/null -w "health=%{http_code}\n" http://127.0.0.1:8011/health
curl -s -o /dev/null -w "mcp_noauth=%{http_code}\n" -X POST http://127.0.0.1:8011/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
kill %1 2>/dev/null
```
Expected: `health=200`. `mcp_noauth` debe ser `401` (o `400/406` si pide headers de protocolo) — el punto es que NO devuelve 200 con la lista de tools sin auth. Anota el código real.

- [ ] **Step 5: Commit**

```bash
git add remote/app/server.py
git commit -m "feat(remote): ensamblado del servidor (Streamable HTTP + CORS + /health)"
```

---

### Task 8: Empaquetado (Dockerfile, .env.example, README)

**Files:**
- Create: `remote/Dockerfile`, `remote/.env.example`, `remote/README.md`, `remote/.dockerignore`

- [ ] **Step 1: Crear `remote/Dockerfile`**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir uv
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev
COPY app ./app
ENV HOST=0.0.0.0 PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"
CMD ["uv", "run", "uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: Crear `remote/.dockerignore`**

```
.venv/
__pycache__/
*.pyc
.env
tests/
```

- [ ] **Step 3: Crear `remote/.env.example`**

```bash
# Token de Meta de SOLO LECTURA (System User, ads_read). Solo en Dokploy, nunca en git.
META_ACCESS_TOKEN=pega_el_token_de_solo_lectura
# App OAuth de Google (Google Cloud Console, cuenta agencia.narkan)
GOOGLE_CLIENT_ID=xxxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxx
# URL pública exacta del conector (sin barra final)
MCP_BASE_URL=https://mcp.plasa.cl
# Correos autorizados (separados por coma)
ALLOWED_EMAILS=agencia.narkan@gmail.com
```

- [ ] **Step 4: Crear `remote/README.md`**

````markdown
# Meta Ads MCP remoto (claude.ai) — Narkan

Conector web de **solo lectura** para usar Meta Ads desde **claude.ai en el navegador**.
Despliegue en el VPS con Dokploy; los trabajadores lo añaden como conector y entran con Google.

## Variables de entorno (en Dokploy, nunca en git)
Ver `.env.example`: `META_ACCESS_TOKEN`, `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`,
`MCP_BASE_URL`, `ALLOWED_EMAILS`.

## Local
```bash
cd remote
uv sync
env $(grep -v '^#' .env | xargs) uv run uvicorn app.server:app --host 0.0.0.0 --port 8000
# /health -> 200 ; /mcp sin token -> 401
```

## Despliegue (resumen — ver el plan para el detalle)
1. App OAuth de Google con redirect `https://mcp.plasa.cl/auth/callback`.
2. DNS `mcp.plasa.cl` -> IP del VPS.
3. Servicio en Dokploy (build path `remote/`), variables de entorno, dominio `mcp.plasa.cl` con HTTPS.

## Uso (trabajador)
claude.ai -> Ajustes -> Conectores -> Añadir conector -> `https://mcp.plasa.cl` ->
iniciar sesión con `agencia.narkan@gmail.com` -> preguntar.

Solo lectura: imposible crear/editar/gastar. Basado en el reporting de konquest (MIT).
````

- [ ] **Step 5: Verificar build de la imagen Docker**

Run: `cd remote && docker build -t narkan-meta-remote:test . && echo BUILD_OK`
Expected: imprime `BUILD_OK`. (Si `docker` no está disponible en la máquina, omite este step y anótalo; se validará en el despliegue.)

- [ ] **Step 6: Commit**

```bash
git add remote/Dockerfile remote/.dockerignore remote/.env.example remote/README.md
git commit -m "feat(remote): Dockerfile, .env.example y README de despliegue"
```

---

### Task 9: Smoke de integración con token real (lo corre el controlador)

> Requiere el **token real** de solo lectura (lo provee el controlador por env, NO se escribe en git). Valida la ruta de tools end-to-end localmente; la parte OAuth/claude.ai se valida en el despliegue (Tarea 11).

**Files:** ninguno (verificación).

- [ ] **Step 1: Arrancar el server con credenciales de prueba + token real y listar/llamar tools por dentro**

```bash
cd remote && env META_ACCESS_TOKEN="$REAL_TOKEN" uv run python -c "
import asyncio
from app import tools
async def main():
    print('token:', (await tools.check_token_status())['name'])
    accs = await tools.get_ad_accounts()
    print('cuentas:', accs['total'])
    acc = accs['accounts'][0]['id']
    camps = await tools.get_campaigns(acc)
    print('campañas en', acc, ':', camps['total'], camps['status_counts'])
    ins = await tools.get_insights(acc, date_preset='last_30d')
    print('insights filas:', len(ins['data']))
asyncio.run(main())
"
```
Expected: imprime el nombre del System User, el número de cuentas (7), y campañas/insights reales de una cuenta. Esto confirma que las 11 tools operan contra Graph v25.0.

- [ ] **Step 2: (si docker está disponible) Arrancar el contenedor y probar `/health`**

```bash
cd remote && docker run --rm -d -p 8012:8000 --name narkanmcp \
  -e META_ACCESS_TOKEN="$REAL_TOKEN" -e GOOGLE_CLIENT_ID=test -e GOOGLE_CLIENT_SECRET=test -e MCP_BASE_URL=https://mcp.plasa.cl \
  narkan-meta-remote:test
sleep 4
curl -s -o /dev/null -w "health=%{http_code}\n" http://127.0.0.1:8012/health
docker stop narkanmcp
```
Expected: `health=200`.

- [ ] **Step 3: Registrar el resultado** (no hay commit; es verificación).

---

### Task 10: Runbook de despliegue (Google + DNS + Dokploy + firewall)

> Acciones **del usuario** sobre servicios externos; el controlador puede asistir con la API de Dokploy bajo confirmación. No hay código que commitear más allá de documentar.

**Files:**
- Create: `remote/DEPLOY.md` (runbook detallado)

- [ ] **Step 1: Escribir `remote/DEPLOY.md`** con estos pasos concretos:

```markdown
# Despliegue del conector remoto

## 1. App OAuth de Google (cuenta agencia.narkan)
- Google Cloud Console -> APIs & Services -> Credentials -> Create OAuth client ID -> Web application.
- Authorized redirect URI: `https://mcp.plasa.cl/auth/callback`
- Scopes/Consent: `openid`, `email`, `profile` (User type External; añade agencia.narkan como usuario de prueba si la app queda en "Testing").
- Copia Client ID y Client Secret.

## 2. DNS
- Crea un registro A: `mcp.plasa.cl` -> `173.249.49.22`.
- Verifica: `dig +short mcp.plasa.cl` devuelve la IP.

## 3. Servicio en Dokploy
- Nueva Application en el proyecto deseado, fuente = repo GitHub `pietro-narkan/meta-mcp`, **Build Path** = `remote/`, builder = Dockerfile.
- Environment (no en git):
  - META_ACCESS_TOKEN = (token read-only de plaza-backend)
  - GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET = (paso 1)
  - MCP_BASE_URL = https://mcp.plasa.cl
  - ALLOWED_EMAILS = agencia.narkan@gmail.com
- Deploy. Espera a que el healthcheck `/health` esté verde.
- Domains -> añade `mcp.plasa.cl`, container port 8000, HTTPS on (Let's Encrypt). Redeploy si es compose.

## 4. Firewall (opcional, hardening)
- Si el VPS tiene firewall restrictivo, permite entrada desde `160.79.104.0/21` al 443.
- (El endpoint ya está protegido por OAuth + TLS; esto es defensa en profundidad.)

## 5. Verificación
- `curl https://mcp.plasa.cl/health` -> `{"status":"ok"}`.
- `curl https://mcp.plasa.cl/.well-known/oauth-protected-resource` -> JSON cuyo `resource` == `https://mcp.plasa.cl`.
```

- [ ] **Step 2: Commit**

```bash
git add remote/DEPLOY.md
git commit -m "docs(remote): runbook de despliegue (Google, DNS, Dokploy, firewall)"
```

---

### Task 11: Conexión en claude.ai + verificación E2E (usuario)

> Requiere el despliegue de la Tarea 10 ya en marcha. Acción del usuario en claude.ai.

**Files:** ninguno.

- [ ] **Step 1: Añadir el conector en claude.ai**
claude.ai -> Ajustes -> Conectores -> "Añadir conector personalizado" -> URL `https://mcp.plasa.cl` -> conectar -> "Iniciar sesión con Google" con `agencia.narkan@gmail.com` -> aprobar.
Expected: el conector queda "conectado" y aparecen 11 tools de solo lectura.

- [ ] **Step 2: Probar una consulta real**
En un chat de claude.ai: "¿Qué campañas activas hay en cada cuenta y cuánto gastaron este mes?"
Expected: responde con datos reales (campañas/gasto de las cuentas).

- [ ] **Step 3: Verificar el rechazo de otra cuenta**
Intenta conectar con una cuenta Google distinta a la allowlist.
Expected: el login es rechazado (no obtiene acceso).

- [ ] **Step 4: Registrar el resultado E2E.**

---

## Notas de implementación

- **Orden:** Tareas 1→8 son secuenciales y testeables localmente por subagentes. Tarea 9 la corre el controlador con el token real (vía API de Dokploy). Tareas 10–11 requieren al usuario (Google, DNS, claude.ai).
- **Incertidumbre de API externa:** las firmas exactas de `OAuthProxy`/`JWTVerifier`/`http_app` se descubren en los Steps de discovery (Tareas 6 y 7); ajustar el wiring a la versión instalada. El bucle de revisión cubre desajustes.
- **Token para Tarea 9:** en Dokploy, proyecto `plaza` → app `plaza-backend` → env `META_SYSTEM_USER_TOKEN` (vía API de Dokploy con `x-api-key`). No se commitea.
- **Pendiente de seguridad heredado:** rotar la API key de Dokploy.
