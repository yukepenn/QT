"""Orchestrate basic feature columns (read_bars → features). Runnable CLI."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd

from src.features.build_types import ChannelsFeatureConfig, IndicatorsFeatureConfig, RegimeFeatureConfig
from src.features.channels import add_channel_features
from src.features.feature_config import FEATURE_COLUMNS, RAW_COLUMNS, validate_no_registry_duplicates
from src.features.indicators import add_indicator_features
from src.features.levels import add_prior_day_levels
from src.features.orb import add_orb
from src.features.price_action import add_price_action_features
from src.features.regime import add_regime_features
from src.features.time_features import add_time_features
from src.features.volatility import add_intraday_volatility
from src.features.volume import add_volume_features
from src.features.vwap import add_vwap


def build_basic_features(
    df: pd.DataFrame,
    *,
    orb_open_minutes: int = 15,
    vwap_bands: tuple[float, ...] = (1.0, 2.0),
    vol_windows: tuple[int, ...] = (5, 15, 30),
    price_action_windows: tuple[int, ...] = (3, 5, 10, 20, 30, 60),
    volume_windows: tuple[int, ...] = (20, 30, 60),
    indicators: IndicatorsFeatureConfig | None = None,
    channels: ChannelsFeatureConfig | None = None,
    regime: RegimeFeatureConfig | None = None,
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    validate_no_registry_duplicates()
    ind = indicators or IndicatorsFeatureConfig()
    ch = channels or ChannelsFeatureConfig()
    reg = regime or RegimeFeatureConfig()

    out = add_time_features(df, copy=copy, allow_overwrite=allow_overwrite)
    out = add_vwap(out, bands=vwap_bands, copy=False, allow_overwrite=allow_overwrite)
    out = add_orb(out, open_minutes=orb_open_minutes, copy=False, allow_overwrite=allow_overwrite)
    out = add_prior_day_levels(out, copy=False, allow_overwrite=allow_overwrite)
    out = add_intraday_volatility(out, windows=vol_windows, copy=False, allow_overwrite=allow_overwrite)
    out = add_price_action_features(out, windows=price_action_windows, copy=False, allow_overwrite=allow_overwrite)
    out = add_volume_features(out, windows=volume_windows, copy=False, allow_overwrite=allow_overwrite)
    out = add_indicator_features(out, ind, copy=False, allow_overwrite=allow_overwrite)
    out = add_channel_features(out, ch, copy=False, allow_overwrite=allow_overwrite)
    out = add_regime_features(out, reg, copy=False, allow_overwrite=allow_overwrite)
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Read bars and build basic features (in-memory).")
    p.add_argument("--asset", choices=["equity", "futures"], required=True)
    p.add_argument("--symbol", default=None)
    p.add_argument("--root", default=None)
    p.add_argument("--contract", default=None)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--orb-open-minutes", type=int, default=15)
    p.add_argument("--head", type=int, default=5)
    args = p.parse_args(argv)

    if args.asset == "equity" and not args.symbol:
        print("ERROR equity requires --symbol", file=sys.stderr)
        return 2
    if args.asset == "futures" and not args.root:
        print("ERROR futures requires --root", file=sys.stderr)
        return 2

    try:
        validate_no_registry_duplicates()
        print("registry_validation=passed", flush=True)
    except ValueError as e:
        print(f"registry_validation=FAILED {e}", file=sys.stderr)
        return 1

    from src.data.read_bars import read_bars

    df = read_bars(
        asset=args.asset,
        symbol=args.symbol,
        root=args.root,
        start=args.start,
        end=args.end,
        data_dir=args.data_dir,
        contract=args.contract,
    )
    raw_subset = [c for c in RAW_COLUMNS if c in df.columns]
    raw_snap = df[raw_subset].copy()

    out = build_basic_features(
        df,
        orb_open_minutes=int(args.orb_open_minutes),
        copy=True,
        allow_overwrite=False,
    )

    preserved = True
    for c in raw_subset:
        if c == "ts_ny":
            continue
        if not raw_snap[c].equals(out[c]):
            preserved = False
            break
    if "ts_utc" in raw_subset:
        preserved = preserved and raw_snap["ts_utc"].equals(out["ts_utc"])

    print(f"rows={len(out)}", flush=True)
    print(f"min_ts_utc={out['ts_utc'].min().isoformat() if len(out) else 'n/a'}", flush=True)
    print(f"max_ts_utc={out['ts_utc'].max().isoformat() if len(out) else 'n/a'}", flush=True)
    print(f"raw_column_count={len(raw_subset)}", flush=True)
    print(f"final_column_count={len(out.columns)}", flush=True)
    feat_cols = [c for c in out.columns if c not in RAW_COLUMNS]
    print(f"feature_column_count={len(feat_cols)}", flush=True)
    print(f"raw_columns_preserved_subset={preserved}", flush=True)

    print("feature_columns_by_module:", flush=True)
    for mod, cols in FEATURE_COLUMNS.items():
        present = [c for c in cols if c in out.columns]
        print(f"  {mod}: {present}", flush=True)

    head_cols = [
        "ts_ny",
        "asset",
        "symbol",
        "root",
        "contract",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "session_date",
        "minute_from_open",
        "vwap",
        "vwap_dist_pct",
        "vwap_z",
        "orb_high",
        "orb_low",
        "orb_breakout_dir",
        "prior_day_high",
        "prior_day_low",
        "ret_std_15",
        "atr_like_15",
    ]
    existing = [c for c in head_cols if c in out.columns]
    print(f"head_columns={existing}", flush=True)
    if len(out):
        print(out[existing].head(int(args.head)).to_string(), flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
