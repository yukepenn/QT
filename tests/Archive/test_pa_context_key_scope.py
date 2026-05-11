"""PA strategies: context_key only partitions prepare_signal_context; thresholds live in normalized_param_key."""

from __future__ import annotations

from copy import deepcopy

import pytest

from src.strategies.loader import apply_overrides, load_strategy, load_strategy_config


def _base(name: str):
    return load_strategy(name), load_strategy_config(name)


def _assert_ctx_stable_npk_changes(
    strategy: str, overrides: dict[str, object]
) -> None:
    s, cfg0 = _base(strategy)
    k0 = s.context_key(cfg0)
    p0 = s.normalized_param_key(cfg0)
    cfg1 = apply_overrides(deepcopy(cfg0), overrides)
    assert s.context_key(cfg1) == k0
    assert s.normalized_param_key(cfg1) != p0


def _assert_ctx_changes(strategy: str, overrides: dict[str, object]) -> None:
    s, cfg0 = _base(strategy)
    k0 = s.context_key(cfg0)
    cfg1 = apply_overrides(deepcopy(cfg0), overrides)
    assert s.context_key(cfg1) != k0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signal.body_pct_min", 0.99),
        ("signal.trend_score_min", 0.01),
        ("signal.require_vwap_side", True),
    ],
)
def test_pa_buy_sell_close_trend_thresholds_not_in_context_key(
    field: str, value: object
) -> None:
    _assert_ctx_stable_npk_changes("pa_buy_sell_close_trend", {field: value})


def test_pa_buy_sell_close_trend_windows_and_atr_in_context_key() -> None:
    _assert_ctx_changes(
        "pa_buy_sell_close_trend", {"features.pa_range_window": 30}
    )
    _assert_ctx_changes(
        "pa_buy_sell_close_trend", {"features.pa_regime_window": 20}
    )
    _assert_ctx_changes(
        "pa_buy_sell_close_trend", {"signal.atr_column": "atr_like_14"}
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signal.climax_score_min", 0.99),
        ("signal.bear_context_min", 0.99),
        ("signal.max_dist_below_vwap_atr", 0.5),
    ],
)
def test_pa_climax_reversal_thresholds_not_in_context_key(
    field: str, value: object
) -> None:
    _assert_ctx_stable_npk_changes("pa_climax_reversal", {field: value})


def test_pa_climax_reversal_range_and_atr_in_context_key() -> None:
    _assert_ctx_changes("pa_climax_reversal", {"features.pa_range_window": 30})
    _assert_ctx_changes(
        "pa_climax_reversal", {"signal.atr_column": "atr_like_14"}
    )


def test_pa_climax_reversal_pa_regime_window_not_in_prepare() -> None:
    """prepare_signal_context only uses pa_range_window columns; regime window is n_pk / feature only."""
    s, cfg0 = _base("pa_climax_reversal")
    k0 = s.context_key(cfg0)
    cfg1 = apply_overrides(deepcopy(cfg0), {"features.pa_regime_window": 14})
    assert s.context_key(cfg1) == k0
    assert s.normalized_param_key(cfg1) != s.normalized_param_key(cfg0)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signal.trading_range_score_min", 0.01),
        ("signal.confirm_mode", "bull_reversal_only"),
    ],
)
def test_pa_trading_range_bls_hs_thresholds_not_in_context_key(
    field: str, value: object
) -> None:
    _assert_ctx_stable_npk_changes("pa_trading_range_bls_hs", {field: value})


def test_pa_trading_range_bls_hs_shape_fields_in_context_key() -> None:
    _assert_ctx_changes(
        "pa_trading_range_bls_hs", {"features.pa_range_window": 30}
    )
    _assert_ctx_changes(
        "pa_trading_range_bls_hs", {"features.pa_regime_window": 20}
    )
    _assert_ctx_changes(
        "pa_trading_range_bls_hs", {"signal.atr_column": "atr_like_14"}
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signal.require_tr_regime", True),
        ("signal.tr_regime_max", 0.11),
    ],
)
def test_pa_failed_trap_filters_not_in_context_key(field: str, value: object) -> None:
    _assert_ctx_stable_npk_changes("pa_failed_range_breakout_trap", {field: value})


def test_pa_failed_trap_fail_window_bars_unused_for_signals() -> None:
    """fail_window_bars is validated but not referenced in generate_signal_arrays_from_context (stale)."""
    s, cfg0 = _base("pa_failed_range_breakout_trap")
    k0 = s.context_key(cfg0)
    cfg1 = apply_overrides(deepcopy(cfg0), {"signal.fail_window_bars": 9})
    assert s.context_key(cfg1) == k0
    assert s.normalized_param_key(cfg1) != s.normalized_param_key(cfg0)


