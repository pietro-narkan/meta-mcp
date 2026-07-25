"""Regression tests for the remote MCP ASGI surface."""
from starlette.testclient import TestClient
from app import server, security

INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-11-25",
        "capabilities": {},
        "clientInfo": {"name": "t", "version": "1"},
    },
}


def test_secret_path_gate():
    secret = security.require_secret()
    with TestClient(server.app) as client:
        assert client.get("/health").status_code == 200
        assert client.post("/mcp", json=INIT).status_code == 404
        r = client.post(
            f"/{secret}/mcp",
            headers={"Accept": "application/json, text/event-stream"},
            json=INIT,
        )
        assert r.status_code == 200


def test_mcp_endpoint_accepts_trailing_slash_without_redirect():
    secret = security.require_secret()
    with TestClient(server.app, follow_redirects=False) as client:
        response = client.post(
            f"/{secret}/mcp/",
            headers={"Accept": "application/json, text/event-stream"},
            json=INIT,
        )
        assert response.status_code == 200
        assert "location" not in response.headers


def test_mcp_endpoint_tolerates_sse_only_and_wildcard_accept():
    secret = security.require_secret()
    with TestClient(server.app) as client:
        for accept in ("text/event-stream", "*/*"):
            response = client.post(
                f"/{secret}/mcp",
                headers={"Accept": accept},
                json=INIT,
            )
            assert response.status_code == 200
            assert response.headers["content-type"].startswith("text/event-stream")


def test_cors_allows_claude_and_chatgpt_origins():
    secret = security.require_secret()
    with TestClient(server.app) as client:
        for origin in server.ALLOWED_WEB_ORIGINS:
            response = client.options(
                f"/{secret}/mcp",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": (
                        "authorization,content-type,mcp-protocol-version"
                    ),
                },
            )
            assert response.status_code == 200
            assert response.headers["access-control-allow-origin"] == origin


def test_cors_does_not_allow_unknown_origins():
    secret = security.require_secret()
    with TestClient(server.app) as client:
        response = client.options(
            f"/{secret}/mcp",
            headers={
                "Origin": "https://example.invalid",
                "Access-Control-Request-Method": "POST",
            },
        )
        assert "access-control-allow-origin" not in response.headers


async def test_all_tools_are_annotated_read_only():
    registered = await server.mcp.list_tools()

    assert len(registered) == 11
    for tool in registered:
        assert tool.annotations is not None
        assert tool.annotations.readOnlyHint is True
        assert tool.annotations.destructiveHint is False
        assert tool.annotations.idempotentHint is True
        assert tool.annotations.openWorldHint is True
