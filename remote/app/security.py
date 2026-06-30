"""Candado por ruta secreta: el MCP se sirve en /<MCP_SECRET>/mcp."""
from __future__ import annotations

from app import config


def mcp_path(secret: str) -> str:
    """Ruta donde se monta el endpoint MCP."""
    return f"/{secret}/mcp"


def require_secret() -> str:
    """Devuelve MCP_SECRET o lanza si falta / es demasiado corto (<16 chars)."""
    secret = config.MCP_SECRET
    if not secret or len(secret) < 16:
        raise RuntimeError("MCP_SECRET ausente o demasiado corto (>=16 chars).")
    return secret