def test_pa_failed_trap_range_atr_in_context_key() -> None:
    _assert_ctx_changes(
        "pa_failed_range_breakout_trap", {"features.pa_range_window": 30}
    )
    _assert_ctx_changes(
        "pa_failed_range_breakout_trap", {"signal.atr_column": "atr_like_14"}
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signal.tight_bull_score_min", 0.01),
        ("signal.require_vwap_side", True),
    ],
)
def test_pa_tight_channel_thresholds_not_in_context_key(
    field: str, value: object
) -> None:
    _assert_ctx_stable_npk_changes("pa_tight_channel_pullback", {field: value})


def test_pa_tight_channel_regime_window_atr_in_context_key() -> None:
    _assert_ctx_changes(
        "pa_tight_channel_pullback", {"features.pa_regime_window": 20}
    )
    _assert_ctx_changes(
        "pa_tight_channel_pullback", {"signal.atr_column": "atr_like_14"}
    )


def test_pa_mtr_bear_min_not_in_context_key() -> None:
    _assert_ctx_stable_npk_changes(
        "pa_mtr_reversal", {"signal.bear_channel_score_min": 0.01}
    )


def test_pa_mtr_range_atr_in_context_key() -> None:
    _assert_ctx_changes("pa_mtr_reversal", {"features.pa_range_window": 30})
    _assert_ctx_changes("pa_mtr_reversal", {"signal.atr_column": "atr_like_14"})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signal.broad_bull_score_min", 0.01),
        ("signal.require_vwap_context", True),
        ("signal.block_climax", False),
    ],
)
def test_pa_broad_channel_thresholds_not_in_context_key(
    field: str, value: object
) -> None:
    _assert_ctx_stable_npk_changes("pa_broad_channel_zone", {field: value})


def test_pa_broad_channel_pa_regime_not_in_prepare() -> None:
    s, cfg0 = _base("pa_broad_channel_zone")
    k0 = s.context_key(cfg0)
    cfg1 = apply_overrides(deepcopy(cfg0), {"features.pa_regime_window": 14})
    assert s.context_key(cfg1) == k0
    assert s.normalized_param_key(cfg1) != s.normalized_param_key(cfg0)


def test_pa_broad_channel_range_atr_in_context_key() -> None:
    _assert_ctx_changes("pa_broad_channel_zone", {"features.pa_range_window": 30})
    _assert_ctx_changes(
        "pa_broad_channel_zone", {"signal.atr_column": "atr_like_14"}
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signal.context_score_min", 0.01),
        ("signal.require_trend_context", False),
    ],
)
def test_pa_second_entry_thresholds_not_in_context_key(
    field: str, value: object
) -> None:
    _assert_ctx_stable_npk_changes("pa_second_entry_pullback", {field: value})


def test_pa_second_entry_pa_regime_not_in_prepare() -> None:
    s, cfg0 = _base("pa_second_entry_pullback")
    k0 = s.context_key(cfg0)
    cfg1 = apply_overrides(deepcopy(cfg0), {"features.pa_regime_window": 14})
    assert s.context_key(cfg1) == k0
    assert s.normalized_param_key(cfg1) != s.normalized_param_key(cfg0)


def test_pa_second_entry_range_atr_in_context_key() -> None:
    _assert_ctx_changes(
        "pa_second_entry_pullback", {"features.pa_range_window": 30}
    )
    _assert_ctx_changes(
        "pa_second_entry_pullback", {"signal.atr_column": "atr_like_14"}
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signal.min_wedge_pushes", 5.0),
        ("signal.bear_context_min", 0.99),
    ],
)
def test_pa_wedge_thresholds_not_in_context_key(field: str, value: object) -> None:
    _assert_ctx_stable_npk_changes("pa_wedge_reversal", {field: value})


def test_pa_wedge_pa_regime_not_in_prepare() -> None:
    s, cfg0 = _base("pa_wedge_reversal")
    k0 = s.context_key(cfg0)
    cfg1 = apply_overrides(deepcopy(cfg0), {"features.pa_regime_window": 14})
    assert s.context_key(cfg1) == k0
    assert s.normalized_param_key(cfg1) != s.normalized_param_key(cfg0)


def test_pa_wedge_range_atr_in_context_key() -> None:
    _assert_ctx_changes("pa_wedge_reversal", {"features.pa_range_window": 30})
    _assert_ctx_changes("pa_wedge_reversal", {"signal.atr_column": "atr_like_14"})


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("signal.recent_breakout_lookback", 12),
        ("signal.pullback_test_atr", 0.05),
    ],
)
def test_pa_generic_breakout_scan_thresholds_not_in_context_key(
    field: str, value: object
) -> None:
    _assert_ctx_stable_npk_changes("pa_generic_breakout_pullback", {field: value})


def test_pa_generic_overlap_regime_range_atr_in_context_key() -> None:
    _assert_ctx_changes(
        "pa_generic_breakout_pullback", {"features.pa_range_window": 30}
    )
    _assert_ctx_changes(
        "pa_generic_breakout_pullback", {"features.pa_regime_window": 20}
    )
    _assert_ctx_changes(
        "pa_generic_breakout_pullback", {"signal.atr_column": "atr_like_14"}
    )
