"""The backend listens on this Mac only: the dashboard has no login, and the page reaches it through Vite's proxy."""
import runpy
from pathlib import Path

import uvicorn


def test_backend_listens_on_this_mac_only(monkeypatch):
    calls = []
    monkeypatch.setattr(uvicorn, "run", lambda *args, **kwargs: calls.append(kwargs))
    runpy.run_path(str(Path(__file__).resolve().parents[1] / "main.py"), run_name="__main__")
    assert calls and calls[0]["host"] == "127.0.0.1"
