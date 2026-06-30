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
