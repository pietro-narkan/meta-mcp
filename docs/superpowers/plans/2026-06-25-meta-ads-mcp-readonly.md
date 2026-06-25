# Meta Ads MCP (solo-lectura) — Plan de Implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vendorizar konquest-meta-ads-mcp recortado a solo-lectura y empaquetarlo como un repo privado que cada trabajador (macOS o Windows) clona, configura con un comando y consulta desde Claude Code.

**Architecture:** MCP stdio en Python sobre el SDK oficial de MCP (FastMCP). Se copia el paquete `meta_ads_mcp` de konquest (MIT) al repo, se aplica un parche de allowlist en `server.py` que impide registrar cualquier tool de escritura, y se carga el token desde un `.env` (gitignored) vía `python-dotenv`. Scripts de setup por SO generan el `.mcp.json` local y validan el token.

**Tech Stack:** Python 3.11/3.12, uv, `mcp[cli]` (FastMCP), `facebook-business`, `httpx`, `python-dotenv`, `pytest` + `pytest-asyncio`. Bash (setup.sh) y PowerShell (setup.ps1).

## Global Constraints

- **Python:** 3.11 o 3.12 (`requires-python >=3.11`). Gestor: **uv**.
- **Solo lectura:** ninguna tool de escritura/gestión puede registrarse. Doble candado: allowlist + token `ads_read`.
- **Token NUNCA en git.** `.env` y `.mcp.json` van en `.gitignore`. Solo se commitean `.env.example` y `.mcp.json.example`.
- **Multiplataforma:** macOS y Windows nativo. El server y el `.mcp.json` son idénticos; solo cambia el script de setup.
- **Graph API:** konquest usa la constante `v25.0` (verificada funcionando con el token). NO cambiarla.
- **Licencia:** conservar el `LICENSE` MIT de konquest y la atribución a `brandu-mos/konquest-meta-ads-mcp` (copyright "AgentStack").
- **Allowlist núcleo (verbatim, núcleo confirmado en vivo):**
  `check_token_status, get_ad_accounts, discover_all_accounts, get_campaigns, get_campaign_details, get_adsets, get_adset_details, get_ads, get_ad_details, get_insights, get_bulk_insights`
- **Conjunto de ESCRITURA prohibido (verbatim, debe quedar fuera):**
  `create_campaign, update_campaign, create_adset, update_adset, create_ad_from_manifest, update_ad, create_ad_creative, update_ad_creative, create_product_set, update_product_set, upload_ad_image, upload_video_asset, upload_video_resumable, bulk_rename_objects, delete_campaign_structure, create_multi_asset_ad, duplicate_campaign, duplicate_adset, send_test_event`
- **README y mensajes al trabajador en español.**
- Repo destino: **esta carpeta** `meta-mcp`, privada, cuenta GitHub `pietro-narkan`. Rama de trabajo: `feat/readonly-mcp`.

## File Structure

```
meta-mcp/
├── meta_ads_mcp/                 # paquete konquest vendorizado (MIT)
│   ├── __main__.py               # MOD: carga .env antes de arrancar
│   ├── server.py                 # MOD: parche allowlist solo-lectura + READ_ONLY_TOOLS
│   ├── runtime_env.py            # NUEVO: load_environment() (python-dotenv)
│   └── ... (api.py, auth.py, core/*, etc. — sin cambios)
├── scripts/
│   └── healthcheck.py            # NUEVO: valida token y lista cuentas
├── tests/
│   ├── conftest.py               # NUEVO: token dummy para imports
│   ├── test_runtime_env.py       # NUEVO
│   ├── test_readonly_allowlist.py# NUEVO
│   └── test_healthcheck.py       # NUEVO
├── .env.example                  # NUEVO
├── .mcp.json.example             # NUEVO
├── .gitignore                    # NUEVO/MOD
├── setup.sh                      # NUEVO (macOS/Linux)
├── setup.ps1                     # NUEVO (Windows)
├── pyproject.toml                # MOD: + python-dotenv, config pytest asyncio
├── uv.lock                       # MOD: regenerado por uv
├── LICENSE                       # de konquest (MIT)
├── VENDOR.md                     # NUEVO: provenance del vendor
└── README.md                     # MOD: guía del trabajador (español)
```

---

### Task 1: Vendorizar konquest y dejar el paquete instalable

**Files:**
- Create (copia): `meta_ads_mcp/` (todo el paquete), `pyproject.toml`, `uv.lock`, `LICENSE`
- Create: `VENDOR.md`
- Create/Modify: `.gitignore`

