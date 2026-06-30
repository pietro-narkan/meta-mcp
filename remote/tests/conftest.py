import os
import pytest

# Must be set before any app.* imports so app.config reads them at cache time.
os.environ.setdefault("META_ACCESS_TOKEN", "TEST_DUMMY_TOKEN")
os.environ.setdefault("MCP_SECRET", "test_secret_minimum_16_plus_chars")

from app import tools


class FakeClient:
    def __init__(self, responses):
        self._responses = responses
        self.calls = []

    async def get(self, path, params=None):
        self.calls.append((path, params))
        return self._responses[path]


@pytest.fixture
def fake(monkeypatch):
    def _install(responses):
        client = FakeClient(responses)
        monkeypatch.setattr(tools, "get_client", lambda: client)
        return client
    return _install
