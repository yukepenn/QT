"""Generic candidate arbitration (no fills, no PnL).

Selection helpers pick **which** candidate fires when several are active on
the same bar. The canonical simulator still lives under ``legacy/`` until the
execution-backed combiner loop is complete.
"""

from __future__ import annotations

from typing import Any, Callable, Hashable, Sequence, TypeVar

T = TypeVar("T")


def choose_highest_priority(
    candidates: Sequence[T],
    *,
    priority_key: Callable[[T], float],
    tie_key: Callable[[T, int], Hashable] | None = None,
) -> int | None:
    """Return index of winning candidate (max priority), deterministic on ties.

    ``tie_key`` receives ``(candidate, index)`` so callers can supply stable
    ordering (e.g. lexicographic ``candidate_id``).
    """
    if not candidates:
        return None
    best_i = 0
    best_p = priority_key(candidates[0])
    for i in range(1, len(candidates)):
        p = priority_key(candidates[i])
        if p > best_p:
            best_p = p
            best_i = i
        elif p == best_p:
            a = (tie_key(candidates[best_i], best_i) if tie_key else best_i)
            b = (tie_key(candidates[i], i) if tie_key else i)
            if b < a:
                best_i = i
    return best_i


def rank_candidates(
    rows: list[dict[str, Any]],
    *,
    priority_col: str = "priority",
    id_col: str = "candidate_id",
) -> list[int]:
    """Return row indices sorted by descending ``priority_col``, stable ties."""
    if not rows:
        return []

    def prio(row: dict[str, Any]) -> float:
        v = row.get(priority_col, 0.0)
        try:
            return float(v)
        except (TypeError, ValueError):
            return 0.0

    indexed = list(enumerate(rows))

    def sort_key(item: tuple[int, dict[str, Any]]) -> tuple[float, str, int]:
        i, row = item
        cid = str(row.get(id_col, ""))
        return (-prio(row), cid, i)

    indexed.sort(key=sort_key)
    return [i for i, _ in indexed]