**Interfaces:**
- Produces: paquete `meta_ads_mcp` importable y ejecutable como `python -m meta_ads_mcp`; comando `uv sync` funcional.

- [ ] **Step 1: Clonar konquest a una carpeta temporal**

```bash
rm -rf /tmp/konquest-src
git clone --depth 1 https://github.com/brandu-mos/konquest-meta-ads-mcp /tmp/konquest-src
git -C /tmp/konquest-src rev-parse HEAD   # anota este hash para VENDOR.md
```

- [ ] **Step 2: Copiar el paquete y los archivos de build al repo**

```bash
cd /home/pietro/Escritorio/meta-mcp
cp -r /tmp/konquest-src/meta_ads_mcp ./meta_ads_mcp
cp /tmp/konquest-src/pyproject.toml ./pyproject.toml
cp /tmp/konquest-src/uv.lock ./uv.lock
cp /tmp/konquest-src/LICENSE ./LICENSE
```

- [ ] **Step 3: Crear `.gitignore`**

```gitignore
# Secretos y config local
.env
.mcp.json

# Python / uv
.venv/
__pycache__/
*.pyc

# Datos locales opcionales de konquest
marketing-vault/
```

- [ ] **Step 4: Crear `VENDOR.md` con la provenance**

```markdown
# Provenance del vendor

Este repo vendoriza el paquete `meta_ads_mcp` de
[brandu-mos/konquest-meta-ads-mcp](https://github.com/brandu-mos/konquest-meta-ads-mcp)
(open-core, licencia MIT — ver `LICENSE`, copyright "AgentStack").

- Commit vendorizado: `<PEGAR_HASH_DEL_STEP_1>`
- Fecha: 2026-06-25
- Modificaciones locales: ver `meta_ads_mcp/server.py` (parche allowlist solo-lectura),
  `meta_ads_mcp/__main__.py` (carga de `.env`) y `meta_ads_mcp/runtime_env.py`.
```

- [ ] **Step 5: Instalar dependencias**

Run: `uv sync`
Expected: crea `.venv`, instala `mcp`, `facebook-business`, `httpx`, `pyyaml`, `pydantic` sin errores.

- [ ] **Step 6: Verificar que el paquete importa y ejecuta como módulo**

Run: `env META_ACCESS_TOKEN=DUMMY uv run python -c "import meta_ads_mcp.server; print('import ok')"`
Expected: imprime `import ok` sin excepción.

> Si falla porque algún módulo lee `META_ACCESS_TOKEN` al importar, el `DUMMY` de arriba lo cubre (no hay llamadas de red al importar). Si falla por otra causa, registrar el error y resolver antes de seguir.

- [ ] **Step 7: Commit**

```bash
git add meta_ads_mcp pyproject.toml uv.lock LICENSE VENDOR.md .gitignore
git commit -m "feat: vendorizar paquete meta_ads_mcp de konquest (MIT)"
```

---

### Task 2: Cargar `.env` con python-dotenv

**Files:**
- Create: `meta_ads_mcp/runtime_env.py`
- Modify: `meta_ads_mcp/__main__.py`
- Modify: `pyproject.toml` (añadir dependencia `python-dotenv`)
- Test: `tests/test_runtime_env.py`, `tests/conftest.py`

**Interfaces:**
- Produces: `meta_ads_mcp.runtime_env.load_environment() -> None` — carga el `.env` del directorio actual al entorno del proceso (no-op si no existe; no pisa variables ya definidas).

- [ ] **Step 1: Crear `tests/conftest.py` (token dummy para que los imports no fallen)**

```python
import os

# Garantiza que importar meta_ads_mcp.* nunca falle por falta de token en tests.
os.environ.setdefault("META_ACCESS_TOKEN", "TEST_DUMMY_TOKEN")
```

- [ ] **Step 2: Escribir el test que falla**

```python
# tests/test_runtime_env.py
import os


def test_load_environment_loads_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("META_ACCESS_TOKEN=FROM_DOTENV\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)

    from meta_ads_mcp.runtime_env import load_environment

    load_environment()
    assert os.environ["META_ACCESS_TOKEN"] == "FROM_DOTENV"
```

- [ ] **Step 3: Ejecutar el test y verificar que falla**

Run: `uv run pytest tests/test_runtime_env.py -v`
Expected: FAIL con `ModuleNotFoundError: meta_ads_mcp.runtime_env` (o `ImportError`).

