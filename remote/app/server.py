"""Servidor MCP remoto Streamable HTTP para Claude y ChatGPT (solo lectura).

El MCP se sirve en /<MCP_SECRET>/mcp; /health en la raíz; otras rutas -> 404.
"""
from __future__ import annotations

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import tools
from app.security import mcp_path, require_secret

ALLOWED_WEB_ORIGINS = [
    "https://claude.ai",
    "https://claude.com",
    "https://chatgpt.com",
    "https://www.chatgpt.com",
    "https://chat.openai.com",
]

mcp = FastMCP(
    "Narkan Meta Ads (solo lectura)",
    instructions=(
        "Consulta Meta Ads sin modificar campañas, presupuestos ni anuncios. "
        "Todas las herramientas son de solo lectura y consultan la Meta Graph API."
    ),
)

for _fn in tools.TOOLS:
    mcp.tool(
        _fn,
        annotations=ToolAnnotations(
            readOnlyHint=True,
            destructiveHint=False,
            idempotentHint=True,
            openWorldHint=True,
        ),
    )


@mcp.custom_route("/health", methods=["GET"])
async def _health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# El MCP se sirve en la ruta secreta (conserva su lifespan intacto).
app = mcp.http_app(path=mcp_path(require_secret()), stateless_http=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_WEB_ORIGINS,
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=[
        "Accept",
        "Authorization",
        "Content-Type",
        "Last-Event-ID",
        "Mcp-Session-Id",
        "MCP-Protocol-Version",
    ],
    expose_headers=["Mcp-Session-Id"],
)
