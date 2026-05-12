"""Committed strategy integration status table."""

from __future__ import annotations

import csv
from pathlib import Path


def test_integration_status_csv_has_champion_trio():
    root = Path(__file__).resolve().parents[1] / "docs" / "STRATEGY_INTEGRATION_STATUS.csv"
    with root.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    ids = {r["strategy"] for r in rows}
    for sid in ("pa_buy_sell_close_trend", "gap_acceptance_failure", "cci_extreme_snapback"):
        assert sid in ids
        row = next(r for r in rows if r["strategy"] == sid)
        assert row.get("loads") == "yes"
        assert row.get("generates_dataframe_signals") == "yes"
