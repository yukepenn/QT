from __future__ import annotations

import pandas as pd

from src.research.trade_enrichment import enrich_trades_with_context


def test_missing_optional_columns_handled() -> None:
    trades = pd.DataFrame(
        {
            "entry_ts_utc": ["2025-01-02T14:31:00Z"],
            "r_multiple": [1.0],
        }
    )
    feats = pd.DataFrame({"ts_utc": ["2025-01-02T14:31:00Z"]})
    out = enrich_trades_with_context(trades, feats)
    assert "entry_minute_bucket" in out.columns
    assert "gap_direction" in out.columns
    assert "vwap_side_at_entry" in out.columns


def test_lookahead_columns_removed() -> None:
    trades = pd.DataFrame({"entry_ts_utc": ["2025-01-02T14:31:00Z"], "r_multiple": [1.0]})
    feats = pd.DataFrame(
        {
            "ts_utc": ["2025-01-02T14:31:00Z"],
            "full_session_high_LOOKAHEAD": [999.0],
        }
    )
    out = enrich_trades_with_context(trades, feats)
    assert "full_session_high_LOOKAHEAD" not in out.columns


def test_entry_minute_bucket_computed() -> None:
    # 09:31 ET
    trades = pd.DataFrame({"entry_ts_utc": ["2025-01-02T14:31:00Z"], "r_multiple": [1.0]})
    feats = pd.DataFrame({"ts_utc": ["2025-01-02T14:31:00Z"]})
    out = enrich_trades_with_context(trades, feats)
    assert out.loc[0, "entry_minute_bucket"] == "0-15"


def test_gap_direction_and_pct_computed() -> None:
    trades = pd.DataFrame({"entry_ts_utc": ["2025-01-02T14:31:00Z"], "r_multiple": [1.0]})
    feats = pd.DataFrame(
        {
            "ts_utc": ["2025-01-02T14:31:00Z"],
            "prior_day_close": [100.0],
            "day_open": [101.0],
        }
    )
    out = enrich_trades_with_context(trades, feats)
    assert out.loc[0, "gap_direction"] == "gap_up"
    assert float(out.loc[0, "gap_pct"]) == 0.01


def test_vwap_side_computed_if_available() -> None:
    trades = pd.DataFrame({"entry_ts_utc": ["2025-01-02T14:31:00Z"], "r_multiple": [1.0]})
    feats = pd.DataFrame(
        {
            "ts_utc": ["2025-01-02T14:31:00Z"],
            "close": [101.0],
            "vwap": [100.0],
        }
    )
    out = enrich_trades_with_context(trades, feats)
    assert out.loc[0, "vwap_side_at_entry"] == "above_vwap"

