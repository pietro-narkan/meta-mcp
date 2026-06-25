# tests/test_healthcheck.py
import importlib.util
import pathlib

_spec = importlib.util.spec_from_file_location(
    "healthcheck", pathlib.Path(__file__).parent.parent / "scripts" / "healthcheck.py"
)
healthcheck = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(healthcheck)


def test_format_report_lists_accounts_and_status():
    data = {
        "name": "plasa-backend",
        "accounts": [
            {"account_id": "111", "name": "Bellas Todas", "account_status": 1},
            {"account_id": "222", "name": "Narkan", "account_status": 101},
        ],
    }
    out = healthcheck.format_report(data)
    assert "Token válido" in out
    assert "Cuentas accesibles: 2" in out
    assert "act_111" in out and "Bellas Todas" in out and "(activa)" in out
    assert "act_222" in out and "estado 101" in out