- [ ] **Step 4: Añadir `python-dotenv` a las dependencias**

En `pyproject.toml`, dentro de `[project].dependencies`, añadir la línea:

```toml
    "python-dotenv>=1.0.0",
```

Luego: `uv sync`

- [ ] **Step 5: Crear `meta_ads_mcp/runtime_env.py`**

```python
"""Carga el .env local del trabajador al entorno del proceso."""
import os

from dotenv import load_dotenv


def load_environment() -> None:
    """Carga <cwd>/.env al entorno del proceso.

    No-op si el archivo no existe. No sobrescribe variables ya presentes.
    Se fija al directorio actual para coincidir con cómo Claude Code arranca
    el server (uv corre con CWD = carpeta del repo, donde vive el .env).
    """
    load_dotenv(os.path.join(os.getcwd(), ".env"))
```

- [ ] **Step 6: Ejecutar el test y verificar que pasa**

Run: `uv run pytest tests/test_runtime_env.py -v`
Expected: PASS.

- [ ] **Step 7: Conectar la carga en el arranque (`__main__.py`)**

Abrir `meta_ads_mcp/__main__.py`. Debe quedar así (cargar el entorno ANTES de importar/arrancar el server):

```python
from meta_ads_mcp.runtime_env import load_environment

load_environment()

from meta_ads_mcp.server import main

main()
```

> Si el `__main__.py` original tiene un guard `if __name__ == "__main__":`, conservarlo envolviendo `main()`. Lo esencial: `load_environment()` se ejecuta antes de `main()`.

- [ ] **Step 8: Verificar el arranque carga el .env (smoke manual)**

Carga un `.env` desde un directorio temporal (no toca el repo):
```bash
uv --directory /home/pietro/Escritorio/meta-mcp run python -c "import os, tempfile; d=tempfile.mkdtemp(); open(os.path.join(d,'.env'),'w').write('META_ACCESS_TOKEN=HELLO_DOTENV\n'); os.chdir(d); import meta_ads_mcp.runtime_env as e; e.load_environment(); print('TOKEN=', os.environ.get('META_ACCESS_TOKEN'))"
```
Expected: imprime `TOKEN= HELLO_DOTENV`.

- [ ] **Step 9: Commit**

```bash
git add meta_ads_mcp/runtime_env.py meta_ads_mcp/__main__.py pyproject.toml uv.lock tests/conftest.py tests/test_runtime_env.py
git commit -m "feat: cargar .env con python-dotenv al arrancar el MCP"
```

---

### Task 3: Parche de allowlist solo-lectura

**Files:**
- Modify: `meta_ads_mcp/server.py`
- Modify: `pyproject.toml` (config de pytest asyncio)
- Test: `tests/test_readonly_allowlist.py`

**Interfaces:**
- Consumes: instancia `mcp` (FastMCP) y los imports de `core/*` en `server.py`.
- Produces: constante `meta_ads_mcp.server.READ_ONLY_TOOLS: set[str]`; garantiza que `await server.mcp.list_tools()` devuelve exactamente esas tools.

- [ ] **Step 1: Habilitar modo asyncio en pytest**

En `pyproject.toml`, añadir (o fusionar) al final:

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 2: Escribir el test que falla**

```python
# tests/test_readonly_allowlist.py
WRITE_TOOLS = {
    "create_campaign", "update_campaign", "create_adset", "update_adset",
    "create_ad_from_manifest", "update_ad", "create_ad_creative", "update_ad_creative",
    "create_product_set", "update_product_set", "upload_ad_image", "upload_video_asset",
    "upload_video_resumable", "bulk_rename_objects", "delete_campaign_structure",
    "create_multi_asset_ad", "duplicate_campaign", "duplicate_adset", "send_test_event",
}
CORE_READ = {
    "check_token_status", "get_ad_accounts", "discover_all_accounts",
    "get_campaigns", "get_campaign_details", "get_adsets", "get_adset_details",
    "get_ads", "get_ad_details", "get_insights", "get_bulk_insights",
}


async def test_only_readonly_tools_are_registered():
    from meta_ads_mcp import server

    names = {t.name for t in await server.mcp.list_tools()}

    # El conjunto registrado es exactamente la allowlist declarada.
    assert names == server.READ_ONLY_TOOLS, f"diferencia: {names ^ server.READ_ONLY_TOOLS}"
    # Las tools núcleo de reporting están presentes.
    assert CORE_READ <= names, f"faltan núcleo: {CORE_READ - names}"
    # Ninguna tool de escritura se coló.
    assert not (names & WRITE_TOOLS), f"escritura filtrada: {names & WRITE_TOOLS}"
```

