"""Synthetic frames, combo application, and reference-engine sweep loops."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from src.backtest.backtest_config import BacktestConfig, _bt_cfg_from_dict
from src.backtest.engine import run_strategy_backtest
from src.backtest.signal_adapter import assert_canonical_signal_frame
from src.backtest.config import (
    finalize_backtest_config,
    grid_combos_from_document,
    load_grid_document,
    merge_strategy_config,
)
from src.backtest.strategy_runner import (
    STANDARD_SIGNAL_CONTRACT_VERSION,
    FeatureFrameCache,
    feature_config_fingerprint,
    run_strategy_pipeline,
)
from src.backtest.sweep_grid import config_hash, expand_param_grid
from src.backtest.sweep_types import ENGINE_LABEL, SYNTHETIC_SIGNAL_ROW, SweepResult, SweepRunConfig
from src.data.read_bars import read_bars
from src.execution.policy import default_intraday_policy
from src.execution.types import ExecutionPolicy
from src.strategies.loader import apply_overrides


def _semantics_version(policy: ExecutionPolicy | None) -> str:
    pol = policy or default_intraday_policy()
    return str(pol.semantics_version)


def synthetic_ohlcv_and_signals(*, target_r: float) -> pd.DataFrame:
    n = 12
    rng = pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC")
    ny = pd.date_range("2024-01-02 09:30", periods=n, freq="min")
    minute = np.arange(n, dtype=np.int32)
    o = np.linspace(100.0, 101.0, n)
    df = pd.DataFrame(
        {
            "session_date": ["2024-01-02"] * n,
            "ts_utc": rng,
            "ts_ny": ny,
            "minute_from_open": minute,
            "open": o,
            "high": o + 0.5,
            "low": o - 0.5,
            "close": o + 0.1,
            "sig_strategy": ["synthetic_smoke"] * n,
            "sig_side": [0] * n,
            "sig_entry_ref": [pd.NA] * n,
            "sig_stop": [float("nan")] * n,
            "sig_target": [float("nan")] * n,
            "sig_target_mode": [""] * n,
            "sig_target_r": [float("nan")] * n,
            "sig_risk_per_share": [float("nan")] * n,
            "sig_reason": [""] * n,
            "sig_valid": [False] * n,
        }
    )
    i = SYNTHETIC_SIGNAL_ROW
    df.loc[i, "sig_valid"] = True
    df.loc[i, "sig_side"] = 1
    df.loc[i, "sig_stop"] = 99.0
    df.loc[i, "sig_target_mode"] = "fixed_r"
    df.loc[i, "sig_target_r"] = float(target_r)
    df.loc[i, "sig_target"] = float("nan")
    df.loc[i, "sig_risk_per_share"] = 1.0
    return df


def apply_combo_to_signal_row(
    df: pd.DataFrame,
    combo: Mapping[str, Any],
    *,
    signal_row_index: int = SYNTHETIC_SIGNAL_ROW,
) -> pd.DataFrame:
    out = df.copy()
    for k, v in combo.items():
        if not isinstance(k, str) or not k.startswith("sig_"):
            continue
        if k not in out.columns:
            continue
        out.loc[out.index[signal_row_index], k] = v
    return out


def run_single_combo(
    base_df: pd.DataFrame,
    combo: Mapping[str, Any],
    *,
    combo_id: str,
    strategy: str,
    sweep_cfg: SweepRunConfig,
    signal_row_index: int = SYNTHETIC_SIGNAL_ROW,
) -> SweepResult:
    df = apply_combo_to_signal_row(base_df, combo, signal_row_index=signal_row_index)
    assert_canonical_signal_frame(df)
    bt = sweep_cfg.backtest or BacktestConfig()
    pol = sweep_cfg.policy or default_intraday_policy(
        slippage_per_share=bt.slippage_per_share,
        commission_per_trade=bt.commission_per_trade,
        eod_exit_minute=bt.eod_exit_minute,
    )
    tdf, summ = run_strategy_backtest(df, config=bt, policy=pol, exit_plan=None)
    h = config_hash({"combo": dict(combo), "strategy": strategy})
    sem = _semantics_version(pol)
    tg = float(summ.get("total_gross_r", float("nan")))
    if tg != tg:
        tg = float("nan")
    pfr = float(summ.get("profit_factor_r", float("nan")))
    if pfr != pfr:
        pfr = float("nan")
    return SweepResult(
        combo_id=combo_id,
        strategy=strategy,
        config_hash=h,
        trade_count=int(summ.get("trades", 0)),
        total_r=float(summ.get("total_r", 0.0)),
        total_net_pnl=float(summ.get("total_net_pnl", 0.0)),
        total_gross_r=tg,
        max_drawdown_r=float(summ.get("max_drawdown_r", 0.0)),
        avg_r=float(summ.get("avg_r", 0.0)),
        win_rate=float(summ.get("win_rate", 0.0)),
        profit_factor_r=pfr,
        execution_semantics_version=sem,
        engine=ENGINE_LABEL,
        result_lineage="mainline",
        symbol=sweep_cfg.symbol,
        start=sweep_cfg.start,
        end=sweep_cfg.end,
        params_json=json.dumps(dict(combo), sort_keys=True, default=str),
        notes="synthetic_smoke" if strategy == "synthetic_smoke" else "",
        asset=str(sweep_cfg.asset or "equity"),
        data_source="synthetic_builtin",
        feature_config_hash="",
        signal_contract_version=STANDARD_SIGNAL_CONTRACT_VERSION,
    )


def run_single_combo_from_signals(
    signal_df: pd.DataFrame,
    *,
    combo_id: str,
    combo_params: Mapping[str, Any],
    strategy: str,
    sweep_cfg: SweepRunConfig,
    asset: str,
    data_source: str,
    feature_config_hash: str,
    signal_contract_version: str,
    dry_run: bool = False,
    strategy_cfg: Mapping[str, Any] | None = None,
) -> SweepResult:
    assert_canonical_signal_frame(signal_df)
    bt = sweep_cfg.backtest or _bt_cfg_from_dict(dict(strategy_cfg) if strategy_cfg is not None else None)
    pol = sweep_cfg.policy or default_intraday_policy(
        slippage_per_share=bt.slippage_per_share,
        commission_per_trade=bt.commission_per_trade,
        eod_exit_minute=bt.eod_exit_minute,
    )
    sem = _semantics_version(pol)
    h = config_hash({"combo": dict(combo_params), "strategy": strategy, "feature_key": feature_config_hash})
    if dry_run:
        return SweepResult(
            combo_id=combo_id,
            strategy=strategy,
            config_hash=h,
            trade_count=0,
            total_r=0.0,
            total_net_pnl=0.0,
            total_gross_r=float("nan"),
            max_drawdown_r=0.0,
            avg_r=0.0,
            win_rate=0.0,
            profit_factor_r=float("nan"),
            execution_semantics_version=sem,
            engine=ENGINE_LABEL,
            result_lineage="mainline",
            symbol=sweep_cfg.symbol,
            start=sweep_cfg.start,
            end=sweep_cfg.end,
            params_json=json.dumps(dict(combo_params), sort_keys=True, default=str),
            notes="dry_run",
            asset=asset,
            data_source=data_source,
            feature_config_hash=feature_config_hash,
            signal_contract_version=signal_contract_version,
        )
    _tdf, summ = run_strategy_backtest(signal_df, config=bt, policy=pol, exit_plan=None)
    tg = float(summ.get("total_gross_r", float("nan")))
    if tg != tg:
        tg = float("nan")
    pfr = float(summ.get("profit_factor_r", float("nan")))
    if pfr != pfr:
        pfr = float("nan")
    return SweepResult(
        combo_id=combo_id,
        strategy=strategy,
        config_hash=h,
        trade_count=int(summ.get("trades", 0)),
        total_r=float(summ.get("total_r", 0.0)),
        total_net_pnl=float(summ.get("total_net_pnl", 0.0)),
        total_gross_r=tg,
        max_drawdown_r=float(summ.get("max_drawdown_r", 0.0)),
        avg_r=float(summ.get("avg_r", 0.0)),
        win_rate=float(summ.get("win_rate", 0.0)),
        profit_factor_r=pfr,
        execution_semantics_version=sem,
        engine=ENGINE_LABEL,
        result_lineage="mainline",
        symbol=sweep_cfg.symbol,
        start=sweep_cfg.start,
        end=sweep_cfg.end,
        params_json=json.dumps(dict(combo_params), sort_keys=True, default=str),
        notes="",
        asset=asset,
        data_source=data_source,
        feature_config_hash=feature_config_hash,
        signal_contract_version=signal_contract_version,
    )


def run_real_symbol_sweep(
    *,
    strategy_name: str,
    symbol: str,
    asset: str,
    start: str,
    end: str,
    data_dir: str | Path,
    config_path: str | None,
    grid_path: str | None,
    max_combos: int | None,
    dry_run: bool,
    sweep_cfg: SweepRunConfig,
    feature_cache: Any | None = None,
) -> pd.DataFrame:
    base_cfg = merge_strategy_config(strategy_name, Path(config_path) if config_path else None, None)
    combos: list[dict[str, Any]] = [{}]
    if grid_path:
        combos = grid_combos_from_document(load_grid_document(grid_path))
    if max_combos is not None:
        combos = combos[: int(max_combos)]
    bars = read_bars(asset=asset, symbol=symbol, start=start, end=end, data_dir=data_dir)
    if bars is None or len(bars) == 0:
        raise ValueError(
            f"No bars for symbol={symbol!r} start={start!r} end={end!r} data_dir={data_dir!r}. "
            "Install IBKR parquet partitions or adjust the date window."
        )
    data_source = f"ibkr_parquet:{Path(data_dir).resolve()}"
    rows: list[dict[str, Any]] = []
    inner_cache = feature_cache if feature_cache is not None else FeatureFrameCache(bars)
    for i, combo in enumerate(combos):
        cfg = apply_overrides(base_cfg, combo)
        finalize_backtest_config(cfg)
        fch = feature_config_fingerprint(cfg)
        _, canon = inner_cache.build_signals(strategy_name, cfg, asset, symbol, start, end, data_dir)
        cid = f"combo_{i:04d}"
        sr = run_single_combo_from_signals(
            canon,
            combo_id=cid,
            combo_params=combo,
            strategy=strategy_name,
            sweep_cfg=sweep_cfg,
            asset=asset,
            data_source=data_source,
            feature_config_hash=fch,
            signal_contract_version=STANDARD_SIGNAL_CONTRACT_VERSION,
            dry_run=dry_run,
            strategy_cfg=cfg,
        )
        rows.append(sr.__dict__)
    return pd.DataFrame(rows)


def run_param_sweep(
    base_df: pd.DataFrame,
    grid: dict[str, list[Any]],
    *,
    sweep_cfg: SweepRunConfig | None = None,
    signal_row_index: int = SYNTHETIC_SIGNAL_ROW,
) -> pd.DataFrame:
    cfg = sweep_cfg or SweepRunConfig()
    combos = expand_param_grid(grid)
    if cfg.max_combos is not None:
        combos = combos[: int(cfg.max_combos)]
    rows: list[dict[str, Any]] = []
    for i, c in enumerate(combos):
        cid = f"combo_{i:04d}"
        sr = run_single_combo(
            base_df,
            c,
            combo_id=cid,
            strategy=cfg.strategy,
            sweep_cfg=cfg,
            signal_row_index=signal_row_index,
        )
        rows.append(sr.__dict__)
    return pd.DataFrame(rows)


def run_synthetic_smoke(*, sweep_cfg: SweepRunConfig | None = None) -> pd.DataFrame:
    cfg = sweep_cfg or SweepRunConfig()
    base = synthetic_ohlcv_and_signals(target_r=2.0)
    grid = {"sig_target_r": [1.0, 2.0]}
    return run_param_sweep(base, grid, sweep_cfg=cfg)
