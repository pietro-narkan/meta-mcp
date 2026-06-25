import os

# Garantiza que importar meta_ads_mcp.* nunca falle por falta de token en tests.
os.environ.setdefault("META_ACCESS_TOKEN", "TEST_DUMMY_TOKEN")
