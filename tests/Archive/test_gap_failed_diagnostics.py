from __future__ import annotations

import pandas as pd

from src.research.gap_failed_diagnostics import (
    _bucket_entry_minute,
    _bucket_risk,
    _group_summary,
)


def test_bucket_risk() -> None:
    s = pd.Series([0.01, 0.03, 0.049, 0.05, 0.11, None])
    b = _bucket_risk(s)
    assert list(b) == ["<0.03", "0.03-0.05", "0.03-0.05", "0.05-0.10", ">0.10", "unknown"]


def test_bucket_entry_minute_handles_parse() -> None:
    # 2025-12-01 14:31Z == 09:31 ET (1 minute after open)
    s = pd.Series(["2025-12-01T14:31:00Z", None])
    b = _bucket_entry_minute(s)
    assert b.iloc[0] == "0-15"
    assert b.iloc[1] == "unknown"


def test_group_summary_missing_column() -> None:
    df = pd.DataFrame({"r_multiple": [1, -1]})
    out = _group_summary(df, "exit_reason")
    assert out.iloc[0]["group"] == "MISSING_COLUMN"


def test_group_summary_basic() -> None:
    df = pd.DataFrame({"exit_reason": ["stop", "stop", "target"], "r_multiple": [-1.0, -1.0, 1.0]})
    out = _group_summary(df, "exit_reason")
    assert set(out["group"]) == {"stop", "target"}

