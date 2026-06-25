WRITE_TOOLS = {
    "create_campaign", "update_campaign", "create_adset", "update_adset",
    "create_ad_from_manifest", "update_ad", "create_ad_creative", "update_ad_creative",
    "create_product_set", "update_product_set", "upload_ad_image", "upload_video_asset",
    "upload_video_resumable", "bulk_rename_objects", "delete_campaign_structure",
    "create_multi_asset_ad", "duplicate_campaign", "duplicate_adset", "send_test_event",
}
CORE_READ = {
    "check_token_status", "get_ad_accounts", "discover_all_accounts",
    "get_campaigns", "get_campaign_details", "get_adsets", "get_adset_details",
    "get_ads", "get_ad_details", "get_insights", "get_bulk_insights",
}


async def test_only_readonly_tools_are_registered():
    from meta_ads_mcp import server

    names = {t.name for t in await server.mcp.list_tools()}

    # El conjunto registrado es exactamente la allowlist declarada.
    assert names == server.READ_ONLY_TOOLS, f"diferencia: {names ^ server.READ_ONLY_TOOLS}"
    # Las tools núcleo de reporting están presentes.
    assert CORE_READ <= names, f"faltan núcleo: {CORE_READ - names}"
    # Ninguna tool de escritura se coló.
    assert not (names & WRITE_TOOLS), f"escritura filtrada: {names & WRITE_TOOLS}"