- [ ] **Step 3: Ejecutar el test y verificar que falla**

Run: `uv run pytest tests/test_readonly_allowlist.py -v`
Expected: FAIL — `AttributeError: module 'meta_ads_mcp.server' has no attribute 'READ_ONLY_TOOLS'` (o el set no coincide porque hay 57 tools registradas).

- [ ] **Step 4: Aplicar el parche en `server.py`**

Localizar la construcción de la instancia: `mcp = FastMCP(...)` (cerca de la línea 13-16). **Inmediatamente después de esa línea y ANTES del primer `from meta_ads_mcp.core...` / import de módulos core**, insertar:

```python
# --- Solo-lectura (Narkan) -------------------------------------------------
# Solo estas tools se registran. Cada tool de escritura/gestión queda fuera
# porque filtramos el decorador @mcp.tool ANTES de importar los módulos core
# (que registran por efecto secundario al importarse).
READ_ONLY_TOOLS = {
    "check_token_status", "get_ad_accounts", "discover_all_accounts",
    "get_campaigns", "get_campaign_details", "get_adsets", "get_adset_details",
    "get_ads", "get_ad_details", "get_insights", "get_bulk_insights",
}

_real_tool = mcp.tool


def _readonly_tool(*args, **kwargs):
    def decorator(fn):
        if fn.__name__ in READ_ONLY_TOOLS:
            return _real_tool(*args, **kwargs)(fn)
        return fn  # no se registra

    return decorator


mcp.tool = _readonly_tool
# ---------------------------------------------------------------------------
```

> No restaurar `mcp.tool` después de los imports: dejarlo parcheado es defensa en profundidad (si alguien añadiera módulos con tools de escritura, tampoco se registrarían).

- [ ] **Step 5: Ejecutar el test y verificar que pasa**

Run: `uv run pytest tests/test_readonly_allowlist.py -v`
Expected: PASS.

- [ ] **Step 6: Verificar manualmente la lista de tools expuestas**

Run: `env META_ACCESS_TOKEN=DUMMY uv run python -c "import asyncio; from meta_ads_mcp import server; print(sorted(t.name for t in asyncio.run(server.mcp.list_tools())))"`
Expected: imprime exactamente las 11 tools de `READ_ONLY_TOOLS`, ninguna de escritura.

- [ ] **Step 7: Commit**

```bash
git add meta_ads_mcp/server.py pyproject.toml tests/test_readonly_allowlist.py
git commit -m "feat: parche de allowlist solo-lectura (11 tools de reporting)"
```

---

### Task 4: Archivos de configuración (ejemplos + gitignore)

**Files:**
- Create: `.env.example`, `.mcp.json.example`
- Verify: `.gitignore` (ya creado en Task 1)

**Interfaces:**
- Produces: plantillas que el setup materializa en `.env` y `.mcp.json` locales.

- [ ] **Step 1: Crear `.env.example`**

```bash
# Token de Meta de SOLO LECTURA (System User, scope ads_read).
# Te lo entrega el admin por gestor de contraseñas. NUNCA lo subas a git.
META_ACCESS_TOKEN=pega_aqui_tu_token_de_solo_lectura
```

- [ ] **Step 2: Crear `.mcp.json.example`**

```json
{
  "mcpServers": {
    "meta-ads": {
      "command": "uv",
      "args": ["--directory", ".", "run", "python", "-m", "meta_ads_mcp"]
    }
  }
}
```

- [ ] **Step 3: Verificar que ambos son válidos**

Run: `uv run python -c "import json; json.load(open('.mcp.json.example')); print('json ok')"`
Expected: imprime `json ok`.

Run: `git check-ignore .env .mcp.json`
Expected: imprime `.env` y `.mcp.json` (confirmando que están ignorados).

- [ ] **Step 4: Commit**

```bash
git add .env.example .mcp.json.example
git commit -m "feat: plantillas .env.example y .mcp.json.example"
```

---

### Task 5: Script de health-check

**Files:**
- Create: `scripts/healthcheck.py`
- Test: `tests/test_healthcheck.py`

**Interfaces:**
- Consumes: `meta_ads_mcp.runtime_env.load_environment`.
- Produces: `scripts.healthcheck.format_report(data: dict) -> str` y `main()` (CLI). `data` tiene forma `{"name": str, "accounts": [{"account_id": str, "name": str, "account_status": int}, ...]}`.

