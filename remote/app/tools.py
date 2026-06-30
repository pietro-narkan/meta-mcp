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


TOOLS = [
    check_token_status, get_ad_accounts, discover_all_accounts,
    get_campaigns, get_campaign_details, get_adsets, get_adset_details,
    get_ads, get_ad_details,
]
