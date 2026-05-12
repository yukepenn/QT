"""Helpers to normalize or validate canonical ``sig_*`` signal columns."""

from __future__ import annotations

from typing import Any, Mapping

import pandas as pd

from src.strategies.metadata import get_strategy_output_contract
from src.strategies.strategy.base import STANDARD_SIGNAL_COLUMNS, validate_standard_signal_columns


def infer_signal_mapping(strategy_name: str, metadata: Mapping[str, Any] | None = None) -> dict[str, str]:
    """Return optional ``old_name -> sig_*`` renames from strategy output contract.

    ``metadata.yaml`` may define ``output_contract`` with non-standard column
    names. Unknown keys are ignored.
    """
    del metadata
    oc = get_strategy_output_contract(strategy_name)
    if not isinstance(oc, dict):
        return {}
    out: dict[str, str] = {}
    for k, v in oc.items():
        if isinstance(k, str) and isinstance(v, str) and v.startswith("sig_"):
            out[k] = v
    return out


def canonicalize_signal_frame(
    df: pd.DataFrame,
    mapping: Mapping[str, str] | None = None,
    *,
    copy: bool = True,
) -> pd.DataFrame:
    """Rename columns via ``mapping`` (``source_col`` → ``sig_*`` target).

    Does not invent OHLC or session columns. After renames, missing
    ``STANDARD_SIGNAL_COLUMNS`` are reported by :func:`validate_canonical_signal_frame`.
    """
    out = df.copy() if copy else df
    if not mapping:
        return out
    rename = {k: v for k, v in mapping.items() if k in out.columns and k != v}
    if rename:
        out = out.rename(columns=rename)
    return out


def validate_canonical_signal_frame(df: pd.DataFrame) -> list[str]:
    """Return semantic issues for valid rows (empty means OK).

    Raises ``ValueError`` if required standard signal columns are missing
    (same contract as :func:`validate_standard_signal_columns`).
    """
    validate_standard_signal_columns(df)
    issues: list[str] = []
    for i, row in df.iterrows():
        v = row.get("sig_valid")
        if pd.isna(v) or not bool(v):
            continue
        tm = str(row.get("sig_target_mode", "") or "").strip().lower()
        if tm not in ("fixed_r", "fixed_price", "none"):
            issues.append(f"row {i}: invalid sig_target_mode {tm!r}")
        sd = row.get("sig_side")
        if pd.isna(sd) or int(sd) == 0:
            issues.append(f"row {i}: sig_valid True but sig_side is zero or NaN")
        if pd.isna(row.get("sig_stop")):
            issues.append(f"row {i}: sig_valid True but sig_stop is NaN")
    return issues


def assert_canonical_signal_frame(df: pd.DataFrame) -> None:
    """Raise ``ValueError`` if :func:`validate_canonical_signal_frame` finds issues."""
    miss = [c for c in STANDARD_SIGNAL_COLUMNS if c not in df.columns]
    if miss:
        raise ValueError(f"missing standard signal columns: {miss}")
    issues = validate_canonical_signal_frame(df)
    if issues:
        raise ValueError("canonical signal validation failed: " + "; ".join(issues))
