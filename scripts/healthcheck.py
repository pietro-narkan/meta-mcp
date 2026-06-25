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
