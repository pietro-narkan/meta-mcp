"""Servidor MCP remoto Streamable HTTP para Claude y ChatGPT (solo lectura).

El MCP se sirve en /<MCP_SECRET>/mcp; /health en la raíz; otras rutas -> 404.
"""
from __future__ import annotations

from fastmcp import FastMCP
from mcp.types import ToolAnnotations
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app import tools
from app.security import mcp_path, require_secret

ALLOWED_WEB_ORIGINS = [
    "https://claude.ai",
    "https://claude.com",
    "https://chatgpt.com",
    "https://www.chatgpt.com",
    "https://chat.openai.com",
]


class MCPClientCompatibilityMiddleware:
    """Tolera variantes de URL/Accept usadas por clientes MCP web."""

    def __init__(self, app: ASGIApp, endpoint: str) -> None:
        self.app = app
        self.endpoint = endpoint

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        compatible_scope = scope
        if scope.get("path") == f"{self.endpoint}/":
            # Evita que Starlette genere un 307 a http:// detrás de Traefik.
            compatible_scope = dict(scope)
            compatible_scope["path"] = self.endpoint
            compatible_scope["raw_path"] = self.endpoint.encode("ascii")

        if (
            compatible_scope.get("method") == "POST"
            and compatible_scope.get("path") == self.endpoint
        ):
            headers = list(compatible_scope.get("headers", []))
            accept = b",".join(
                value for name, value in headers if name.lower() == b"accept"
            ).lower()
            if (
                not accept
                or b"*/*" in accept
                or (
                    b"text/event-stream" in accept
                    and b"application/json" not in accept
                )
            ):
                compatible_scope = dict(compatible_scope)
                compatible_scope["headers"] = [
                    (name, value)
                    for name, value in headers
                    if name.lower() != b"accept"
                ] + [
                    (
                        b"accept",
                        b"application/json, text/event-stream",
                    ),
                ]

        await self.app(compatible_scope, receive, send)


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
MCP_ENDPOINT = mcp_path(require_secret())
app = mcp.http_app(path=MCP_ENDPOINT, stateless_http=True)

app.add_middleware(
    MCPClientCompatibilityMiddleware,
    endpoint=MCP_ENDPOINT,
)

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