- [ ] **Step 1: Escribir el test que falla**

```python
# tests/test_healthcheck.py
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "healthcheck", pathlib.Path(__file__).parent.parent / "scripts" / "healthcheck.py"
)
healthcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(healthcheck)


def test_format_report_lists_accounts_and_status():
    data = {
        "name": "plasa-backend",
        "accounts": [
            {"account_id": "111", "name": "Bellas Todas", "account_status": 1},
            {"account_id": "222", "name": "Narkan", "account_status": 101},
        ],
    }
    out = healthcheck.format_report(data)
    assert "Token válido" in out
    assert "Cuentas accesibles: 2" in out
    assert "act_111" in out and "Bellas Todas" in out and "(activa)" in out
    assert "act_222" in out and "estado 101" in out
```

- [ ] **Step 2: Ejecutar el test y verificar que falla**

Run: `uv run pytest tests/test_healthcheck.py -v`
Expected: FAIL — `FileNotFoundError` o `No module named 'healthcheck'` (el archivo no existe aún).

- [ ] **Step 3: Crear `scripts/healthcheck.py`**

```python
"""Health-check: valida el token de solo-lectura y lista las cuentas accesibles.

Uso:  uv run python scripts/healthcheck.py
"""
import json
import os
import sys
import urllib.parse
import urllib.request

from meta_ads_mcp.runtime_env import load_environment

GRAPH = "https://graph.facebook.com/v25.0"


def _get(path: str, token: str):
    sep = "&" if "?" in path else "?"
    url = f"{GRAPH}/{path}{sep}access_token={urllib.parse.quote(token)}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)


def fetch(token: str) -> dict:
    me = _get("me?fields=id,name", token)
    accts = _get("me/adaccounts?fields=account_id,name,account_status&limit=200", token)
    return {"name": me.get("name"), "accounts": accts.get("data", [])}


def format_report(data: dict) -> str:
    lines = [
        f"✅ Token válido — usuario: {data['name']}",
        f"Cuentas accesibles: {len(data['accounts'])}",
    ]
    for a in data["accounts"]:
        state = "activa" if a.get("account_status") == 1 else f"estado {a.get('account_status')}"
        lines.append(f"  - act_{a['account_id']} · {a.get('name')} ({state})")
    return "\n".join(lines)


def main() -> None:
    load_environment()
    token = os.environ.get("META_ACCESS_TOKEN")
    if not token or token.startswith("pega_aqui"):
        print("❌ Falta META_ACCESS_TOKEN válido (revisa tu .env).", file=sys.stderr)
        sys.exit(1)
    try:
        print(format_report(fetch(token)))
    except Exception as exc:  # noqa: BLE001 — el mensaje al usuario es lo importante
        print(f"❌ El token no validó: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Ejecutar el test y verificar que pasa**

Run: `uv run pytest tests/test_healthcheck.py -v`
Expected: PASS.

- [ ] **Step 5: (Opcional, requiere token real) Probar el health-check en vivo**

Solo si tienes el token de solo-lectura a mano:
```bash
printf 'META_ACCESS_TOKEN=<TOKEN_REAL>\n' > .env
uv run python scripts/healthcheck.py
rm .env   # no dejar el token escrito si esto fue solo una prueba
```
Expected: "✅ Token válido — usuario: plasa-backend" y la lista de ~7 cuentas.

- [ ] **Step 6: Commit**

```bash
git add scripts/healthcheck.py tests/test_healthcheck.py
git commit -m "feat: script de health-check del token y cuentas"
```

---

### Task 6: `setup.sh` (macOS / Linux)

**Files:**
- Create: `setup.sh`

**Interfaces:**
- Consumes: `scripts/healthcheck.py`, `.env.example`.
- Produces: `.env` y `.mcp.json` locales; deja el MCP listo para Claude Code.

- [ ] **Step 1: Crear `setup.sh`**

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
REPO_DIR="$(pwd)"

echo "▶ (1/5) Verificando uv..."
if ! command -v uv >/dev/null 2>&1; then
  echo "    Instalando uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="$HOME/.local/bin:$PATH"
fi

echo "▶ (2/5) Instalando dependencias..."
uv sync

if [ ! -f .env ]; then
  echo "▶ (3/5) Configurando token de solo-lectura..."
  cp .env.example .env
  printf "    Pega tu token de SOLO LECTURA de Meta y pulsa Enter:\n    > "
  read -rs TOKEN
  echo
  TOKEN="$TOKEN" python3 - <<'PY'
import os, pathlib
tok = os.environ["TOKEN"].strip()
p = pathlib.Path(".env")
out = []
for ln in p.read_text().splitlines():
    out.append(f"META_ACCESS_TOKEN={tok}" if ln.startswith("META_ACCESS_TOKEN=") else ln)
p.write_text("\n".join(out) + "\n")
print("    Token guardado en .env")
PY
else
  echo "▶ (3/5) .env ya existe, lo dejo como está."
fi

echo "▶ (4/5) Generando .mcp.json..."
cat > .mcp.json <<JSON
{
  "mcpServers": {
    "meta-ads": {
      "command": "uv",
      "args": ["--directory", "${REPO_DIR}", "run", "python", "-m", "meta_ads_mcp"]
    }
  }
}
JSON

echo "▶ (5/5) Health-check..."
uv run python scripts/healthcheck.py

echo
echo "✅ Listo. Abre Claude Code en esta carpeta y pregunta, por ejemplo:"
echo "   \"¿Qué campañas activas hay y cuánto gastaron este mes?\""
```

