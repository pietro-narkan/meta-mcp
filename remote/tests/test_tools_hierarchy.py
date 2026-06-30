from app import tools


async def test_get_campaigns_counts_statuses(fake):
    c = fake({"act_111/campaigns": {"data": [
        {"id": "1", "name": "C1", "status": "ACTIVE", "effective_status": "ACTIVE", "objective": "OUTCOME_SALES"},
        {"id": "2", "name": "C2", "status": "PAUSED", "effective_status": "PAUSED", "objective": "OUTCOME_SALES"},
    ]}})
    out = await tools.get_campaigns("111")  # acepta sin act_
    assert out["total"] == 2
    assert out["status_counts"] == {"ACTIVE": 1, "PAUSED": 1}
    assert out["campaigns"][0]["name"] == "C1"
    assert c.calls[0][0] == "act_111/campaigns"


async def test_get_campaign_details_returns_node(fake):
    fake({"120": {"id": "120", "name": "Camp", "status": "ACTIVE", "objective": "OUTCOME_SALES"}})
    out = await tools.get_campaign_details("120")
    assert out["id"] == "120" and out["name"] == "Camp"


async def test_get_adsets_and_ads(fake):
    fake({
        "act_9/adsets": {"data": [{"id": "a1", "name": "AS", "status": "PAUSED", "daily_budget": "2000"}]},
        "act_9/ads": {"data": [{"id": "d1", "name": "AD", "status": "ACTIVE"}]},
    })
    asets = await tools.get_adsets("act_9")
    ads = await tools.get_ads("act_9")
    assert asets["adsets"][0]["daily_budget"] == "2000"
    assert ads["ads"][0]["id"] == "d1"
