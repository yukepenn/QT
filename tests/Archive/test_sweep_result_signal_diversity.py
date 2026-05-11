"""Tests for sweep_result_signal_diversity helpers."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.research.scoring import passes_filters
from src.research.sweep_result_signal_diversity import merged_config_from_row, run_audit
from src.research.select_candidates import unflatten_config_from_row


def test_unflatten_roundtrip_nested_keys():
    row = pd.Series(
        {
            "signal.entry_start_minute": 45,
            "signal.entry_end_minute": 200,
            "risk.target_r": 1.5,
            "params_json": "",
        }
    )
    cfg = unflatten_config_from_row(row)
    assert cfg["signal"]["entry_start_minute"] == 45
    assert cfg["risk"]["target_r"] == 1.5


def test_merged_config_from_row_includes_strategy_overlay():
    row = pd.Series(
        {
            "signal.side": "long_only",
            "params_json": "",
        }
    )
    m = merged_config_from_row(
        "pa_climax_reversal", row, base_cfg=None
    )
    assert m.get("strategy") == "pa_climax_reversal"
    assert m["signal"]["side"] == "long_only"


def test_passes_filters_max_drawdown_boundary():
    ns = pytest.importorskip("argparse").Namespace(
        min_trades=30,
        min_profit_factor=1.05,
        min_total_r=0.0,
        max_drawdown_r=-50.0,
        max_avg_bars_held=120.0,
        max_eod_count=0,
        max_end_of_data_count=0,
    )
    ok_row = pd.Series(
        {
            "trades": 40,
            "profit_factor": 1.1,
            "total_r": 1.0,
            "max_drawdown_r": -10.0,
            "avg_bars_held": 10.0,
            "eod_count": 0,
            "end_of_data_count": 0,
        }
    )
    bad_row = pd.Series(
        {
            "trades": 40,
            "profit_factor": 1.1,
            "total_r": 1.0,
            "max_drawdown_r": -60.0,
            "avg_bars_held": 10.0,
            "eod_count": 0,
            "end_of_data_count": 0,
        }
    )
    assert passes_filters(ok_row, ns) is True
    assert passes_filters(bad_row, ns) is False


def test_run_audit_empty_strict_writes_headers():
    import argparse as ap

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        csv_path = td_path / "results.csv"
        csv_path.write_text(
            "strategy,asset,symbol,root,contract,start,end,params_json,trades,profit_factor,total_r,max_drawdown_r,avg_bars_held,eod_count,end_of_data_count\n"
            "pa_climax_reversal,equity,QQQ,,,2023-01-01,2024-12-31,{},10,1.0,-5.0,-3.0,50.0,0,0\n",
            encoding="utf-8",
        )
        ns = ap.Namespace(
            min_trades=30,
            min_profit_factor=1.05,
            min_total_r=0.0,
            max_drawdown_r=-50.0,
            max_avg_bars_held=120.0,
            max_eod_count=0,
            max_end_of_data_count=0,
        )
        out = td_path / "out"
        summary = run_audit(
            strategy="pa_climax_reversal",
            results_csv=csv_path,
            base_cfg=None,
            asset="equity",
            symbol="QQQ",
            start="2023-01-01",
            end="2024-12-31",
            output_root=out,
            top_pool=10,
            filter_ns=ns,
            top_per_signal_hash=3,
        )
        assert summary["n_strict_eligible"] == 0
        raw = (out / "raw_sweep_signal_diversity_pa_climax_reversal.csv").read_text(
            encoding="utf-8"
        )
        assert "row_rank" in raw.splitlines()[0]
