import runpy
from pathlib import Path


def test_main_module_can_run_as_script(monkeypatch):
    monkeypatch.setenv("LEADGEN_SKIP_SERVER", "1")
    module_globals = runpy.run_path(str(Path(__file__).resolve().parents[1] / "app" / "main.py"), run_name="__main__")

    assert "app" in module_globals
    assert module_globals["app"].title == "Coldmailer Automation API"
