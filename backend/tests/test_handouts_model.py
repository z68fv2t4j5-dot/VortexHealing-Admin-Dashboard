import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import handouts as api
from app.core.config import settings
from handouts import model


def lm_studio(monkeypatch, models=None, down=False):
    def get(url, timeout):
        if down:
            raise httpx.ConnectError("down")
        return httpx.Response(200, json={"data": models or []}, request=httpx.Request("GET", url))
    monkeypatch.setattr(model.httpx, "get", get)


def test_status_reports_what_is_loaded(monkeypatch):
    lm_studio(monkeypatch, [{"id": settings.QWEN_MODEL, "state": "loaded", "loaded_context_length": 32768},
                            {"id": settings.EMBED_MODEL, "state": "not-loaded"}])
    assert model.status() == {"lm_studio": True, "qwen": True, "embedder": False, "qwen_context": 32768, "loading": False}
    lm_studio(monkeypatch, down=True)
    assert model.status() == {"lm_studio": False, "qwen": False, "embedder": False, "loading": False}


def test_load_uses_the_mlx_file_the_context_and_the_identifier():
    server, qwen, embed = model.load_commands()
    assert server[1:] == ["server", "start"]
    assert qwen[1:] == ["load", settings.QWEN_LOAD_KEY, "--identifier", settings.QWEN_MODEL,
                        "--context-length", str(settings.QWEN_CONTEXT), "-y"]
    assert embed[1:3] == ["load", settings.EMBED_MODEL]


def test_load_skips_what_is_already_loaded(monkeypatch):
    lm_studio(monkeypatch, [{"id": settings.QWEN_MODEL, "state": "loaded"}])
    ran = []
    monkeypatch.setattr(model.subprocess, "run", lambda cmd, **kw: ran.append(cmd[1:3]))
    model._load()
    assert ran == [["server", "start"], ["load", settings.EMBED_MODEL]]


def test_a_failing_command_does_not_stop_the_others(monkeypatch):
    lm_studio(monkeypatch, [])
    ran = []

    def run(cmd, **kw):
        ran.append(cmd[1])
        if cmd[1] == "server":
            raise OSError("no lms")
    monkeypatch.setattr(model.subprocess, "run", run)
    model._load()
    assert ran == ["server", "load", "load"]


def test_api_status_and_load(monkeypatch):
    lm_studio(monkeypatch, down=True)
    app = FastAPI()
    app.include_router(api.router, prefix="/api")
    client = TestClient(app)
    assert client.get("/api/handouts/model").json()["lm_studio"] is False
    monkeypatch.setattr(model, "load", lambda: True)
    assert client.post("/api/handouts/model/load").json() == {"started": True}
