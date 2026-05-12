"""Layer 1 parameter sweep CLI — reference execution via ``run_strategy_backtest``."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.backtest.config import validate_testing_grid_for_strategy
from src.backtest.sweep_grid import config_hash, expand_param_grid
from src.backtest.sweep_io import (
    default_run_manifest,
    git_sha,
    write_real_sweep_artifacts,
    write_smoke_artifacts,
)
from src.backtest.sweep_results import (
    apply_combo_to_signal_row,
    run_param_sweep,
    run_real_symbol_sweep,
    run_single_combo,
    run_single_combo_from_signals,
    run_synthetic_smoke,
    synthetic_ohlcv_and_signals,
)
from src.backtest.sweep_types import ENGINE_LABEL, SYNTHETIC_SIGNAL_ROW, SweepCombo, SweepResult, SweepRunConfig
from src.backtest.strategy_runner import load_strategy_config_merged, validate_canonical_pipeline
from src.execution.policy import default_intraday_policy
from src.strategies.loader import available_strategies

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
        help="Directory for sweep_results.csv, sweep_summary.md, run_manifest.json.",
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
        rep = validate_canonical_pipeline(
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
    from src.backtest.config import finalize_backtest_config

    finalize_backtest_config(cfg)


def _load_testing_yaml(path: Any, *, expected_strategy: str) -> dict[str, Any]:
    from src.backtest.config import load_testing_yaml

    return load_testing_yaml(Path(path), expected_strategy=expected_strategy)


def _metrics_row(**kwargs: Any) -> dict[str, Any]:
    from src.backtest.config import sweep_metrics_row

    return sweep_metrics_row(**kwargs)
