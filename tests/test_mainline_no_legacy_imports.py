"""Mainline ``src/`` must not import removed legacy packages or ``archive/``."""

from __future__ import annotations

from pathlib import Path

_BANNED = (
    "src.backtest.legacy",
    "src.combiner.legacy",
    "from archive",
    "import archive",
)


def test_src_tree_has_no_banned_legacy_import_substrings():
    root = Path(__file__).resolve().parents[1] / "src"
    for path in sorted(root.rglob("*.py")):
        if "Archive" in path.parts:
            continue
        text = path.read_text(encoding="utf-8")
        for b in _BANNED:
            assert b not in text, f"{path.relative_to(root.parent)} contains forbidden substring {b!r}"
