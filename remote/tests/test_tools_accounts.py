from app import tools


async def test_get_ad_accounts_shapes_output(fake):
    fake({"me/adaccounts": {"data": [
        {"account_id": "111", "name": "Bellas Todas", "account_status": 1, "currency": "CLP"},
    ]}})
    out = await tools.get_ad_accounts()
    assert out["total"] == 1
    assert out["accounts"][0]["id"] == "act_111"
    assert out["accounts"][0]["name"] == "Bellas Todas"
    assert out["accounts"][0]["active"] is True


async def test_check_token_status_reports_valid(fake):
    fake({"me": {"id": "123", "name": "plasa-backend"}})
    out = await tools.check_token_status()
    assert out["valid"] is True
    assert out["name"] == "plasa-backend"


async def test_discover_all_accounts_lists_ids(fake):
    fake({"me/adaccounts": {"data": [
        {"account_id": "111", "name": "A", "account_status": 1, "currency": "CLP"},
        {"account_id": "222", "name": "B", "account_status": 101, "currency": "CLP"},
    ]}})
    out = await tools.discover_all_accounts()
    assert {a["id"] for a in out["accounts"]} == {"act_111", "act_222"}
