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


_DELIVERY_INSIGHT_FIELDS = (
    "account_currency",
    "date_start",
    "date_stop",
    "spend",
    "impressions",
    "clicks",
    "ctr",
    "cpc",
    "cpm",
    "reach",
    "frequency",
)

# Meta devuelve las conversiones como matrices de action_type/value. Se conservan
# completas en la respuesta y además se normalizan abajo para que los clientes MCP
# no tengan que conocer todos los nombres internos de Meta.
_CONVERSION_INSIGHT_FIELDS = (
    "actions",
    "action_values",
    "cost_per_action_type",
    "conversions",
    "conversion_values",
    "cost_per_conversion",
    "purchase_roas",
    "website_purchase_roas",
    "mobile_app_purchase_roas",
    "results",
    "cost_per_result",
)

_INSIGHT_FIELDS = ",".join((*_DELIVERY_INSIGHT_FIELDS, *_CONVERSION_INSIGHT_FIELDS))

_ACTION_ALIASES = {
    "purchases": (
        "omni_purchase",
        "purchase",
        "offsite_conversion.fb_pixel_purchase",
        "onsite_conversion.purchase",
        "app_custom_event.fb_mobile_purchase",
        "offline_conversion.purchase",
    ),
    "leads": (
        "lead",
        "onsite_conversion.lead_grouped",
        "onsite_conversion.lead",
        "offsite_conversion.fb_pixel_lead",
    ),
    "add_to_cart": (
        "omni_add_to_cart",
        "add_to_cart",
        "offsite_conversion.fb_pixel_add_to_cart",
    ),
    "initiate_checkout": (
        "omni_initiated_checkout",
        "initiate_checkout",
        "offsite_conversion.fb_pixel_initiate_checkout",
    ),
    "landing_page_views": (
        "omni_landing_page_view",
        "landing_page_view",
    ),
    "contacts": (
        "omni_contact",
        "contact",
        "offsite_conversion.fb_pixel_contact",
    ),
    "messaging_conversations_started": (
        "onsite_conversion.messaging_conversation_started_7d",
        "onsite_conversion.messaging_conversation_started",
        "messaging_conversation_started_7d",
        "messaging_conversation_started",
    ),
    "messaging_first_replies": (
        "onsite_conversion.messaging_first_reply",
        "onsite_conversion.messaging_first_reply_7d",
        "messaging_first_reply",
    ),
    "link_clicks": ("link_click",),
    "video_views": ("video_view",),
    "post_engagements": ("post_engagement",),
}

_COST_FIELD_BY_METRIC = {
    "purchases": "cost_per_purchase",
    "leads": "cost_per_lead",
    "add_to_cart": "cost_per_add_to_cart",
    "initiate_checkout": "cost_per_initiate_checkout",
    "landing_page_views": "cost_per_landing_page_view",
    "contacts": "cost_per_contact",
    "messaging_conversations_started": "cost_per_messaging_conversation_started",
    "messaging_first_replies": "cost_per_messaging_first_reply",
    "link_clicks": "cost_per_link_click",
}

_NORMALIZED_CONVERSION_FIELDS = (
    "purchases",
    "purchase_conversion_value",
    "cost_per_purchase",
    "roas",
    "leads",
    "cost_per_lead",
    "add_to_cart",
    "cost_per_add_to_cart",
    "initiate_checkout",
    "cost_per_initiate_checkout",
    "landing_page_views",
    "cost_per_landing_page_view",
    "contacts",
    "cost_per_contact",
    "messaging_conversations_started",
    "cost_per_messaging_conversation_started",
    "messaging_first_replies",
    "cost_per_messaging_first_reply",
    "link_clicks",
    "cost_per_link_click",
    "video_views",
    "post_engagements",
)

_META_ATTRIBUTION_NOTICE = (
    "Compras, valores, leads y conversaciones son resultados atribuidos y "
    "reportados por Meta para el periodo solicitado. null significa que Meta no "
    "devolvió esa métrica; no representa facturación externa."
)


def _first_action_value(items: object, aliases: tuple[str, ...]) -> str | None:
    if not isinstance(items, list):
        return None
    values = {
        item.get("action_type"): item.get("value")
        for item in items
        if isinstance(item, dict) and item.get("action_type")
    }
    for alias in aliases:
        value = values.get(alias)
        if value is not None:
            return str(value)
    return None


