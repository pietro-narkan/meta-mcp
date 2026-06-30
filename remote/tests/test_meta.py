import httpx
import pytest
import respx

from app.meta import MetaClient, MetaError


@respx.mock
async def test_get_builds_url_and_returns_json():
    route = respx.get("https://graph.facebook.com/v25.0/act_123/campaigns").mock(
        return_value=httpx.Response(200, json={"data": [{"id": "1"}]})
    )
    client = MetaClient("TOK")
    out = await client.get("act_123/campaigns", {"fields": "id"})
    assert out == {"data": [{"id": "1"}]}
    assert route.called
    sent = route.calls.last.request
    assert sent.headers["Authorization"] == "Bearer TOK"
    assert "access_token" not in sent.url.params
    assert sent.url.params["fields"] == "id"


@respx.mock
async def test_get_raises_metaerror_on_http_error():
    respx.get("https://graph.facebook.com/v25.0/me").mock(
        return_value=httpx.Response(400, json={"error": {"message": "Bad token"}})
    )
    client = MetaClient("TOK")
    with pytest.raises(MetaError) as exc:
        await client.get("me")
    assert "Bad token" in str(exc.value)
