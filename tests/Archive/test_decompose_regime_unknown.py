"""Tests for regime_unknown decomposition helpers (no heavy trade files)."""
from __future__ import annotations

import pandas as pd

from src.research.decompose_regime_unknown import _system_label, run_one
from src.research.trade_quality_unknown import minute_bucket_open, prepare_unknown_frame, summarize_unknown_by


def test_minute_bucket_open_edges() -> None:
    s = pd.Series([0, 30, 31, 60, 61, 120, 121, 240, 241, float("nan")])
    b = minute_bucket_open(s)
    assert list(b)[:4] == ["m0_30", "m0_30", "m31_60", "m31_60"]
    assert b.iloc[4] == "m61_120"
    assert b.iloc[7] == "m121_240"
    assert b.iloc[8] == "m241p"
    assert b.iloc[9] == "missing"


def test_prepare_unknown_frame_and_summarize(tmp_path) -> None:
    df = pd.DataFrame(
        {
            "entry_regime_label": ["regime_unknown", "late_trend_climax", "regime_unknown"],
            "r_multiple": [1.0, -2.0, 3.0],
            "entry_minute_from_open": [10, 10, 90],
            "exit_reason": ["target", "stop", "target"],
            "entry_trade_number_of_day": [1, 1, 2],
        }
    )
    unk = prepare_unknown_frame(df)
    assert len(unk) == 2
    assert set(unk["unk_minute_bucket"]) == {"m0_30", "m61_120"}
    sm = summarize_unknown_by(unk, "unk_minute_bucket", min_n=1)
    assert len(sm) == 2
    assert sm["trades"].sum() == 2


def test_run_one_writes_csvs(tmp_path) -> None:
    df = pd.DataFrame(
        {
            "entry_regime_label": ["regime_unknown"] * 6,
            "r_multiple": [0.5, -0.2, 0.1, 0.3, -0.1, 0.2],
            "entry_minute_from_open": [5, 40, 70, 150, 200, 5],
            "entry_vwap_cross_count": [1, 2, 6, 12, 3, 1],
            "entry_range_efficiency": [0.1] * 6,
            "exit_reason": ["target"] * 5 + ["stop"],
            "entry_trade_number_of_day": [1, 1, 2, 2, 3, 1],
        }
    )
    p = tmp_path / "demo_sys_enriched.csv"
    df.to_csv(p, index=False)
    assert _system_label(p) == "demo_sys"
    keys = run_one(p, tmp_path / "out")
    out = tmp_path / "out" / "demo_sys"
    assert (out / "demo_sys_unknown_by_minute_bucket.csv").exists()
    assert isinstance(keys, list)


def test_summarize_unknown_by_missing_column() -> None:
    unk = pd.DataFrame({"r_multiple": [1.0], "unk_minute_bucket": ["m0_30"]})
    assert summarize_unknown_by(unk, "nonexistent").empty
