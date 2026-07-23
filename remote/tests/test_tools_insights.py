from app import tools


async def test_get_insights_passes_date_preset(fake):
    c = fake({"act_5/insights": {"data": [{"spend": "184908", "impressions": "42178", "clicks": "1740", "ctr": "4.12"}]}})
    out = await tools.get_insights("5", date_preset="last_7d")
    assert out["data"][0]["spend"] == "184908"
    assert out["data"][0]["purchases"] is None
    assert "atribuidos" in out["meta_attribution_notice"]
    assert c.calls[0][1]["date_preset"] == "last_7d"
    assert "actions" in c.calls[0][1]["fields"]
    assert "action_values" in c.calls[0][1]["fields"]
    assert "cost_per_action_type" in c.calls[0][1]["fields"]
    assert "purchase_roas" in c.calls[0][1]["fields"]


async def test_get_insights_normalizes_meta_conversion_metrics(fake):
    row = {
        "account_currency": "CLP",
        "spend": "100000",
        "actions": [
            {"action_type": "offsite_conversion.fb_pixel_purchase", "value": "4"},
            {"action_type": "omni_purchase", "value": "5"},
            {"action_type": "omni_add_to_cart", "value": "20"},
            {"action_type": "omni_initiated_checkout", "value": "10"},
            {"action_type": "lead", "value": "8"},
            {
                "action_type": "onsite_conversion.messaging_conversation_started_7d",
                "value": "25",
            },
            {"action_type": "onsite_conversion.messaging_first_reply", "value": "18"},
        ],
        "action_values": [
            {"action_type": "omni_purchase", "value": "320000"},
        ],
        "cost_per_action_type": [
            {"action_type": "omni_purchase", "value": "20000"},
            {
                "action_type": "onsite_conversion.messaging_conversation_started_7d",
                "value": "4000",
            },
        ],
        "purchase_roas": [
            {"action_type": "omni_purchase", "value": "3.2"},
        ],
    }
    fake({"act_5/insights": {"data": [row]}})

    out = await tools.get_insights("act_5")
    metrics = out["data"][0]

    # omni_* se prefiere para no duplicar el mismo evento entre canales.
    assert metrics["purchases"] == "5"
    assert metrics["purchase_conversion_value"] == "320000"
    assert metrics["cost_per_purchase"] == "20000"
    assert metrics["roas"] == "3.2"
    assert metrics["add_to_cart"] == "20"
    assert metrics["initiate_checkout"] == "10"
    assert metrics["leads"] == "8"
    assert metrics["messaging_conversations_started"] == "25"
    assert metrics["cost_per_messaging_conversation_started"] == "4000"
    assert metrics["messaging_first_replies"] == "18"
    # Las matrices originales de Meta se conservan.
    assert metrics["actions"] == row["actions"]
    assert metrics["action_values"] == row["action_values"]


async def test_get_insights_derives_cost_and_roas_only_from_meta_totals(fake):
    fake({
        "act_5/insights": {
            "data": [{
                "spend": "90",
                "actions": [{"action_type": "purchase", "value": "3"}],
                "action_values": [{"action_type": "purchase", "value": "270"}],
            }],
        },
    })

    out = await tools.get_insights("5")
    metrics = out["data"][0]

    assert metrics["cost_per_purchase"] == "30.00"
    assert metrics["roas"] == "3.00"
    assert metrics["derived_from_meta_totals"] == ["cost_per_purchase", "roas"]


async def test_get_insights_uses_meta_conversion_arrays_as_fallback(fake):
    fake({
        "act_5/insights": {
            "data": [{
                "spend": "50",
                "conversions": [{"action_type": "lead", "value": "2"}],
                "cost_per_conversion": [{"action_type": "lead", "value": "25"}],
            }],
        },
    })

    out = await tools.get_insights("5")
    metrics = out["data"][0]

    assert metrics["leads"] == "2"
    assert metrics["cost_per_lead"] == "25"


async def test_get_bulk_insights_uses_level(fake):
    c = fake({"act_5/insights": {"data": [{"campaign_name": "C", "spend": "10"}]}})
    out = await tools.get_bulk_insights("act_5", level="adset", date_preset="maximum")
    assert out["level"] == "adset"
    assert c.calls[0][1]["level"] == "adset"
    assert c.calls[0][1]["date_preset"] == "maximum"


async def test_get_bulk_insights_rejects_invalid_level_without_calling_meta(fake):
    c = fake({})
    out = await tools.get_bulk_insights("act_5", level="account")
    assert out["error"] == "level debe ser campaign, adset o ad"
    assert c.calls == []


def test_tools_has_exactly_eleven():
    names = [f.__name__ for f in tools.TOOLS]
    assert len(names) == 11
    assert "get_insights" in names and "get_bulk_insights" in names
    # ninguna de escritura
    assert not any(n.startswith(("create_", "update_", "delete_", "upload_", "duplicate_")) for n in names)
