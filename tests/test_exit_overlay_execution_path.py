"""Pure helpers for ``run_exit_overlay_execution_path`` (no heavy data)."""

from __future__ import annotations

import pandas as pd
import pytest

from src.execution.types import TradeIntent
from src.research.run_exit_overlay_execution_path import (
    OVERLAY_REGISTRY,
    aggregate_replay,
    apply_overlay,
    normalize_overlay_names,
)
from src.combiner.run import _combiner_cfg_from_yaml


def test_normalize_overlay_names_case_and_separators() -> None:
    assert normalize_overlay_names("Trend_Swing-2R, MAX_hold ") == ["trend_swing_2r", "max_hold"]


def test_overlay_registry_contains_expected_ids() -> None:
    assert "baseline_execution_backed" in OVERLAY_REGISTRY
    assert "trend_swing_2r" in OVERLAY_REGISTRY
    assert "trail_after_1r_simple" in OVERLAY_REGISTRY


def test_apply_overlay_trail_and_runner_are_unsupported_not_faked() -> None:
    intent = TradeIntent(
        candidate_id="X",
        strategy="s",
        side=1,
        signal_idx=0,
        entry_idx=1,
        stop_price=99.0,
        max_hold_bars=120,
        management_mode="none",
        target_mode="fixed_r",
        target_r=1.5,
    )
    cfg = _combiner_cfg_from_yaml({"execution": {"slippage_per_share": 0.01}})
    ni, plan, st, note = apply_overlay("trail_after_1r_simple", intent, max_hold_bars=120, combiner_cfg=cfg)
    assert ni is None and plan is None and st == "unsupported" and "TrailingRule" in note
    ni2, plan2, st2, note2 = apply_overlay("runner_after_1r_reference", intent, max_hold_bars=120, combiner_cfg=cfg)
    assert ni2 is None and plan2 is None and st2 == "unsupported" and "ladder" in note2


def test_aggregate_replay_empty_schema() -> None:
    agg = aggregate_replay(pd.DataFrame())
    assert agg["trades"] == 0
    assert agg["profit_factor_r"] == ""


def test_aggregate_replay_profit_factor_is_string_when_finite() -> None:
    df = pd.DataFrame({"r_multiple": [1.0, -1.0], "exit_reason": ["target", "stop"]})
    agg = aggregate_replay(df)
    assert agg["trades"] == 2
    assert isinstance(agg["profit_factor_r"], str)
    assert agg["profit_factor_r"] == "1.0"


@pytest.mark.parametrize("bad", ["unknown_overlay_xyz", "not_in_registry"])
def test_main_rejects_unknown_overlay(bad: str) -> None:
    from src.research.run_exit_overlay_execution_path import main

    rc = main(
        [
            "--dry-run",
            "--profile",
            "pa_only_mtp1_meta",
            "--overlays",
            bad,
            "--output-root",
            "src/research/results/exit_overlay_execution_path",
        ]
    )
    assert rc == 2
