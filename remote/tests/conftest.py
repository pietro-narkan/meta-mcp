import os
import pytest
from app import tools

os.environ.setdefault("META_ACCESS_TOKEN", "TEST_DUMMY_TOKEN")


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
