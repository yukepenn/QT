"""
Research-only: enrich combiner `trades.csv` rows with entry-time features (no lookahead).

Join policy: merge_asof backward on UTC — each trade uses the last bar's features at or before
`entry_ts_utc`. Does not forward-fill future bars.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.read_bars import read_bars
from src.features.build_features import build_basic_features
from src.features.build_types import RegimeFeatureConfig
from src.research.trade_quality_helpers import (
    ALWAYS_IN_MAP,
    REGIME_LABEL_MAP,
    TRADE_MODE_MAP,
    add_prior_trade_columns,
    enum_label,
    exit_reason_flags,
    merge_features_asof_backward,
)


DEFAULT_REGIME_WINDOW = 20


def _pick_columns(feats: pd.DataFrame, w: int) -> list[str]:
    candidates = [
        "minute_from_open",
        f"range_efficiency_{w}",
        f"vwap_cross_count_{w}",
        f"trend_score_{w}",
        f"compression_score_{w}",
        f"pa_strong_breakout_score_{w}",
        f"pa_trading_range_score_{w}",
        f"pa_climax_score_{w}",
        f"pa_late_trend_score_{w}",
        f"pa_trend_to_tr_transition_score_{w}",
        f"pa_limit_order_market_score_{w}",
        f"pa_regime_label_{w}",
        f"pa_trade_mode_{w}",
        f"pa_always_in_side_{w}",
        "pa_distance_from_vwap_atr",
        f"vwap_slope_{w}",
        "close_above_vwap",
        "close_below_vwap",
        "above_orb_high",
        "below_orb_low",
        "orb_width_pct",
        "orb_high_dist",
        "orb_low_dist",
        "atr_like_20",
        "near_prior_close_atr",
    ]
    near = [c for c in feats.columns if str(c).startswith("near_") and str(c).endswith("_atr")]
    base = [c for c in candidates if c in feats.columns]
    return ["ts_utc"] + base + [c for c in near if c not in base]


def _nearest_magnet(
    df: pd.DataFrame,
) -> tuple[pd.Series, pd.Series]:
    cols = [c for c in df.columns if str(c).startswith("near_") and str(c).endswith("_atr")]
    if not cols:
        return pd.Series([pd.NA] * len(df), dtype="string"), pd.Series(np.nan, index=df.index)
    sub = df[cols].apply(pd.to_numeric, errors="coerce")
    # smallest distance to any magnet proxy
    dist = sub.min(axis=1, skipna=True)
    # label: column name with min distance
    idx = sub.idxmin(axis=1, skipna=True)
    return idx.astype("string"), dist


def enrich_trades_frame(
    trades: pd.DataFrame,
    feats: pd.DataFrame,
    *,
    regime_window: int = DEFAULT_REGIME_WINDOW,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    meta: dict[str, Any] = {
        "timestamp_policy": "merge_asof_backward_on_entry_ts_utc_vs_feature_ts_utc",
        "regime_window": regime_window,
    }
    if trades.empty:
        meta["rows_in"] = 0
        meta["rows_out"] = 0
        meta["unmatched_trades"] = 0
        return trades.copy(), meta

    rows_in = len(trades)
    t2 = trades.copy()
    t2["entry_ts_utc"] = pd.to_datetime(t2["entry_ts_utc"], utc=True, errors="coerce")
    use_cols = _pick_columns(feats, regime_window)
    got = set(use_cols)
    meta["feature_columns_merged"] = sorted(c for c in got if c != "ts_utc")
    meta["missing_optional_feature_columns"] = sorted(
        c
        for c in [
            "minute_from_open",
            f"range_efficiency_{regime_window}",
            f"vwap_cross_count_{regime_window}",
            f"trend_score_{regime_window}",
            f"compression_score_{regime_window}",
            f"pa_strong_breakout_score_{regime_window}",
            f"pa_trading_range_score_{regime_window}",
            f"pa_climax_score_{regime_window}",
            f"pa_late_trend_score_{regime_window}",
            f"pa_trend_to_tr_transition_score_{regime_window}",
            f"pa_limit_order_market_score_{regime_window}",
            f"pa_regime_label_{regime_window}",
            f"pa_trade_mode_{regime_window}",
            f"pa_always_in_side_{regime_window}",
            "pa_distance_from_vwap_atr",
            f"vwap_slope_{regime_window}",
            "close_above_vwap",
            "close_below_vwap",
            "above_orb_high",
            "below_orb_low",
            "orb_width_pct",
            "orb_high_dist",
            "orb_low_dist",
            "atr_like_20",
            "near_prior_close_atr",
        ]
        if c not in feats.columns
    )

    fsub = feats[use_cols].copy()
    merged = merge_features_asof_backward(t2, fsub, trade_ts_col="entry_ts_utc", feature_ts_col="ts_utc")
    keycol = f"pa_regime_label_{regime_window}"
    unmatched = int(merged[keycol].isna().sum()) if keycol in merged.columns else int(merged["minute_from_open"].isna().sum()) if "minute_from_open" in merged.columns else len(merged)

    merged = add_prior_trade_columns(
        merged,
        session_col="session_date",
        entry_ts_col="entry_ts_utc",
        strategy_col="strategy",
        family_col="strategy_family",
        r_col="r_multiple",
    )
    if "daily_trade_number" in merged.columns:
        merged["entry_trade_number_of_day"] = pd.to_numeric(merged["daily_trade_number"], errors="coerce")
    merged["entry_session_date"] = merged["session_date"].astype(str)
    merged["entry_strategy"] = merged["strategy"].astype(str)
    merged["entry_family"] = merged["strategy_family"].astype(str)
    merged["entry_candidate"] = merged.get("candidate_id", pd.Series(pd.NA, index=merged.index)).astype(str)
    merged["entry_side"] = merged["side"].astype(str)

    w = regime_window
    if f"pa_regime_label_{w}" in merged.columns:
        merged["entry_regime_label"] = merged[f"pa_regime_label_{w}"].map(
            lambda x: enum_label(REGIME_LABEL_MAP, x)
        )
    if f"pa_trade_mode_{w}" in merged.columns:
        merged["entry_trade_mode"] = merged[f"pa_trade_mode_{w}"].map(lambda x: enum_label(TRADE_MODE_MAP, x))
    if f"pa_always_in_side_{w}" in merged.columns:
        merged["entry_always_in_side"] = merged[f"pa_always_in_side_{w}"].map(
            lambda x: enum_label(ALWAYS_IN_MAP, x)
        )

    rename_map = {
        "minute_from_open": "entry_minute_from_open",
        f"range_efficiency_{w}": "entry_range_efficiency",
        f"vwap_cross_count_{w}": "entry_vwap_cross_count",
        f"trend_score_{w}": "entry_trend_score",
        f"compression_score_{w}": "entry_compression_score",
        f"pa_strong_breakout_score_{w}": "entry_pa_strong_breakout_score",
        f"pa_trading_range_score_{w}": "entry_pa_trading_range_score",
        f"pa_climax_score_{w}": "entry_pa_climax_score",
        f"pa_late_trend_score_{w}": "entry_pa_late_trend_score",
        f"pa_trend_to_tr_transition_score_{w}": "entry_pa_trend_to_tr_transition_score",
        f"pa_limit_order_market_score_{w}": "entry_pa_limit_order_market_score",
        "pa_distance_from_vwap_atr": "entry_distance_from_vwap_atr",
        f"vwap_slope_{w}": "entry_vwap_slope",
        "close_above_vwap": "entry_above_vwap",
        "close_below_vwap": "entry_below_vwap",
        "above_orb_high": "entry_above_orb_high",
        "below_orb_low": "entry_below_orb_low",
        "orb_width_pct": "entry_orb_width_pct",
        "orb_high_dist": "entry_orb_high_dist",
        "orb_low_dist": "entry_orb_low_dist",
        "near_prior_close_atr": "entry_distance_to_prev_close_atr",
    }
    for old, new in rename_map.items():
        if old in merged.columns and new not in merged.columns:
            merged[new] = merged[old]

    atr = pd.to_numeric(merged.get("atr_like_20", pd.Series(np.nan, index=merged.index)), errors="coerce")
    if "entry_orb_high_dist" in merged.columns:
        merged["entry_distance_to_orh_atr"] = pd.to_numeric(merged["entry_orb_high_dist"], errors="coerce") / (
            atr + 1e-12
        )
    if "entry_orb_low_dist" in merged.columns:
        merged["entry_distance_to_orl_atr"] = pd.to_numeric(merged["entry_orb_low_dist"], errors="coerce") / (
            atr + 1e-12
        )

    nm_lab, nm_dist = _nearest_magnet(merged)
    merged["entry_nearest_magnet"] = nm_lab
    merged["entry_magnet_distance_atr"] = nm_dist

    if "exit_reason" in merged.columns:
        flags = merged["exit_reason"].map(exit_reason_flags)
        merged["entry_is_profit_target_exit"] = [t[0] for t in flags]
        merged["entry_is_stop_exit"] = [t[1] for t in flags]
        merged["entry_is_forced_exit"] = [t[2] for t in flags]

    meta["rows_in"] = rows_in
    meta["rows_out"] = len(merged)
    meta["unmatched_trades"] = unmatched
    meta["missing_optional_fields"] = meta["missing_optional_feature_columns"]
    return merged, meta


def _write_summary_md(path: Path, meta: dict[str, Any], output_csv: Path) -> None:
    lines = [
        "# Trade enrichment summary",
        "",
        f"- rows_in: {meta.get('rows_in')}",
        f"- rows_out: {meta.get('rows_out')}",
        f"- unmatched_trades (no minute_from_open after join): {meta.get('unmatched_trades')}",
        f"- timestamp_policy: `{meta.get('timestamp_policy')}`",
        f"- regime_window: {meta.get('regime_window')}",
        f"- output: `{output_csv.as_posix()}`",
        "",
        "## Feature columns merged",
        "",
        "```",
        json.dumps(meta.get("feature_columns_merged", []), indent=2),
        "```",
        "",
        "## Missing optional feature columns",
        "",
        "```",
        json.dumps(meta.get("missing_optional_feature_columns", []), indent=2),
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Enrich combiner trades with entry-time features.")
    p.add_argument("--trades", default=None, help="Path to trades.csv")
    p.add_argument("--manifest", default=None, help="CSV with columns including trades_path, system_label")
    p.add_argument("--asset", choices=["equity", "futures"], default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--output", default=None, help="Single output CSV")
    p.add_argument("--summary", default=None, help="Single summary .md")
    p.add_argument("--output-root", default=None, help="Directory for manifest mode outputs")
    p.add_argument("--regime-window", type=int, default=DEFAULT_REGIME_WINDOW)
    args = p.parse_args(argv)

    raw = read_bars(
        asset=args.asset,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        data_dir=args.data_dir,
    )
    feats = build_basic_features(
        raw,
        orb_open_minutes=15,
        copy=True,
        allow_overwrite=False,
        regime=RegimeFeatureConfig(windows=(int(args.regime_window),)),
    )

    if args.manifest:
        man = pd.read_csv(args.manifest)
        root = Path(args.output_root or "src/research/results/trade_quality_router_v1/enriched_trades")
        if not root.is_absolute():
            root = Path.cwd() / root
        root.mkdir(parents=True, exist_ok=True)
        col_path = "trades_path" if "trades_path" in man.columns else "trade_file"
        for _, row in man.iterrows():
            tpath = Path(str(row[col_path]))
            if not tpath.is_absolute():
                tpath = Path.cwd() / tpath
            label = str(row.get("system_label", tpath.stem))
            trades = pd.read_csv(tpath)
            enriched, meta = enrich_trades_frame(trades, feats, regime_window=int(args.regime_window))
            out_csv = root / f"{label}_enriched.csv"
            enriched.to_csv(out_csv, index=False)
            _write_summary_md(root / f"{label}_enrichment_summary.md", meta, out_csv)
            print(f"Wrote {out_csv}", flush=True)
        return 0

    if not args.trades or not args.output:
        print("ERROR: need --trades and --output, or --manifest", file=sys.stderr)
        return 2
    tpath = Path(args.trades)
    if not tpath.is_absolute():
        tpath = Path.cwd() / tpath
    trades = pd.read_csv(tpath)
    enriched, meta = enrich_trades_frame(trades, feats, regime_window=int(args.regime_window))
    out = Path(args.output)
    if not out.is_absolute():
        out = Path.cwd() / out
    out.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(out, index=False)
    if args.summary:
        sp = Path(args.summary)
        if not sp.is_absolute():
            sp = Path.cwd() / sp
        _write_summary_md(sp, meta, out)
    print(f"Wrote {out}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
