"""Layer 1 parameter sweep — **canonical reference engine** + explicit ``--legacy``.

**Canonical path:** expand grid → build / map ``sig_*`` frame →
:func:`src.backtest.engine.run_strategy_backtest` →
``src.execution.path.simulate_trade_path`` → :func:`src.backtest.metrics.summarize_trades`.

**Legacy path:** ``python -m src.backtest.sweep --legacy ...`` delegates to
``src.backtest.legacy.sweep_legacy`` (``engine=legacy_numba_fast``). Do not mix
R/PnL with canonical outputs without labeling (see ``docs/LEGACY_RESULTS_POLICY.md``).

CLI:

- ``--smoke`` — deterministic synthetic canonical sweep (no disk I/O unless ``--output-root``).
- ``--legacy`` must be the **first** argv token to run the Numba grid unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd

from src.backtest.legacy.engine_legacy import BacktestConfig
from src.backtest.engine import run_strategy_backtest
from src.backtest.signal_adapter import assert_canonical_signal_frame
from src.execution.policy import default_intraday_policy
from src.execution.types import ExecutionPolicy

SYNTHETIC_SIGNAL_ROW = 3
CANONICAL_ENGINE_LABEL = "canonical_reference"


@dataclass(frozen=True)
class SweepCombo:
    """One flattened parameter dict (e.g. ``sig_target_r`` overrides)."""

    combo_id: str
    params: dict[str, Any]


@dataclass
class SweepResult:
    """One row of canonical sweep output (also representable as ``dict``)."""

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
    canonical_or_legacy: str
    symbol: str = ""
    start: str = ""
    end: str = ""
    params_json: str = ""
    notes: str = ""


@dataclass
class CanonicalSweepConfig:
    """Knobs for :func:`run_canonical_sweep` (synthetic or future real-data runs)."""

    strategy: str = "synthetic_smoke"
    symbol: str = "SYNTH"
    start: str = "2024-01-02"
    end: str = "2024-01-02"
    data_root: str = ""
    output_root: Path | None = None
    max_combos: int | None = None
    no_save: bool = True
    backtest: BacktestConfig | None = None
    policy: ExecutionPolicy | None = None


def expand_param_grid(grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    """Cartesian product of lists (same shape as ``expand_grid({"grid": ...})``)."""
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
    """Stable short hash for a config mapping (order-independent keys)."""
    blob = json.dumps(config, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:20]


def _semantics_version(policy: ExecutionPolicy | None) -> str:
    pol = policy or default_intraday_policy()
    return str(pol.semantics_version)


def _synthetic_ohlcv_and_signals(*, target_r: float) -> pd.DataFrame:
    """Tiny single-session frame with one valid long signal (canonical ``sig_*``)."""
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
    """Apply ``sig_*`` scalar overrides on the signal row only."""
    out = df.copy()
    for k, v in combo.items():
        if not isinstance(k, str) or not k.startswith("sig_"):
            continue
        if k not in out.columns:
            continue
        out.loc[out.index[signal_row_index], k] = v
    return out


def run_single_canonical_combo(
    base_df: pd.DataFrame,
    combo: Mapping[str, Any],
    *,
    combo_id: str,
    strategy: str,
    sweep_cfg: CanonicalSweepConfig,
    signal_row_index: int = SYNTHETIC_SIGNAL_ROW,
) -> SweepResult:
    """Run :func:`run_strategy_backtest` for one parameter combo (canonical engine)."""
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
    if tg != tg:  # NaN
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
        engine=CANONICAL_ENGINE_LABEL,
        canonical_or_legacy="canonical",
        symbol=sweep_cfg.symbol,
        start=sweep_cfg.start,
        end=sweep_cfg.end,
        params_json=json.dumps(dict(combo), sort_keys=True, default=str),
        notes="synthetic_smoke" if strategy == "synthetic_smoke" else "",
    )


def run_canonical_sweep(
    base_df: pd.DataFrame,
    grid: dict[str, list[Any]],
    *,
    sweep_cfg: CanonicalSweepConfig | None = None,
    signal_row_index: int = SYNTHETIC_SIGNAL_ROW,
) -> pd.DataFrame:
    """Run ``run_strategy_backtest`` for each flattened combo in ``grid``."""
    cfg = sweep_cfg or CanonicalSweepConfig()
    combos = expand_param_grid(grid)
    if cfg.max_combos is not None:
        combos = combos[: int(cfg.max_combos)]
    rows: list[dict[str, Any]] = []
    for i, c in enumerate(combos):
        cid = f"combo_{i:04d}"
        sr = run_single_canonical_combo(
            base_df,
            c,
            combo_id=cid,
            strategy=cfg.strategy,
            sweep_cfg=cfg,
            signal_row_index=signal_row_index,
        )
        rows.append(sr.__dict__)
    return pd.DataFrame(rows)


def run_synthetic_canonical_smoke(
    *,
    sweep_cfg: CanonicalSweepConfig | None = None,
) -> pd.DataFrame:
    """Two-combo synthetic sweep over ``sig_target_r`` (no external data)."""
    cfg = sweep_cfg or CanonicalSweepConfig()
    base = _synthetic_ohlcv_and_signals(target_r=2.0)
    grid = {"sig_target_r": [1.0, 2.0]}
    return run_canonical_sweep(base, grid, sweep_cfg=cfg)


def _write_tiny_results(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "canonical_sweep_smoke.csv"
    df.to_csv(p, index=False)
    meta = {
        "engine": CANONICAL_ENGINE_LABEL,
        "canonical_or_legacy": "canonical",
        "execution_semantics_version": str(df["execution_semantics_version"].iloc[0])
        if len(df)
        else "",
    }
    (out_dir / "canonical_sweep_meta.json").write_text(
        json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8"
    )


def canonical_sweep_main(argv: list[str] | None) -> int:
    """CLI entry for canonical sweep (does not handle leading ``--legacy``)."""
    p = argparse.ArgumentParser(
        description=(
            "Layer 1 sweep: canonical reference engine via run_strategy_backtest. "
            "For legacy Numba grid, invoke with --legacy as the first argument "
            "(see docs/LEGACY_RESULTS_POLICY.md)."
        )
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help="Run deterministic synthetic canonical sweep (no QQQ / no parquet).",
    )
    p.add_argument("--strategy", default="synthetic_smoke", help="Strategy id label in results.")
    p.add_argument("--symbol", default="SYNTH", help="Symbol label in results rows.")
    p.add_argument("--start", default="2024-01-02", help="Data window label (smoke).")
    p.add_argument("--end", default="2024-01-02", help="Data window label (smoke).")
    p.add_argument("--config", default="", help="Strategy YAML path (reserved; not used by --smoke).")
    p.add_argument("--grid", default="", help="Parameter grid file (reserved; not used by --smoke).")
    p.add_argument("--data-root", default="", help="Reserved for future real-data sweeps.")
    p.add_argument(
        "--output-root",
        type=str,
        default=None,
        help="Optional directory for tiny CSV/JSON (respect --no-save).",
    )
    p.add_argument("--max-combos", type=int, default=None)
    p.add_argument("--no-save", action="store_true", help="Skip writing files even if --output-root set.")
    p.add_argument(
        "--canonical-help",
        action="store_true",
        help="Print canonical pipeline description.",
    )
    args = p.parse_args(argv)

    if args.canonical_help:
        print(
            "Canonical sweep: expand grid → canonical sig_* frame → "
            "run_strategy_backtest → simulate_trade_path → summarize_trades. "
            "Use --smoke for a built-in synthetic regression. "
            "Full real-data sweeps are not run in CI; wire read_bars + FeatureStore later."
        )
        return 0

    if args.data_root and not args.smoke:
        print(
            "ERROR: real-data canonical sweep is not wired in this release. "
            "Use --smoke or --legacy.",
            file=sys.stderr,
        )
        return 3

    if args.smoke:
        cfg = CanonicalSweepConfig(
            strategy=args.strategy,
            symbol=args.symbol,
            start=args.start,
            end=args.end,
            data_root=args.data_root,
            output_root=Path(args.output_root) if args.output_root else None,
            max_combos=args.max_combos,
            no_save=bool(args.no_save),
        )
        df = run_synthetic_canonical_smoke(sweep_cfg=cfg)
        print(f"engine={CANONICAL_ENGINE_LABEL}", flush=True)
        print(f"canonical_or_legacy=canonical", flush=True)
        print(df.to_string(index=False), flush=True)
        if cfg.output_root is not None and not cfg.no_save:
            _write_tiny_results(df, cfg.output_root)
            print(f"Wrote: {cfg.output_root.resolve()}", flush=True)
        return 0

    p.print_help(sys.stderr)
    return 1


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--legacy":
        print("engine=legacy_numba_fast", flush=True)
        from src.backtest.legacy.sweep_legacy import main as legacy_main

        return int(legacy_main(argv[1:]))
    return canonical_sweep_main(argv)


def validate_testing_grid_for_strategy(strategy: str, testing: dict[str, Any]) -> None:
    from src.backtest.legacy import sweep_legacy as sl

    return sl.validate_testing_grid_for_strategy(strategy, testing)


def _finalize_combo_config(cfg: dict[str, Any]) -> None:
    from src.backtest.legacy import sweep_legacy as sl

    return sl._finalize_combo_config(cfg)


def _load_testing_yaml(path: Any, *, expected_strategy: str) -> dict[str, Any]:
    from src.backtest.legacy import sweep_legacy as sl

    return sl._load_testing_yaml(path, expected_strategy=expected_strategy)


def _metrics_row(**kwargs: Any) -> dict[str, Any]:
    from src.backtest.legacy import sweep_legacy as sl

    return sl._metrics_row(**kwargs)


if __name__ == "__main__":
    raise SystemExit(main())
