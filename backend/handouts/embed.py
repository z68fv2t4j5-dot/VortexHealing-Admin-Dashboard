"""Embeddings from LM Studio's nomic model. Returns None when LM Studio is not reachable,
so callers fall back to keyword search instead of failing."""
import logging
from typing import Optional

import httpx
import numpy as np

MODEL = "text-embedding-nomic-embed-text-v1.5"
# nomic is trained with these task prefixes; leaving them off weakens retrieval.
PREFIX = {"document": "search_document: ", "query": "search_query: "}
BATCH = 32

logger = logging.getLogger(__name__)


def embed(texts: list[str], kind: str) -> Optional[np.ndarray]:
    from app.core.config import settings

    vectors: list[list[float]] = []
    try:
        with httpx.Client(timeout=120) as client:
            for i in range(0, len(texts), BATCH):
                batch = [PREFIX[kind] + t for t in texts[i:i + BATCH]]
                r = client.post(f"{settings.LM_STUDIO_URL}/embeddings", json={"model": MODEL, "input": batch})
                r.raise_for_status()
                vectors += [d["embedding"] for d in sorted(r.json()["data"], key=lambda d: d["index"])]
    except (httpx.HTTPError, KeyError, ValueError) as e:
        logger.warning("Embeddings unavailable (%s); using keyword search only", e)
        return None
    v = np.asarray(vectors, dtype=np.float32)
    return v / (np.linalg.norm(v, axis=1, keepdims=True) + 1e-12)
