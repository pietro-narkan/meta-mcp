"""Entry point for running the MCP server via `python -m meta_ads_mcp` or `uv run`."""
from meta_ads_mcp.runtime_env import load_environment

load_environment()

from meta_ads_mcp.server import main

if __name__ == "__main__":
    main()
