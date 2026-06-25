import os


def test_load_environment_loads_dotenv(tmp_path, monkeypatch):
    (tmp_path / ".env").write_text("META_ACCESS_TOKEN=FROM_DOTENV\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("META_ACCESS_TOKEN", raising=False)

    from meta_ads_mcp.runtime_env import load_environment

    load_environment()
    assert os.environ["META_ACCESS_TOKEN"] == "FROM_DOTENV"
