"""Generic readable-vs-fast signal array parity check for sweep-ready strategies."""

from __future__ import annotations

import argparse
import json
import sys
from copy import deepcopy
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.backtest.sweep import _finalize_combo_config
from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config
from src.strategies.loader import apply_overrides, expand_grid, load_strategy, load_strategy_config
from src.strategies.strategy.fast_utils import pack_signal_arrays_from_df


def _load_testing(path: Path, *, strategy: str) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("strategy") != strategy:
        raise ValueError(f"testing YAML strategy mismatch for {strategy}")
    return data


def _merge_cfg(base: dict, combo_flat: dict, fixed: dict) -> dict:
    cfg = apply_overrides(deepcopy(base), combo_flat)
    cfg = apply_overrides(cfg, fixed)
    _finalize_combo_config(cfg)
    return cfg


def _compare(a: np.ndarray, b: np.ndarray, mask: np.ndarray, rtol: float, atol: float) -> int:
    miss = 0
    for i in np.flatnonzero(mask):
        x, y = float(a[i]), float(b[i])
        if np.isnan(x) and np.isnan(y):
            continue
        if abs(x - y) > atol + rtol * max(abs(x), abs(y)):
            miss += 1
    return miss


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Compare pandas generate_signals vs fast arrays.")
    p.add_argument("--strategy", required=True)
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--testing-config", type=Path, required=True)
    p.add_argument("--max-combos", type=int, default=10)
    p.add_argument("--orb-open-minutes", type=int, default=5)
    p.add_argument("--rtol", type=float, default=1e-6)
    p.add_argument("--atol", type=float, default=1e-8)
    args = p.parse_args(argv)

    strat = load_strategy(args.strategy)
    base = load_strategy_config(args.strategy)
    testing = _load_testing(args.testing_config, strategy=args.strategy)
    grid = expand_grid(testing)
    fixed = testing.get("fixed") or {}
    combos = grid[: max(1, args.max_combos)]

    raw = read_bars(asset=args.asset, symbol=args.symbol, start=args.start, end=args.end)
    if raw.empty:
        print("ERROR empty bars", file=sys.stderr)
        return 2

    # Build features using config-derived knobs; optionally override orb_open_minutes for parity runs.
    cfg0 = load_strategy_config(args.strategy)
    if args.orb_open_minutes is not None:
        cfg0 = apply_overrides(cfg0, {"features.orb_open_minutes": int(args.orb_open_minutes)})
    feat = build_features_from_config(raw, cfg0).sort_values("ts_utc", ignore_index=True)

    miss_total = 0
    for ix, combo_flat in enumerate(combos):
        cfg = _merge_cfg(base, combo_flat, fixed)
        df_r = strat.generate_signals(feat, cfg)
        from src.strategies.strategy.base import validate_standard_signal_columns

        validate_standard_signal_columns(df_r)

        ctx = strat.prepare_signal_context(feat, cfg)
        fast = strat.generate_signal_arrays_from_context(ctx, cfg)
        packed = pack_signal_arrays_from_df(df_r)

        side_m = _compare(packed["side"], fast["side"], np.ones(len(feat), dtype=bool), 0, 0)
        valid_m = _compare(
            packed["valid"].astype(np.float64),
            fast["valid"].astype(np.float64),
            np.ones(len(feat), dtype=bool),
            0,
            0,
        )
        mask = packed["valid"] | fast["valid"]
        st_m = _compare(packed["stop"], fast["stop"], mask, args.rtol, args.atol)
        tm_m = _compare(
            packed["target_mode_code"].astype(np.float64),
            fast["target_mode_code"].astype(np.float64),
            mask,
            0,
            0,
        )
        tr_m = _compare(packed["target_r"], fast["target_r"], mask, args.rtol, args.atol)
        rk_m = _compare(packed["risk_preview"], fast["risk_preview"], mask, args.rtol, args.atol)

        row_miss = side_m + valid_m + st_m + tm_m + tr_m + rk_m
        miss_total += row_miss
        print(
            f"combo[{ix}] diff_counts side={side_m} valid={valid_m} stop={st_m} "
            f"tmc={tm_m} tr={tr_m} risk={rk_m} cfg={json.dumps(combo_flat, default=str)[:120]}",
            flush=True,
        )
        if row_miss:
            idx = np.flatnonzero(
                np.abs(packed["side"].astype(np.float64) - fast["side"].astype(np.float64)) > 0
            )[:5]
            print(f"  first side idx: {idx.tolist()}", flush=True)

    print(f"TOTAL_MISMATCH_FIELDS approx={miss_total}", flush=True)
    return 1 if miss_total else 0


if __name__ == "__main__":
    raise SystemExit(main())
