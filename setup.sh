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
