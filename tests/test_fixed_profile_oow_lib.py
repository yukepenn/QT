"""Tests for fixed-profile OOW helpers (no combiner, no heavy trade files)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.research.fixed_profile_oow_lib import (
    FixedProfileSpec,
    combiner_argv,
    decide_label,
    default_windows,
    exit_slip_scenarios_table,
    insample_expected_rows,
    load_window_bounds,
    max_drawdown_r,
    metrics_from_trades,
    sanity_pass,
    score_transfer_rows,
)


def test_max_drawdown_r() -> None:
    assert max_drawdown_r(np.array([1.0, -2.0, 1.0])) < 0


def test_metrics_from_trades_trade_numbers() -> None:
    df = pd.DataFrame(
        {
            "session_date": ["2023-01-03"] * 3,
            "entry_ts_utc": ["2023-01-03T14:31:00Z", "2023-01-03T15:00:00Z", "2023-01-03T16:00:00Z"],
            "r_multiple": [1.0, -0.5, 0.25],
            "exit_reason": ["target", "stop", "target"],
            "strategy": ["a", "a", "a"],
            "strategy_family": ["vwap", "vwap", "vwap"],
        }
    )
    m = metrics_from_trades(df)
    assert m["trades"] == 3
    assert m["trade_1_total_r"] == 1.0
    assert m["trade_2_total_r"] == -0.5
    assert m["trade_3_total_r"] == 0.25


def test_sanity_pass_tolerance() -> None:
    ref = {"trades_ref": 100, "total_r_ref": 10.0}
    assert sanity_pass({"trades": 104, "total_r": 11.0}, ref) is True
    assert sanity_pass({"trades": 200, "total_r": 11.0}, ref) is False


def test_default_windows_clip() -> None:
    w = default_windows("2021-01-01", "2025-06-30")
    ids = {x.window_id for x in w}
    assert "insample_ref" in ids
    late = next(x for x in w if x.window_id == "late_oow")
    assert late.start == "2025-01-01"
    assert late.end <= "2026-12-31"


def test_decide_label_no_runs() -> None:
    assert decide_label([]) == "NEED_MORE_FIXED_PROFILE_OOW"
    assert decide_label([{"status": "NOT_RUN", "profile_id": "vwap_mtp2", "window_id": "early_oow"}]) == "NEED_MORE_FIXED_PROFILE_OOW"


def test_exit_slip_scenarios_table_minimal() -> None:
    df = pd.DataFrame(
        {
            "r_multiple": [1.0, -0.5],
            "risk_per_share": [0.5, 0.5],
            "exit_reason": ["take_profit", "stop_loss"],
        }
    )
    sm = exit_slip_scenarios_table(df, "u")
    assert len(sm) == 4
    assert set(sm["scenario"]) == {"published", "symmetric_stress", "target_limit_stress", "symmetric_extreme"}


def test_combiner_argv_has_no_signal_cache_flag() -> None:
    from pathlib import Path

    spec = FixedProfileSpec("vwap_mtp2", "layer2_fixed_vwap_mtp2.yaml", "vwap_core")
    argv = combiner_argv(
        repo_root=Path("/repo"),
        output_root=Path("/out"),
        spec=spec,
        window_id="insample_ref",
        start="2023-01-01",
        end="2024-12-31",
        python_executable="python",
    )
    joined = " ".join(argv)
    assert "--use-signal-cache" not in joined
    assert "src.combiner.run" in joined
    assert "vwap_core" in joined


def test_load_window_bounds_from_csv(tmp_path) -> None:
    from src.research.fixed_profile_oow_lib import load_window_bounds

    root = tmp_path / "r"
    root.mkdir()
    pd.DataFrame(
        [
            {"window_id": "insample_ref", "window_start": "2023-01-01", "window_end": "2024-12-31"},
            {"window_id": "early_oow", "window_start": "2020-01-01", "window_end": "2022-12-31"},
        ]
    ).to_csv(root / "data_availability.csv", index=False)
    b = load_window_bounds(root, data_dir=tmp_path)
    assert b["insample_ref"] == ("2023-01-01", "2024-12-31")
    tax = tmp_path / "tax.csv"
    tax.write_text(
        "family,setup_type,broader_class,example_strategies,likely_affinity_regimes,likely_avoid_regimes,notes\n"
        "vwap,x,y,z,a,b,c\n",
        encoding="utf-8",
    )
    df = pd.DataFrame(
        {
            "session_date": ["2023-06-01", "2024-06-01", "2025-01-02"],
            "r_multiple": [1.0, 1.0, 0.5],
            "exit_reason": ["target", "target", "target"],
            "entry_regime_label": ["trading_range", "trading_range", "trading_range"],
            "entry_family": ["vwap", "vwap", "vwap"],
        }
    )
    rows = score_transfer_rows(df, taxonomy=tax, analysis_dir=None, train_start="2023-01-01", train_end="2024-12-31", test_label="t")
    subs = {r["subset"]: r for r in rows}
    assert subs["train_all"]["trades"] == 2
    assert subs["test_all"]["trades"] == 1
    assert "top80_train_thr" in subs
