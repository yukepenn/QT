"""PA gate diagnostics: entry-window vs finalized signal counts (first grid combo).

Intermediate gate breakdown is implemented for ``pa_broad_channel_zone`` only; other
strategies report totals plus ``valid_signals`` so sparse/zero-trade strategies still
surface bottleneck magnitude (entry window vs final fills).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.backtest.sweep import _finalize_combo_config
from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config
from src.strategies.loader import (
    apply_overrides,
    expand_grid,
    load_strategy,
    load_strategy_config,
)
from src.strategies.strategy.pa_batch_a_utils import finalize_long_signals_df


def _merge_first_combo(testing_path: Path, strategy: str) -> dict[str, Any]:
    data = yaml.safe_load(testing_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("strategy") != strategy:
        raise ValueError("testing YAML strategy mismatch")
    base = load_strategy_config(strategy)
    grid = expand_grid(data)
    fixed = data.get("fixed") or {}
    combo_flat = grid[0] if grid else {}
    cfg = apply_overrides(apply_overrides(dict(base), combo_flat), fixed)
    _finalize_combo_config(cfg)
    return cfg


def _gates_broad_channel(ctx: Any, config: dict[str, Any]) -> dict[str, float]:
    sig = config.get("signal") or {}
    es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
    thr = float(sig.get("broad_bull_score_min", 0.28))
    max_pd = float(sig.get("max_pullback_depth_atr", 1.15))
    min_pd = float(sig.get("min_pullback_depth_atr", 0.05))
    req_v = bool(sig.get("require_vwap_context", False))
    vwap_min = float(sig.get("vwap_context_min_atr", -0.15))
    block_clx = bool(sig.get("block_climax", True))
    clx_max = float(sig.get("climax_score_max", 0.78))

    n = ctx.n
    minute = ctx.minute
    win = (minute >= es) & (minute <= ee)
    bb = win & np.isfinite(ctx.pa_bbull) & (ctx.pa_bbull >= thr)
    zone = bb & np.isfinite(ctx.close) & (ctx.close <= ctx.pa_rlt)
    pd_ok = (
        zone & np.isfinite(ctx.pa_pd) & (ctx.pa_pd >= min_pd) & (ctx.pa_pd <= max_pd)
    )
    if req_v:
        vw_ok = (
            pd_ok & np.isfinite(ctx.vwap) & (ctx.close >= ctx.vwap + vwap_min * ctx.atr)
        )
    else:
        vw_ok = pd_ok
    rev_ok = vw_ok & (ctx.bull_rev != 0)
    if block_clx:
        climax_ok = rev_ok & (~np.isfinite(ctx.pa_clx) | (ctx.pa_clx <= clx_max))
    else:
        climax_ok = rev_ok

    risk = config.get("risk") or {}
    sm = str(risk.get("stop_mode", "range_low"))
    if sm == "channel_low":
        sm = "range_low"
    tm = str(risk.get("target_mode", "fixed_r"))
    if tm == "channel_mid":
        tm = "range_mid"

    arr = finalize_long_signals_df(
        pd.DataFrame({"_i": np.arange(ctx.n)}),
        strategy_name="pa_gate",
        config=config,
        cand_long=climax_ok.astype(np.bool_),
        session_id=ctx.session_id,
        close=ctx.close,
        low=ctx.low,
        high=ctx.high,
        atr=ctx.atr,
        stop_mode=sm,
        target_mode=tm,
        target_r=float(risk.get("target_r", 1.5)),
        atr_buf_mult=float(risk.get("atr_buffer_mult", 0.35)),
        range_low=ctx.pa_rl,
        range_mid=ctx.pa_rmid,
        range_high=ctx.pa_rh,
        upper_third=ctx.pa_rut,
        vwap=ctx.vwap,
    )

    return {
        "total_bars": float(n),
        "bars_entry_window": float(np.sum(win)),
        "pass_regime_broad_bull": float(np.sum(bb)),
        "pass_zone_below_upper_third": float(np.sum(zone)),
        "pass_pullback_depth_band": float(np.sum(pd_ok)),
        "pass_vwap_context": float(np.sum(vw_ok)),
        "pass_bull_reversal_or_break_bar": float(np.sum(rev_ok)),
        "pass_climax_block": float(np.sum(climax_ok)),
        "final_valid_signals": float(arr["valid"].sum()),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="PA gate diagnostics")
    p.add_argument("--strategy", required=True)
    p.add_argument("--testing-config", type=Path, required=True)
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--output-root", type=Path, required=True)
    args = p.parse_args(argv)

    strat = load_strategy(args.strategy)
    cfg = _merge_first_combo(args.testing_config, args.strategy)
    strat.validate_config(cfg)

    raw = read_bars(
        asset=args.asset, symbol=args.symbol, start=args.start, end=args.end
    )
    if raw.empty:
        print("ERROR: empty bars", file=sys.stderr)
        return 2

    feat = build_features_from_config(raw, cfg).sort_values("ts_utc", ignore_index=True)
    ctx = strat.prepare_signal_context(feat, cfg)

    minute = feat["minute_from_open"].to_numpy(dtype=np.int32)
    sig = cfg.get("signal") or {}
    es, ee = int(sig["entry_start_minute"]), int(sig["entry_end_minute"])
    win_mask = (minute >= es) & (minute <= ee)

    meta: dict[str, Any] = {
        "strategy": args.strategy,
        "symbol": args.symbol,
        "start": args.start,
        "end": args.end,
        "testing_config": str(args.testing_config).replace("\\", "/"),
    }

    if args.strategy == "pa_broad_channel_zone":
        row = {**meta, **_gates_broad_channel(ctx, cfg)}
    else:
        arr = strat.generate_signal_arrays_from_context(ctx, cfg)
        row = {
            **meta,
            "total_bars": float(len(feat)),
            "bars_entry_window": float(np.sum(win_mask)),
            "final_valid_signals": float(arr["valid"].sum()),
        }

    args.output_root.mkdir(parents=True, exist_ok=True)
    flat_path = args.output_root / "pa_gate_rows.csv"
    write_header = not flat_path.exists()
    with flat_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row.keys()))
        if write_header:
            w.writeheader()
        w.writerow(row)

    jl = args.output_root / "pa_gate_rows.jsonl"
    with jl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, sort_keys=True) + "\n")

    print(json.dumps(row, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
