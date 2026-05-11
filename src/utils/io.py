"""Small IO helpers."""

from __future__ import annotations

from pathlib import Path


def read_text(path: Path) -> str:
    return Path(path).read_text(encoding="utf-8")
