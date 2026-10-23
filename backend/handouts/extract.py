"""Extract plain text from document files.

Supported formats:
  .doc / .docx  – converted via macOS ``textutil``
  .pdf          – parsed with ``pypdf``

Any other extension raises ``ValueError``.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def extract_text(path: str | Path) -> str:
    """Return the plain-text content of *path*.

    Raises
    ------
    ValueError
        If the file extension is not one of the supported types.
    subprocess.CalledProcessError
        If ``textutil`` fails (only for .doc/.docx).
    FileNotFoundError
        If the file does not exist.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    suffix = p.suffix.lower()

    if suffix in (".doc", ".docx"):
        return _extract_doc(p)
    elif suffix == ".pdf":
        return _extract_pdf(p)
    else:
        raise ValueError(
            f"Unsupported file type '{suffix}'. "
            "Expected .doc, .docx, or .pdf."
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _extract_doc(p: Path) -> str:
    """Convert .doc/.docx to plain text using macOS textutil."""
    result = subprocess.run(
        ["textutil", "-convert", "txt", "-stdout", str(p)],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def _extract_pdf(p: Path) -> str:
    """Extract text from a PDF using pypdf."""
    from pypdf import PdfReader

    reader = PdfReader(str(p))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)