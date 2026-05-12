"""Layer 1 parameter sweep CLI — reference execution via ``run_strategy_backtest``."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from src.backtest.engine import BacktestConfig, _bt_cfg_from_dict, run_strategy_backtest
from src.backtest.signal_adapter import assert_canonical_signal_frame
from src.backtest.strategy_runner import (
    STANDARD_SIGNAL_CONTRACT_VERSION,
    FeatureFrameCache,
    feature_config_fingerprint,
    finalize_backtest_config,
    grid_combos_from_document,
    load_grid_document,
    load_strategy_config_merged,
    merge_strategy_config,
    validate_pipeline,
    validate_testing_grid_for_strategy,
)
from src.data.read_bars import read_bars
from src.execution.policy import default_intraday_policy
from src.execution.types import ExecutionPolicy
from src.strategies.loader import apply_overrides, available_strategies

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENGINE_LABEL = "reference"
SYNTHETIC_SIGNAL_ROW = 3

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SweepCombo:
    combo_id: str
    params: dict[str, Any]


@dataclass
class SweepResult:
    combo_id: str
    strategy: str
    config_hash: str
    trade_count: int
    total_r: float
    total_net_pnl: float
    total_gross_r: float
    max_drawdown_r: float
    avg_r: float
    win_rate: float
    profit_factor_r: float
    execution_semantics_version: str
    engine: str
    result_lineage: str
    symbol: str = ""
    start: str = ""
    end: str = ""
    params_json: str = ""
    notes: str = ""
    asset: str = "equity"
    data_source: str = ""
    feature_config_hash: str = ""
    signal_contract_version: str = ""


@dataclass
class SweepRunConfig:
    strategy: str = "synthetic_smoke"
    symbol: str = "SYNTH"
    start: str = "2024-01-02"
    end: str = "2024-01-02"
    data_root: str = ""
    output_root: Any = None  # Path | None
    max_combos: int | None = None
    no_save: bool = True
    backtest: BacktestConfig | None = None
    policy: ExecutionPolicy | None = None
    asset: str = "equity"


# ---------------------------------------------------------------------------
# Grid / config hashing
# ---------------------------------------------------------------------------


def expand_param_grid(grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    if not grid:
        return [{}]
    keys = list(grid.keys())
    vals: list[list[Any]] = []
    for k in keys:
        v = grid[k]
        if isinstance(v, (list, tuple)):
            vals.append(list(v))
        else:
            vals.append([v])
    return [dict(zip(keys, combo)) for combo in itertools.product(*vals)]


def config_hash(config: Mapping[str, Any]) -> str:
    blob = json.dumps(config, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:20]


# ---------------------------------------------------------------------------
# Artifact I/O
# ---------------------------------------------------------------------------


def git_sha() -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, timeout=5)
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def write_real_sweep_artifacts(df: pd.DataFrame, out_dir: Path, manifest: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "sweep_results.csv", index=False)
    (out_dir / "sweep_meta.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    lines = [
        "# Sweep summary",
        "",
        f"- engine: `{manifest.get('engine', '')}`",
        f"- execution_semantics_version: `{manifest.get('execution_semantics_version', '')}`",
        f"- strategy: `{manifest.get('strategy', '')}`",
        f"- symbol: `{manifest.get('symbols', '')}`",
        f"- window: `{manifest.get('start', '')}` … `{manifest.get('end', '')}`",
        f"- combos: {len(df)}",
        "",
        "Per-combo metrics are in `sweep_results.csv`.",
    ]
    (out_dir / "sweep_summary.md").write_text("\n".join(lines), encoding="utf-8")


def write_smoke_artifacts(df: pd.DataFrame, out_dir: Path, *, execution_semantics_version: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "sweep_smoke.csv", index=False)
    meta = {
        "engine": ENGINE_LABEL,
        "result_lineage": "mainline",
        "execution_semantics_version": execution_semantics_version,
    }
    (out_dir / "sweep_meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")


def default_run_manifest(
    *,
    pol_semantics: str,
    args: Any,
    no_save: bool,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "git_sha": "",
        "command": " ".join(sys.argv),
        "timestamp": "",
        "engine": ENGINE_LABEL,
        "execution_semantics_version": str(pol_semantics),
        "symbols": getattr(args, "symbol", ""),
        "strategy": getattr(args, "strategy", ""),
        "start": getattr(args, "start", ""),
        "end": getattr(args, "end", ""),
        "config_path": getattr(args, "config", "") or "",
        "grid_path": getattr(args, "grid", "") or "",
        "no_save": bool(no_save),
        "dry_run": bool(dry_run),
        "result_lineage": "mainline",
        "asset": getattr(args, "asset", "equity"),
        "data_root": getattr(args, "data_root", "") or "",
    }


# ---------------------------------------------------------------------------
# Synthetic + sweep execution
# ---------------------------------------------------------------------------


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
        min_risk_per_share=bt.min_risk_per_share,
    )
    _tdf, summ = run_strategy_backtest(df, config=bt, policy=pol, exit_plan=None)
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
        min_risk_per_share=bt.min_risk_per_share,
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

__all__ = [
    "ENGINE_LABEL",
    "SYNTHETIC_SIGNAL_ROW",
    "SweepCombo",
    "SweepResult",
    "SweepRunConfig",
    "apply_combo_to_signal_row",
    "config_hash",
    "expand_param_grid",
    "git_sha",
    "run_param_sweep",
    "run_real_symbol_sweep",
    "run_single_combo",
    "run_single_combo_from_signals",
    "run_synthetic_smoke",
    "synthetic_ohlcv_and_signals",
    "validate_testing_grid_for_strategy",
    "main",
]


def sweep_main(argv: list[str] | None) -> int:
    p = argparse.ArgumentParser(
        description=(
            "Layer 1 sweep: reference engine via run_strategy_backtest → simulate_trade_path."
        )
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help="Run deterministic synthetic sweep (no QQQ / no parquet).",
    )
    p.add_argument(
        "--validate-pipeline",
        action="store_true",
        help="Validate strategy + optional bars/features/signals (no backtest accounting).",
    )
    p.add_argument("--strategy", default="synthetic_smoke", help="Strategy id (registered name for real runs).")
    p.add_argument("--symbol", default="SYNTH", help="Symbol (e.g. QQQ) for real runs.")
    p.add_argument("--asset", default="equity", choices=("equity", "futures"), help="Asset class for read_bars.")
    p.add_argument("--start", default="2024-01-02", help="Start date (NY calendar day) YYYY-MM-DD.")
    p.add_argument("--end", default="2024-01-02", help="End date (NY calendar day, inclusive) YYYY-MM-DD.")
    p.add_argument("--config", default="", help="Base strategy YAML/JSON (default: parameters/<strategy>.yaml).")
    p.add_argument(
        "--grid",
        default="",
        help="Grid YAML/JSON: either {grid: {dotted.path: [values]}} or top-level dict of lists.",
    )
    p.add_argument(
        "--data-root",
        default="",
        help="Directory for IBKR parquet tree (e.g. data/raw/ibkr). Required for real-symbol runs.",
    )
    p.add_argument(
        "--output-root",
        type=str,
        default=None,
        help="Directory for sweep_results.csv, sweep_summary.md, sweep_meta.json.",
    )
    p.add_argument("--max-combos", type=int, default=None)
    p.add_argument("--no-save", action="store_true", help="Skip writing files even if --output-root set.")
    p.add_argument("--dry-run", action="store_true", help="Real-symbol sweep: build signals but skip backtest accounting.")
    p.add_argument(
        "--pipeline-help",
        action="store_true",
        help="Print reference pipeline description.",
    )
    args = p.parse_args(argv)

    want_real = bool(
        args.strategy
        and args.strategy != "synthetic_smoke"
        and args.symbol
        and args.symbol != "SYNTH"
        and args.start
        and args.end
        and args.data_root
    )
    if args.data_root and not args.smoke and not args.validate_pipeline and not want_real:
        print(
            "ERROR: --data-root is only used for full real-symbol sweeps "
            "(need --strategy, --symbol, --start, --end, and --data-root together), "
            "or use --smoke / --validate-pipeline.",
            file=sys.stderr,
        )
        return 3

    if args.pipeline_help:
        print(
            "Reference sweep: read_bars → build_features_from_config → generate_signals → "
            "sig_* → run_strategy_backtest → simulate_trade_path → summarize_trades. "
            "Use --smoke for synthetic regression; --validate-pipeline to check wiring."
        )
        return 0

    if args.smoke:
        cfg = SweepRunConfig(
            strategy=args.strategy,
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            data_root=args.data_root,
            output_root=Path(args.output_root) if args.output_root else None,
            max_combos=args.max_combos,
            no_save=bool(args.no_save),
            asset=args.asset,
        )
        df = run_synthetic_smoke(sweep_cfg=cfg)
        print(f"engine={ENGINE_LABEL}", flush=True)
        print("result_lineage=mainline", flush=True)
        print(df.to_string(index=False), flush=True)
        if cfg.output_root is not None and not cfg.no_save:
            sem = str(df["execution_semantics_version"].iloc[0]) if len(df) else ""
            write_smoke_artifacts(df, cfg.output_root, execution_semantics_version=sem)
            print(f"Wrote: {cfg.output_root.resolve()}", flush=True)
        return 0

    if args.validate_pipeline:
        names = set(available_strategies())
        if args.strategy not in names:
            print(
                f"ERROR: --validate-pipeline requires a registered --strategy (got {args.strategy!r}).",
                file=sys.stderr,
            )
            return 2
        cfg0 = load_strategy_config_merged(
            args.strategy,
            Path(args.config) if args.config else None,
            None,
        )
        with_data = bool(args.symbol and args.symbol != "SYNTH" and args.start and args.end)
        data_dir = args.data_root or "data/raw/ibkr"
        rep = validate_pipeline(
            strategy_name=args.strategy,
            cfg=cfg0,
            asset=args.asset,
            symbol=args.symbol if args.symbol != "SYNTH" else "",
            start=args.start,
            end=args.end,
            data_dir=data_dir,
            with_data=with_data,
        )
        print(json.dumps(rep, indent=2, sort_keys=True, default=str), flush=True)
        if rep.get("blockers"):
            return 1
        return 0

    if want_real:
        if args.strategy not in set(available_strategies()):
            print(f"ERROR: unknown strategy {args.strategy!r}", file=sys.stderr)
            return 2
        sweep_cfg = SweepRunConfig(
            strategy=args.strategy,
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            data_root=args.data_root,
            output_root=Path(args.output_root) if args.output_root else None,
            max_combos=args.max_combos,
            no_save=bool(args.no_save),
            asset=args.asset,
        )
        try:
            df = run_real_symbol_sweep(
                strategy_name=args.strategy,
                symbol=args.symbol,
                asset=args.asset,
                start=args.start,
                end=args.end,
                data_dir=args.data_root,
                config_path=args.config or None,
                grid_path=args.grid or None,
                max_combos=args.max_combos,
                dry_run=bool(args.dry_run),
                sweep_cfg=sweep_cfg,
            )
        except (FileNotFoundError, ValueError, OSError, KeyError, TypeError) as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 4
        print(f"engine={ENGINE_LABEL}", flush=True)
        print("result_lineage=mainline", flush=True)
        print(df.to_string(index=False), flush=True)
        if args.output_root and not args.no_save:
            pol = default_intraday_policy()
            manifest = default_run_manifest(
                pol_semantics=str(pol.semantics_version),
                args=args,
                no_save=bool(args.no_save),
                dry_run=bool(args.dry_run),
            )
            manifest["git_sha"] = git_sha()
            manifest["timestamp"] = datetime.now(timezone.utc).isoformat()
            write_real_sweep_artifacts(df, Path(args.output_root), manifest)
            print(f"Wrote: {Path(args.output_root).resolve()}", flush=True)
        return 0

    p.print_help(sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    return sweep_main(list(sys.argv[1:] if argv is None else argv))


def _finalize_combo_config(cfg: dict[str, Any]) -> None:
    finalize_backtest_config(cfg)


def _load_testing_yaml(path: Any, *, expected_strategy: str) -> dict[str, Any]:
    from src.backtest.strategy_runner import load_testing_yaml

    return load_testing_yaml(Path(path), expected_strategy=expected_strategy)


def _metrics_row(**kwargs: Any) -> dict[str, Any]:
    from src.backtest.strategy_runner import sweep_metrics_row

    return sweep_metrics_row(**kwargs)


if __name__ == "__main__":
    import sys

    raise SystemExit(main())
