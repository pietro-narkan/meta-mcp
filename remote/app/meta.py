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
        url = f"{GRAPH_BASE}/{path}"
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    url,
                    params=query,
                    headers={"Authorization": f"Bearer {self._token}"},
                )
        except httpx.HTTPError as exc:  # red
            raise MetaError(f"Error de red: {exc}") from exc
        if resp.status_code != 200:
            try:
                msg = resp.json().get("error", {}).get("message", resp.text[:200])
            except (ValueError, KeyError):
                msg = resp.text[:200]
            raise MetaError(f"Graph API {resp.status_code}: {msg}")
        return resp.json()
