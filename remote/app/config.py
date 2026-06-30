"""Configuración leída del entorno (sin secretos hardcodeados)."""
import os

GRAPH_VERSION = "v25.0"
GRAPH_BASE = f"https://graph.facebook.com/{GRAPH_VERSION}"

META_ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
MCP_SECRET = os.environ.get("MCP_SECRET", "")
