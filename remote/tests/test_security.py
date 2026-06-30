import pytest
from app import security


def test_mcp_path_builds_secret_route():
    assert security.mcp_path("abc123") == "/abc123/mcp"


def test_require_secret_returns_value(monkeypatch):
    monkeypatch.setattr(security.config, "MCP_SECRET", "x" * 32)
    assert security.require_secret() == "x" * 32


def test_require_secret_rejects_empty_or_short(monkeypatch):
    monkeypatch.setattr(security.config, "MCP_SECRET", "")
    with pytest.raises(RuntimeError):
        security.require_secret()
    monkeypatch.setattr(security.config, "MCP_SECRET", "short")
    with pytest.raises(RuntimeError):
        security.require_secret()