- [ ] **Step 2: Hacerlo ejecutable y verificar sintaxis**

```bash
chmod +x setup.sh
bash -n setup.sh && echo "sintaxis ok"
```
Expected: imprime `sintaxis ok` (sin errores de parseo).

- [ ] **Step 3: (Opcional, con token real) Probar el flujo completo**

En un clon limpio o tras `rm -f .env .mcp.json`:
```bash
./setup.sh
```
Expected: instala, pide token, genera `.mcp.json` con la ruta absoluta del repo, y el health-check lista las cuentas. Verifica que `.mcp.json` tiene `"--directory", "/home/pietro/Escritorio/meta-mcp"`.

- [ ] **Step 4: Commit**

```bash
git add setup.sh
git commit -m "feat: setup.sh (onboarding 1 comando para macOS/Linux)"
```

---

### Task 7: `setup.ps1` (Windows)

**Files:**
- Create: `setup.ps1`

**Interfaces:**
- Equivalente a `setup.sh` para Windows: produce `.env` y `.mcp.json`, corre el health-check.

- [ ] **Step 1: Crear `setup.ps1`**

```powershell
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot
$RepoDir = (Get-Location).Path

Write-Host "▶ (1/5) Verificando uv..."
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "    Instalando uv..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}

Write-Host "▶ (2/5) Instalando dependencias..."
uv sync

if (-not (Test-Path .env)) {
    Write-Host "▶ (3/5) Configurando token de solo-lectura..."
    Copy-Item .env.example .env
    $Secure = Read-Host "    Pega tu token de SOLO LECTURA de Meta" -AsSecureString
    $Token = [System.Net.NetworkCredential]::new("", $Secure).Password
    $escaped = $Token -replace '([$])', '$$$1'
    (Get-Content .env) -replace '^META_ACCESS_TOKEN=.*', "META_ACCESS_TOKEN=$escaped" | Set-Content .env
    Write-Host "    Token guardado en .env"
} else {
    Write-Host "▶ (3/5) .env ya existe, lo dejo como está."
}

Write-Host "▶ (4/5) Generando .mcp.json..."
$mcp = [ordered]@{
    mcpServers = [ordered]@{
        "meta-ads" = [ordered]@{
            command = "uv"
            args    = @("--directory", $RepoDir, "run", "python", "-m", "meta_ads_mcp")
        }
    }
}
$mcp | ConvertTo-Json -Depth 6 | Set-Content .mcp.json

Write-Host "▶ (5/5) Health-check..."
uv run python scripts/healthcheck.py

Write-Host ""
Write-Host "✅ Listo. Abre Claude Code en esta carpeta y pregunta."
```

- [ ] **Step 2: Verificar sintaxis (si hay PowerShell disponible)**

Run (Linux con pwsh instalado, o en Windows):
```bash
pwsh -NoProfile -Command "[void][System.Management.Automation.Language.Parser]::ParseFile('setup.ps1',[ref]$null,[ref]$null); 'sintaxis ok'"
```
Expected: imprime `sintaxis ok`.
> Si `pwsh` no está instalado en la máquina de desarrollo, omitir este step y verificar manualmente en una máquina Windows (Task 10 incluye prueba real en Windows).

- [ ] **Step 3: Commit**

```bash
git add setup.ps1
git commit -m "feat: setup.ps1 (onboarding 1 comando para Windows)"
```

---

### Task 8: README para el trabajador (español)

