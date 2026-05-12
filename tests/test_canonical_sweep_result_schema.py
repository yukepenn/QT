"""Canonical sweep result columns (smoke / schema contract)."""

from __future__ import annotations

import src.backtest.sweep as sweep

REQUIRED = {
    "combo_id",
    "strategy",
    "config_hash",
    "trade_count",
    "total_r",
    "total_net_pnl",
    "total_gross_r",
    "max_drawdown_r",
    "avg_r",
    "win_rate",
    "profit_factor_r",
    "execution_semantics_version",
    "engine",
    "canonical_or_legacy",
    "symbol",
    "start",
    "end",
    "params_json",
    "notes",
}


def test_synthetic_sweep_has_schema_columns():
    df = sweep.run_synthetic_canonical_smoke()
    assert REQUIRED.issubset(set(df.columns))
    assert (df["engine"] == sweep.CANONICAL_ENGINE_LABEL).all()
    assert (df["canonical_or_legacy"] == "canonical").all()
    assert df["execution_semantics_version"].astype(str).str.len().gt(0).all()