def _ratio(numerator: object, denominator: object) -> str | None:
    try:
        numerator_value = float(str(numerator))
        denominator_value = float(str(denominator))
    except (TypeError, ValueError):
        return None
    if denominator_value <= 0:
        return None
    return f"{numerator_value / denominator_value:.2f}"


def _normalize_insight_row(row: dict) -> dict:
    """Conserva la respuesta de Meta y agrega métricas de conversión estables."""
    normalized = dict(row)
    actions = row.get("actions")
    conversions = row.get("conversions")
    action_values = row.get("action_values")
    conversion_values = row.get("conversion_values")
    costs = row.get("cost_per_action_type")
    conversion_costs = row.get("cost_per_conversion")
    spend = row.get("spend")
    derived_metrics: list[str] = []

    for metric, aliases in _ACTION_ALIASES.items():
        value = (
            _first_action_value(actions, aliases)
            or _first_action_value(conversions, aliases)
        )
        normalized[metric] = value

        cost_field = _COST_FIELD_BY_METRIC.get(metric)
        if not cost_field:
            continue
        cost = (
            _first_action_value(costs, aliases)
            or _first_action_value(conversion_costs, aliases)
        )
        if cost is None and value is not None:
            cost = _ratio(spend, value)
            if cost is not None:
                derived_metrics.append(cost_field)
        normalized[cost_field] = cost

    purchase_aliases = _ACTION_ALIASES["purchases"]
    purchase_value = (
        _first_action_value(action_values, purchase_aliases)
        or _first_action_value(conversion_values, purchase_aliases)
    )
    normalized["purchase_conversion_value"] = purchase_value

    roas = (
        _first_action_value(row.get("purchase_roas"), purchase_aliases)
        or _first_action_value(row.get("website_purchase_roas"), purchase_aliases)
        or _first_action_value(row.get("mobile_app_purchase_roas"), purchase_aliases)
    )
    if roas is None and purchase_value is not None:
        roas = _ratio(purchase_value, spend)
        if roas is not None:
            derived_metrics.append("roas")
    normalized["roas"] = roas

    # La forma estable siempre contiene todas las claves. Las matrices originales
    # actions/action_values/conversions siguen disponibles para eventos no mapeados.
    for field in _NORMALIZED_CONVERSION_FIELDS:
        normalized.setdefault(field, None)
    if derived_metrics:
        normalized["derived_from_meta_totals"] = derived_metrics
    return normalized


def _normalize_insight_rows(rows: object) -> list[dict]:
    if not isinstance(rows, list):
        return []
    return [_normalize_insight_row(row) for row in rows if isinstance(row, dict)]


async def get_insights(account_id: str, date_preset: str = "last_30d") -> dict:
    """Métricas Meta agregadas, incluidas conversiones, valor, ROAS y mensajes."""
    res = await get_client().get(
        f"{_acct(account_id)}/insights",
        {"fields": _INSIGHT_FIELDS, "date_preset": date_preset},
    )
    return {
        "date_preset": date_preset,
        "meta_attribution_notice": _META_ATTRIBUTION_NOTICE,
        "data": _normalize_insight_rows(res.get("data")),
    }


async def get_bulk_insights(account_id: str, level: str = "campaign", date_preset: str = "last_30d") -> dict:
    """Métricas Meta y conversiones por campaign, adset o ad."""
    if level not in {"campaign", "adset", "ad"}:
        return {
            "error": "level debe ser campaign, adset o ad",
            "level": level,
            "date_preset": date_preset,
        }
    res = await get_client().get(
        f"{_acct(account_id)}/insights",
        {
            "fields": f"{level}_name,{_INSIGHT_FIELDS}",
            "level": level,
            "date_preset": date_preset,
            "limit": "200",
        },
    )
    return {
        "level": level,
        "date_preset": date_preset,
        "meta_attribution_notice": _META_ATTRIBUTION_NOTICE,
        "data": _normalize_insight_rows(res.get("data")),
    }


TOOLS = [
    check_token_status, get_ad_accounts, discover_all_accounts,
    get_campaigns, get_campaign_details, get_adsets, get_adset_details,
    get_ads, get_ad_details, get_insights, get_bulk_insights,
]
