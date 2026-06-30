"""Candado por ruta secreta: el MCP se sirve en /<MCP_SECRET>/mcp."""
from __future__ import annotations

import re

from app import config


def mcp_path(secret: str) -> str:
    """Ruta donde se monta el endpoint MCP."""
    return f"/{secret}/mcp"


def require_secret() -> str:
    """Devuelve MCP_SECRET o lanza si falta / es demasiado corto (<16 chars) o no es URL-safe."""
    secret = config.MCP_SECRET
    if not secret or len(secret) < 16:
        raise RuntimeError("MCP_SECRET ausente o demasiado corto (>=16 chars).")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", secret):
        raise RuntimeError("MCP_SECRET contiene caracteres no URL-safe (solo A-Z a-z 0-9 _ -).")
    return secret