**Files:**
- Modify: `README.md`

**Interfaces:**
- Produces: guía de instalación y uso; atribución a konquest.

- [ ] **Step 1: Reemplazar `README.md` con la guía**

````markdown
# Meta Ads MCP (solo lectura) — Narkan

Consulta los datos de Meta Ads de las cuentas de la agencia **en lenguaje natural
desde Claude Code**. Es de **solo lectura**: puedes ver campañas, conjuntos de
anuncios, anuncios e insights, pero no se puede crear, editar ni gastar nada.

## Requisitos
- [Claude Code](https://claude.com/claude-code) instalado.
- macOS, Linux o Windows.
- (El script instala `uv` automáticamente si falta.)

## Instalación (1 comando)

**macOS / Linux**
```bash
git clone https://github.com/pietro-narkan/meta-mcp
cd meta-mcp
./setup.sh
```

**Windows (PowerShell)**
```powershell
git clone https://github.com/pietro-narkan/meta-mcp
cd meta-mcp
.\setup.ps1
```

El script instala dependencias, te pide **una vez** el token de solo-lectura
(te lo entrega el admin), genera la configuración local y valida que todo funcione
listando las cuentas a las que tienes acceso.

## Cómo usar
Abre Claude Code dentro de la carpeta `meta-mcp` y pregunta, por ejemplo:
- "¿Qué campañas activas hay en cada cuenta y cuánto gastaron este mes?"
- "Compara el CTR de Bellas Todas vs Spa Infinity en los últimos 30 días."
- "Dame el gasto por cuenta de los últimos 7 días."
- "¿Qué conjuntos de anuncios están pausados en Fiorenza?"

## Seguridad
- **Solo lectura.** El token tiene permiso `ads_read`: imposible gastar, crear o borrar.
- **Tu token nunca entra a git.** Vive solo en tu archivo `.env` local (ignorado por git).
- No compartas tu `.env` ni tu token.

## Para el admin
- **Entregar el token:** comparte el token de solo-lectura por gestor de contraseñas,
  nunca por el repo ni por chat.
- **Rotar el token** (si alguien se va o se filtra): genera un nuevo token del System User
  en el Business Manager (app "plasa", scope `ads_read`), y reparte el nuevo. Cada trabajador
  actualiza la línea `META_ACCESS_TOKEN=` de su `.env` y reinicia Claude Code.

## Créditos
Basado en [konquest-meta-ads-mcp](https://github.com/brandu-mos/konquest-meta-ads-mcp)
(licencia MIT — ver `LICENSE`). Recortado a solo-lectura. Ver `VENDOR.md`.
````

- [ ] **Step 2: Verificar que no quedaron placeholders rotos**

Run: `grep -n "PEGAR\|TODO\|TBD" README.md || echo "sin placeholders"`
Expected: imprime `sin placeholders`.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: README guía del trabajador (español)"
```

---

### Task 9: (Opcional) Ampliar la allowlist con tools de lectura adicionales

> Aditivo. Requiere el **token real**. Si no está disponible, omitir: las 11 tools núcleo
> ya cubren el reporting. No incluir una tool que no se haya verificado en vivo.

**Files:**
- Create: `scripts/probe_candidates.py`
- Modify: `meta_ads_mcp/server.py` (ampliar `READ_ONLY_TOOLS`)
- Modify: `tests/test_readonly_allowlist.py` (actualizar expectativa)

**Interfaces:**
- Produces: lista de tools candidatas que devuelven 200 con el token `ads_read`.

- [ ] **Step 1: Crear `scripts/probe_candidates.py`**

```python
"""Prueba en vivo qué tools-candidatas de lectura funcionan con el token ads_read.

Uso (con un .env válido):  uv run python scripts/probe_candidates.py
Imprime, por cada endpoint, OK/te FALLA; usa el resultado para decidir qué
nombres añadir a READ_ONLY_TOOLS en server.py.
"""
import json
import os
import urllib.parse
import urllib.request

from meta_ads_mcp.runtime_env import load_environment

GRAPH = "https://graph.facebook.com/v25.0"


def _get(path, token):
    sep = "&" if "?" in path else "?"
    url = f"{GRAPH}/{path}{sep}access_token={urllib.parse.quote(token)}"
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            return 200, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:160]


def main():
    load_environment()
    token = os.environ["META_ACCESS_TOKEN"]
    acct = _get("me/adaccounts?fields=account_id&limit=1", token)[1]["data"][0]["account_id"]
    act = f"act_{acct}"
    # tool de konquest  ->  endpoint que usa
    probes = {
        "get_account_info": f"{act}?fields=name,account_status,currency",
        "get_ad_creatives": f"{act}/adcreatives?fields=name&limit=1",
        "search_interests": "search?type=adinterest&q=fitness&limit=1",
        "search_geo_locations": "search?type=adgeolocation&q=Santiago&limit=1",
        "estimate_audience_size": f"{act}/reachestimate",  # suele requerir más scope
    }
    for tool, path in probes.items():
        code, _ = _get(path, token)
        print(f"{'OK ' if code == 200 else 'FALLA'} [{code}]  {tool}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Ejecutar el probe con un `.env` válido**

Run: `uv run python scripts/probe_candidates.py`
Expected: una línea por tool con `OK [200]` o `FALLA [code]`.

- [ ] **Step 3: Añadir a `READ_ONLY_TOOLS` solo las que dieron `OK`**

En `meta_ads_mcp/server.py`, agregar los nombres `OK` al set `READ_ONLY_TOOLS`. Ejemplo si `get_account_info`, `get_ad_creatives`, `search_interests` y `search_geo_locations` pasaron:

```python
    # ... 11 núcleo ...
    "get_account_info", "get_ad_creatives", "search_interests", "search_geo_locations",
```

- [ ] **Step 4: Actualizar la expectativa del test y verificar**

En `tests/test_readonly_allowlist.py`, añadir los mismos nombres al set `CORE_READ` (o a un set `EXTRA_READ` que también se exija). El assert `names == server.READ_ONLY_TOOLS` se mantiene.

Run: `uv run pytest tests/ -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add scripts/probe_candidates.py meta_ads_mcp/server.py tests/test_readonly_allowlist.py
git commit -m "feat: ampliar allowlist con tools de lectura verificadas en vivo"
```

---

### Task 10: Verificación end-to-end y publicación

> El último step (crear/push del repo privado) es una acción **hacia afuera**: confirmar con
> el usuario y usar su `gh` autenticado antes de ejecutarla.

**Files:**
- Ninguno nuevo (configuración + verificación + publicación).

- [ ] **Step 1: Suite completa de tests en verde**

Run: `uv run pytest -v`
Expected: todos PASS.

- [ ] **Step 2: Smoke real del MCP en Claude Code (con token real)**

```bash
./setup.sh   # (o .\setup.ps1 en Windows) — deja .env y .mcp.json
```
Luego abrir Claude Code en la carpeta y confirmar:
- El servidor `meta-ads` aparece conectado (revisar tools con `/mcp` o el panel de MCP).
- Solo se listan las tools de lectura (ninguna `create_*`/`update_*`/`delete_*`).
- Preguntar: "¿Qué campañas activas hay y cuánto gastaron este mes?" → responde con datos reales.

- [ ] **Step 3: Confirmar que no hay secretos trackeados**

Run: `git status --porcelain && git ls-files | grep -E '(^|/)\.(env|mcp\.json)$' || echo "sin secretos trackeados"`
Expected: imprime `sin secretos trackeados` y el working tree no muestra `.env`/`.mcp.json` como trackeados.

- [ ] **Step 4: Merge de la rama de trabajo a `main`**

```bash
git checkout main
git merge --no-ff feat/readonly-mcp -m "merge: MCP Meta Ads solo-lectura"
```

- [ ] **Step 5: (Confirmar con el usuario) Crear el repo privado y publicar**

```bash
gh auth status   # debe estar logueado como pietro-narkan
gh repo create pietro-narkan/meta-mcp --private --source=. --remote=origin --push
```
Expected: repo privado creado y `main` empujado.

- [ ] **Step 6: Onboarding del equipo (instrucciones, no código)**

- Añadir a cada trabajador como **colaborador** del repo (`Settings → Collaborators`).
- Compartir el **token de solo-lectura** por gestor de contraseñas.
- Pasarles las 3 líneas de instalación del README según su SO.

---

## Notas de implementación

- **Orden recomendado:** Tasks 1→8 son secuenciales (cada una depende de la anterior).
  Task 9 es opcional/aditiva. Task 10 cierra.
- **Token para pruebas en vivo:** está en el VPS (proyecto Dokploy `plaza`, app `plaza-backend`,
  variable `META_SYSTEM_USER_TOKEN`). El admin lo provee; no se commitea.
- **Recordatorio de seguridad:** rotar la API key de Dokploy que se compartió en el chat de planificación.
