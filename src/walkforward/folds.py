"""Fixed smoke folds (calendar segments only — no rolling train/test)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class SmokeFold:
    fold_id: str
    label: str
    test_start: str
    test_end: str
    reference_start: str | None = None
    reference_end: str | None = None
    note: str | None = None


def _parse_date(s: str) -> datetime:
    return datetime.strptime(s.strip(), "%Y-%m-%d")


def load_smoke_folds(config: dict[str, Any]) -> list[SmokeFold]:
    raw = config.get("folds") or []
    folds: list[SmokeFold] = []
    for row in raw:
        folds.append(
            SmokeFold(
                fold_id=str(row["fold_id"]),
                label=str(row.get("label") or row["fold_id"]),
                test_start=str(row["test_start"]),
                test_end=str(row["test_end"]),
                reference_start=str(row["reference_start"]) if row.get("reference_start") else None,
                reference_end=str(row["reference_end"]) if row.get("reference_end") else None,
                note=str(row["note"]) if row.get("note") else None,
            )
        )
    validate_smoke_folds(folds)
    return folds


def validate_smoke_folds(folds: list[SmokeFold]) -> None:
    if not folds:
        raise ValueError("smoke folds: empty")
    seen: set[str] = set()
    for f in folds:
        if not str(f.fold_id).strip():
            raise ValueError("smoke folds: fold_id empty")
        if f.fold_id in seen:
            raise ValueError(f"smoke folds: duplicate fold_id {f.fold_id}")
        seen.add(f.fold_id)
        ts = _parse_date(f.test_start)
        te = _parse_date(f.test_end)
        if ts >= te:
            raise ValueError(f"smoke folds {f.fold_id}: test_start must be < test_end")
        if f.reference_start and f.reference_end:
            rs = _parse_date(f.reference_start)
            re = _parse_date(f.reference_end)
            if rs >= re:
                raise ValueError(f"smoke folds {f.fold_id}: reference_start must be < reference_end")
