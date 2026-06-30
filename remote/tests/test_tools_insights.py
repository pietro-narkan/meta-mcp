from app import tools


async def test_get_insights_passes_date_preset(fake):
    c = fake({"act_5/insights": {"data": [{"spend": "184908", "impressions": "42178", "clicks": "1740", "ctr": "4.12"}]}})
    out = await tools.get_insights("5", date_preset="last_7d")
    assert out["data"][0]["spend"] == "184908"
    assert c.calls[0][1]["date_preset"] == "last_7d"


async def test_get_bulk_insights_uses_level(fake):
    c = fake({"act_5/insights": {"data": [{"campaign_name": "C", "spend": "10"}]}})
    out = await tools.get_bulk_insights("act_5", level="adset", date_preset="maximum")
    assert out["level"] == "adset"
    assert c.calls[0][1]["level"] == "adset"
    assert c.calls[0][1]["date_preset"] == "maximum"


def test_tools_has_exactly_eleven():
    names = [f.__name__ for f in tools.TOOLS]
    assert len(names) == 11
    assert "get_insights" in names and "get_bulk_insights" in names
    # ninguna de escritura
    assert not any(n.startswith(("create_", "update_", "delete_", "upload_", "duplicate_")) for n in names)
