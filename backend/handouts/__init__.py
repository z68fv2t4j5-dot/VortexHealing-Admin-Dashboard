"""Handouts knowledge base: catalogue, index and search over the English handouts.

Plan: docs/plans/PLAN-handouts-knowledge-base-2610212112.md. Everything derived
from the handouts lives in kb_dir(), outside the repository.
"""
from pathlib import Path


def source_dir() -> Path:
    from app.core.config import settings

    if not settings.HANDOUTS_DIR:
        raise RuntimeError("HANDOUTS_DIR is not set; add it to backend/.env (see backend/.env.example)")
    return Path(settings.HANDOUTS_DIR).expanduser()


def kb_dir() -> Path:
    from app.core.config import settings

    return Path(settings.HANDOUTS_KB_DIR).expanduser()
