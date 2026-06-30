"""Regression test: the secret-path ASGI gate."""
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
        assert r.status_code != 404
