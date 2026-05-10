"""Sweep dedupe keys must cover fields that affect final signal arrays for PA strategies."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from src.strategies.loader import load_strategy

_ROOT = Path(__file__).resolve().parents[1]
_PARAMS = _ROOT / "src" / "strategies" / "parameters"

PA_SPECS: list[tuple[str, list[tuple[str, object]]]] = [
    (
        "pa_trading_range_bls_hs",
        [
            ("signal.entry_start_minute", 99),
            ("risk.target_r", 3.0),
            ("risk.atr_buffer_mult", 0.99),
            ("risk.max_trades_per_day", 3),
        ],
    ),
    (
        "pa_buy_sell_close_trend",
        [
            ("signal.entry_end_minute", 333),
            ("signal.body_pct_min", 0.11),
            ("risk.min_risk_per_share", 0.07),
        ],
    ),
    (
        "pa_tight_channel_pullback",
        [
            ("signal.block_climax", False),
            ("signal.climax_score_max", 0.11),
            ("signal.entry_start_minute", 77),
        ],
    ),
    (
        "pa_broad_channel_zone",
        [
            ("signal.broad_bull_score_min", 0.11),
            ("signal.entry_start_minute", 77),
            ("features.pa_range_window", 55),
            ("signal.zone_max_frac", 0.55),
        ],
    ),
    (
        "pa_generic_breakout_pullback",
        [
            ("signal.recent_breakout_lookback", 12),
            ("risk.atr_buffer_mult", 0.88),
        ],
    ),
    (
        "pa_mtr_reversal",
        [
            ("signal.wedge_push_min", 9.0),
            ("signal.entry_start_minute", 88),
        ],
    ),
    (
        "pa_second_entry_pullback",
        [
            ("signal.context_score_min", 0.11),
            ("risk.max_trades_per_day", 4),
        ],
    ),
    (
        "pa_climax_reversal",
        [
            ("signal.climax_score_min", 0.11),
            ("signal.entry_end_minute", 333),
        ],
    ),
    (
        "pa_failed_range_breakout_trap",
        [
            ("signal.fail_window_bars", 9),
            ("risk.atr_buffer_mult", 0.88),
        ],
    ),
    (
        "pa_wedge_reversal",
        [
            ("signal.min_wedge_pushes", 9.0),
            ("signal.entry_end_minute", 333),
        ],
    ),
]


def _load_base(strategy: str) -> dict:
    path = _PARAMS / f"{strategy}.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("strategy,mutations", PA_SPECS)
def test_normalized_param_key_changes_on_signal_risk_fields(
    strategy: str, mutations: list[tuple[str, object]]
) -> None:
    strat = load_strategy(strategy)
    base = _load_base(strategy)
    k0 = strat.normalized_param_key(base)
    for dotted, val in mutations:
        cfg = deepcopy(base)
        cur: dict = cfg
        parts = dotted.split(".")
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
        cur[parts[-1]] = val
        k1 = strat.normalized_param_key(cfg)
        assert k1 != k0, f"{strategy}: key unchanged when setting {dotted}={val!r}"
