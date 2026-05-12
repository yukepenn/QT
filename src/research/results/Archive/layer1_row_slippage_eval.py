"""Re-evaluate Layer 1 sweep rows at alternate slippage (same bars/features cache)."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import pandas as pd

_QT = Path(__file__).resolve().parents[4]
if str(_QT) not in sys.path:
    sys.path.insert(0, str(_QT))
_LEGACY_FAST = _QT / "archive" / "legacy_backtest" / "fast_legacy.py"
import importlib.util

_spec = importlib.util.spec_from_file_location("fast_legacy", _LEGACY_FAST)
assert _spec and _spec.loader
_fast = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fast)
run_fast_backtest_from_arrays = _fast.run_fast_backtest_from_arrays

from src.combiner.precompute import prepare_backtest_arrays
from src.backtest.sweep import _finalize_combo_config, _load_testing_yaml, _metrics_row
from src.data.read_bars import read_bars
from src.features.feature_key import feature_key_from_config
from src.features.feature_store import FeatureStore
from src.research.scoring import passes_filters
from src.research.select_candidates import unflatten_config_from_row
from src.strategies.loader import apply_overrides, load_strategy, load_strategy_config


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--results-csv", type=Path, required=True)
    p.add_argument("--strategy", required=True)
    p.add_argument("--testing-yaml", type=Path, required=True, help="Same grid as sweep (for base+validation).")
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--slippage", type=float, default=0.02)
    p.add_argument("--top-eval", type=int, default=120, help="Max rows to re-simulate after baseline filters.")
    p.add_argument("--out-csv", type=Path, required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    args = p.parse_args(argv)

    strat = load_strategy(args.strategy)
    if not strat.supports_fast:
        print("ERROR strategy needs supports_fast", file=sys.stderr)
        return 2

    testing = _load_testing_yaml(args.testing_yaml, expected_strategy=args.strategy)
    fixed = testing.get("fixed") or {}

    df = pd.read_csv(args.results_csv)
    df.insert(0, "__source_row__", range(len(df)))
    df = df[df["strategy"].astype(str) == args.strategy].copy()
    if df.empty:
        print("no rows", file=sys.stderr)
        return 2

    strict_ns = argparse.Namespace(
        min_trades=40,
        min_profit_factor=1.10,
        min_total_r=0.0,
        max_drawdown_r=-40.0,
        max_avg_bars_held=120.0,
        max_eod_count=0,
        max_end_of_data_count=0,
        max_max_hold_count=10**9,
    )
    base_filt = df[df.apply(lambda r: passes_filters(r, strict_ns), axis=1)].copy()
    base_filt = base_filt.sort_values("total_r", ascending=False).head(int(args.top_eval))
    if base_filt.empty:
        print("no rows after strict prefilter", file=sys.stderr)
        return 0

    base = load_strategy_config(args.strategy)
    feat_required = strat.required_features()
    sym = args.symbol.upper().strip()

    t0 = time.perf_counter()
    raw = read_bars(
        asset=args.asset,
        symbol=sym,
        root=None,
        start=args.start,
        end=args.end,
        data_dir=args.data_dir,
        contract=None,
    )
    if raw.empty:
        print("empty bars", file=sys.stderr)
        return 2

    fs = FeatureStore(
        asset=args.asset,
        symbol=sym,
        start=args.start,
        end=args.end,
        data_dir=args.data_dir,
        raw_df=raw,
    )
    array_cache: dict[tuple[str, ...], dict[str, Any]] = {}
    context_cache: dict[tuple[Any, ...], Any] = {}

    out_rows: list[dict[str, Any]] = []
    for idx, row in base_filt.iterrows():
        cfg = unflatten_config_from_row(row)
        cfg = apply_overrides(base, cfg)
        cfg = apply_overrides(cfg, fixed)
        if not cfg.get("strategy"):
            cfg = {"strategy": args.strategy, **cfg}
        _finalize_combo_config(cfg)
        strat.validate_config(cfg)
        bt = cfg.setdefault("backtest", {})
        bt["slippage_per_share"] = float(args.slippage)

        fk = feature_key_from_config(cfg)
        if fk not in array_cache:
            feat_df = fs.get_features_by_key(fk, cfg)
            array_cache[fk] = prepare_backtest_arrays(feat_df)
        else:
            feat_df = fs.get_features_by_key(fk, cfg)
        miss = [c for c in feat_required if c not in feat_df.columns]
        if miss:
            raise ValueError(f"missing features: {miss}")

        ck = (fk, strat.context_key(cfg))
        if ck not in context_cache:
            context_cache[ck] = strat.prepare_signal_context(feat_df, cfg)
        sig_arr = strat.generate_signal_arrays_from_context(context_cache[ck], cfg)
        b = cfg.get("backtest") or {}
        mh_raw = b.get("max_hold_minutes")
        max_hold_kw = None if mh_raw is None else int(mh_raw)
        metrics = run_fast_backtest_from_arrays(
            array_cache[fk],
            sig_arr,
            eod_exit_minute=int(b.get("eod_exit_minute", 389)),
            quantity=float(b.get("quantity", 1.0)),
            commission_per_trade=float(b.get("commission_per_trade", 0.0)),
            slippage_per_share=float(b.get("slippage_per_share", 0.0)),
            recompute_target_from_entry=bool(b.get("recompute_target_from_entry", True)),
            max_hold_minutes=max_hold_kw,
        )
        mr = _metrics_row(
            strategy=args.strategy,
            asset=args.asset,
            symbol=sym,
            root=None,
            contract=None,
            start=args.start,
            end=args.end,
            cfg=cfg,
            metrics=metrics,
        )
        mr["__source_row__"] = int(row["__source_row__"])
        mr["baseline_total_r"] = float(row.get("total_r", 0))
        mr["baseline_profit_factor"] = float(row.get("profit_factor", 0))
        mr["stress_slippage"] = float(args.slippage)
        out_rows.append(mr)

    out = pd.DataFrame(out_rows)
    outp = args.out_csv if args.out_csv.is_absolute() else Path.cwd() / args.out_csv
    outp.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(outp, index=False)
    print(f"wrote {outp} rows={len(out)} elapsed_s={time.perf_counter()-t0:.2f}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
