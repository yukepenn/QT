"""Candidate priority / conflict hooks (scaffold)."""

from __future__ import annotations

from typing import Any


def rank_candidates(rows: list[dict[str, Any]], *, policy: str = "metadata_priority") -> list[int]:
    """Return indices into ``rows`` in descending priority (placeholder)."""
    _ = policy
    return list(range(len(rows)))
