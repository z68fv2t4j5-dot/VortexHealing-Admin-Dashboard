"""Is Qwen ready? Model status from LM Studio, and loading through its `lms` command.

A model that is not loaded is loaded by LM Studio on first use, with default settings and an idle
time-out: the first answer is slow and may run with a small context. Loading it here uses the MLX file,
the configured context and no time-out.
"""
import logging
import subprocess
import threading
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)
_loading = threading.Lock()


def _settings():
    from app.core.config import settings

    return settings


def status() -> dict:
    s = _settings()
    base = s.LM_STUDIO_URL.rsplit("/v1", 1)[0]
    try:
        models = httpx.get(f"{base}/api/v0/models", timeout=5).json()["data"]
    except (httpx.HTTPError, KeyError, ValueError):
        return {"lm_studio": False, "qwen": False, "embedder": False, "loading": _loading.locked()}
    loaded = {m["id"]: m for m in models if m.get("state") == "loaded"}
    qwen = loaded.get(s.QWEN_MODEL)
    return {"lm_studio": True, "qwen": qwen is not None, "embedder": s.EMBED_MODEL in loaded,
            "qwen_context": qwen.get("loaded_context_length") if qwen else None,
            "loading": _loading.locked()}


def load_commands() -> list[list[str]]:
    s = _settings()
    lms = str(Path(s.LMS_PATH).expanduser())
    return [[lms, "server", "start"],
            [lms, "load", s.QWEN_LOAD_KEY, "--identifier", s.QWEN_MODEL, "--context-length", str(s.QWEN_CONTEXT), "-y"],
            [lms, "load", s.EMBED_MODEL, "-y"]]


def load() -> bool:
    """Loads whatever is missing, in the background; False when a load is already running."""
    if _loading.locked():
        return False
    threading.Thread(target=_load, daemon=True).start()
    return True


def _load() -> None:
    with _loading:
        current = status()
        for cmd in load_commands():
            if "load" in cmd and ((cmd[2] == _settings().QWEN_LOAD_KEY and current["qwen"])
                                  or (cmd[2] == _settings().EMBED_MODEL and current["embedder"])):
                continue
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=600)
            except (OSError, subprocess.SubprocessError) as e:
                logger.warning("Model command failed (%s): %s", " ".join(cmd[1:3]), e)
