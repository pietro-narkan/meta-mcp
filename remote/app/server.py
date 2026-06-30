"""Servidor MCP remoto Streamable HTTP para claude.ai (solo lectura).

El MCP se sirve en /<MCP_SECRET>/mcp; /health en la raíz; otras rutas -> 404.
"""
from __future__ import annotations

from fastmcp import FastMCP
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import tools
from app.security import mcp_path, require_secret

mcp = FastMCP("Narkan Meta Ads (solo lectura)")

for _fn in tools.TOOLS:
    mcp.tool(_fn)


@mcp.custom_route("/health", methods=["GET"])
async def _health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# El MCP se sirve en la ruta secreta (conserva su lifespan intacto).
app = mcp.http_app(path=mcp_path(require_secret()), stateless_http=True)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://claude.ai"],
    allow_methods=["GET", "POST", "OPTIONS", "DELETE"],
    allow_headers=["Content-Type", "Mcp-Session-Id", "MCP-Protocol-Version"],
    expose_headers=["Mcp-Session-Id"],
    allow_credentials=True,
)
