"""Layer1 testing YAML fixed+grid merge and backtest execution policy mapping."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from src.backtest.engine import BacktestConfig, _bt_cfg_from_dict
from src.backtest.strategy_runner import (
    grid_combos_from_document,
    normalize_override_mapping,
    validate_testing_grid_for_strategy,
)
from src.combiner.candidate import load_candidate_yaml, load_candidates
from src.execution.policy import default_intraday_policy


def test_normalize_override_nested_and_dotted_leaf():
    doc = {"risk": {"min_risk_per_share": 0.03}, "signal.entry_start_minute": 60}
    assert normalize_override_mapping(doc) == {
        "risk.min_risk_per_share": 0.03,
        "signal.entry_start_minute": 60,
    }


def test_normalize_override_list_stays_leaf():
    out = normalize_override_mapping({"signal.side": ["long_only", "short_only"]})
    assert out["signal.side"] == ["long_only", "short_only"]


def test_grid_combos_fixed_only_returns_one_row():
    doc = {
        "strategy": "pa_buy_sell_close_trend",
        "fixed": {"risk.target_mode": "fixed_r", "risk.min_risk_per_share": 0.03},
    }
    combos = grid_combos_from_document(doc)
    assert len(combos) == 1
    assert combos[0]["risk.min_risk_per_share"] == 0.03
    assert combos[0]["risk.target_mode"] == "fixed_r"


def test_grid_combos_fixed_plus_grid_merges_and_disjoint():
    doc = {
        "strategy": "pa_buy_sell_close_trend",
        "fixed": {"risk.target_mode": "fixed_r", "risk.min_risk_per_share": 0.03},
        "grid": {"risk.target_r": [1.0, 1.5], "signal.entry_start_minute": [60, 90]},
    }
    combos = grid_combos_from_document(doc)
    assert len(combos) == 4
    for c in combos:
        assert c["risk.target_mode"] == "fixed_r"
        assert c["risk.min_risk_per_share"] == 0.03
        assert "risk.target_r" in c
        assert "signal.entry_start_minute" in c


def test_grid_combos_fixed_grid_overlap_raises():
    doc = {
        "strategy": "pa_buy_sell_close_trend",
        "fixed": {"risk.target_r": 1.0},
        "grid": {"risk.target_r": [1.5, 2.0]},
    }
    with pytest.raises(ValueError, match="fixed` and `grid` both set"):
        grid_combos_from_document(doc)


def test_validate_testing_grid_uses_same_combos_as_runtime():
    # Smoke: real strategy document validates without drift vs old apply order.
    p = Path("src/strategies/testing_parameters/cci_extreme_snapback_focused.yaml")
    raw = yaml.safe_load(p.read_text(encoding="utf-8"))
    validate_testing_grid_for_strategy("cci_extreme_snapback", raw)


def test_bt_cfg_min_risk_from_risk_section():
    cfg = _bt_cfg_from_dict({"risk": {"min_risk_per_share": 0.03}})
    assert cfg.min_risk_per_share == pytest.approx(0.03)


def test_bt_cfg_min_risk_negative_raises():
    with pytest.raises(ValueError, match="min_risk_per_share"):
        _bt_cfg_from_dict({"risk": {"min_risk_per_share": -0.01}})


def test_bt_cfg_max_trades_alias_precedence():
    cfg = _bt_cfg_from_dict(
        {
            "backtest": {"max_trades_per_session": 2},
            "risk": {"max_trades_per_day": 5},
        }
    )
    assert cfg.max_trades_per_session == 2

    cfg2 = _bt_cfg_from_dict({"risk": {"max_trades_per_day": 3}})
    assert cfg2.max_trades_per_session == 3


def test_default_intraday_policy_threads_min_risk_from_backtest_config():
    bt = BacktestConfig(min_risk_per_share=0.5)
    pol = default_intraday_policy(
        slippage_per_share=bt.slippage_per_share,
        commission_per_trade=bt.commission_per_trade,
        eod_exit_minute=bt.eod_exit_minute,
        min_risk_per_share=bt.min_risk_per_share,
    )
    assert pol.min_risk_per_share == pytest.approx(0.5)


def test_run_strategy_backtest_threads_min_risk_into_default_policy(monkeypatch):
    captured: dict[str, Any] = {}

    def capture_policy(**kwargs):
        captured.update(kwargs)
        from src.execution.policy import default_intraday_policy as real

        return real(**kwargs)

    import src.backtest.engine as eng

    monkeypatch.setattr(eng, "default_intraday_policy", capture_policy)
    monkeypatch.setattr(eng, "simulate_trade_path", lambda *a, **k: __import__(
        "src.execution.types", fromlist=["TradeResult"]
    ).TradeResult(ok=False, reject_reason="x"))

    import pandas as pd

    n = 5
    df = pd.DataFrame(
        {
            "session_date": ["2024-01-02"] * n,
            "ts_utc": pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC"),
            "ts_ny": pd.date_range("2024-01-02 09:30", periods=n, freq="min"),
            "minute_from_open": list(range(n)),
            "open": [100.0] * n,
            "high": [101.0] * n,
            "low": [99.0] * n,
            "close": [100.5] * n,
            "sig_valid": [False] * n,
            "sig_side": [1] * n,
            "sig_entry_ref": [100.0] * n,
            "sig_stop": [99.0] * n,
            "sig_target": [102.0] * n,
            "sig_target_mode": ["fixed_r"] * n,
            "sig_target_r": [1.0] * n,
            "sig_risk_per_share": [1.0] * n,
            "sig_reason": [""] * n,
            "sig_strategy": ["t"] * n,
        }
    )
    strat_cfg = {"risk": {"min_risk_per_share": 0.07}}
    eng.run_strategy_backtest(df, config=eng._bt_cfg_from_dict(strat_cfg))
    assert captured.get("min_risk_per_share") == pytest.approx(0.07)


def test_promotion_writes_combiner_compatible_yaml(tmp_path):
    from src.research import run_layer1_execution_backed_controlled as prom

    runs = tmp_path / "runs" / "pa_test"
    runs.mkdir(parents=True)
    meta = {
        "strategy": "pa_buy_sell_close_trend",
        "config_path": "",
        "grid_path": "src/strategies/testing_parameters/pa_buy_sell_close_trend_focused.yaml",
        "start": "2024-01-01",
        "end": "2024-01-05",
        "data_root": "data/raw/ibkr",
        "asset": "equity",
        "symbol": "QQQ",
    }
    (runs / "sweep_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    rows = [
        {
            "combo_id": "combo_0000",
            "strategy": "pa_buy_sell_close_trend",
            "trade_count": 25,
            "total_r": 2.5,
            "profit_factor_r": 1.2,
            "max_drawdown_r": -1.0,
            "params_json": json.dumps({"risk.target_r": 1.0, "signal.entry_start_minute": 60}),
            "config_hash": "abc",
            "feature_config_hash": "f1",
            "execution_semantics_version": "1.0",
            "signal_contract_version": "standard_sig_v1",
        }
    ]
    import pandas as pd

    pd.DataFrame(rows).to_csv(runs / "sweep_results.csv", index=False)

    out_root = tmp_path / "candidates"
    out_root.mkdir()
    (out_root / "README.md").write_text("# temp\n", encoding="utf-8")

    prom.run_promote(
        runs_root=tmp_path / "runs",
        candidate_root=out_root,
        max_per_strategy=3,
        min_trades=20,
        min_profit_factor_r=1.05,
        min_total_r=0.0,
        gate_label="TEST_GATE",
        dry_run=False,
    )
    yamls = sorted(out_root.glob("*.yaml"))
    assert len(yamls) == 1
    c = load_candidate_yaml(yamls[0])
    assert c.strategy == "pa_buy_sell_close_trend"
    assert "features" in c.config and "signal" in c.config
    raw = yaml.safe_load(yamls[0].read_text(encoding="utf-8"))
    assert raw.get("execution", {}).get("execution_engine") == "execution_backed"
    load_candidates(out_root)


def test_validate_candidates_allow_empty(tmp_path):
    from src.research.run_layer1_execution_backed_controlled import run_validate_candidates

    p = tmp_path / "empty"
    p.mkdir()
    (p / "README.md").write_text("x", encoding="utf-8")
    run_validate_candidates(p, allow_empty=True)


def test_validate_candidates_fails_on_bad_yaml(tmp_path):
    from src.research.run_layer1_execution_backed_controlled import run_validate_candidates

    p = tmp_path / "bad"
    p.mkdir()
    (p / "bad.yaml").write_text("candidate_id: ONLY_ID\nfoo: 1\n", encoding="utf-8")
    with pytest.raises((ValueError, KeyError)):
        run_validate_candidates(p, allow_empty=False)
