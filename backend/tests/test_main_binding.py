"""The backend listens on this Mac only: the dashboard has no login, and the page reaches it through Vite's proxy.

Reads main.py instead of running it: CI installs requirements-test.txt only, and the routers
main.py mounts need packages (openai, passlib, jwt, pandas) that file leaves out.
"""
import ast
from pathlib import Path


def test_backend_listens_on_this_mac_only():
    tree = ast.parse((Path(__file__).resolve().parents[1] / "main.py").read_text(encoding="utf-8"))
    hosts = [kw.value.value for node in ast.walk(tree)
             if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "run"
             for kw in node.keywords if kw.arg == "host"]
    assert hosts == ["127.0.0.1"]
