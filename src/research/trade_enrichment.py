"""Generic trade enrichment utilities (diagnostics-only).

Enrich trades with known-at-entry context by joining to a features DataFrame.
This module must remain:
- no-lookahead (ignores any *_LOOKAHEAD columns)
- robust to missing optional columns
- usable with compact trades (entry_ts_utc only) or index-based (entry_idx)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.read_bars import read_bars
from src.features.build_features import build_basic_features


NY_TZ = "America/New_York"


def _drop_lookahead_cols(df: pd.DataFrame) -> pd.DataFrame:
    bad = [c for c in df.columns if "LOOKAHEAD" in str(c)]
    return df.drop(columns=bad) if bad else df


def _bucket_entry_minute(mins: pd.Series) -> pd.Series:
    x = pd.to_numeric(mins, errors="coerce")
    out = pd.Series(index=x.index, dtype="object")
    out[x < 15] = "0-15"
    out[(x >= 15) & (x < 30)] = "15-30"
    out[(x >= 30) & (x < 60)] = "30-60"
    out[(x >= 60) & (x < 120)] = "60-120"
    out[x >= 120] = "120+"
    out[x.isna()] = "unknown"
    return out


def _bucket_gap_size_atr(x: pd.Series) -> pd.Series:
    v = pd.to_numeric(x, errors="coerce")
    out = pd.Series(index=v.index, dtype="object")
    out[v < 0.25] = "<0.25"
    out[(v >= 0.25) & (v < 0.50)] = "0.25-0.50"
    out[(v >= 0.50) & (v < 1.00)] = "0.50-1.00"
    out[(v >= 1.00) & (v < 1.50)] = "1.00-1.50"
    out[v >= 1.50] = ">1.50"
    out[v.isna()] = "unknown"
    return out


def _bucket_risk(x: pd.Series) -> pd.Series:
    v = pd.to_numeric(x, errors="coerce")
    out = pd.Series(index=v.index, dtype="object")
    out[v < 0.03] = "<0.03"
    out[(v >= 0.03) & (v < 0.05)] = "0.03-0.05"
    out[(v >= 0.05) & (v < 0.10)] = "0.05-0.10"
    out[v >= 0.10] = ">0.10"
    out[v.isna()] = "unknown"
    return out


def _bucket_bars_held(x: pd.Series) -> pd.Series:
    v = pd.to_numeric(x, errors="coerce")
    out = pd.Series(index=v.index, dtype="object")
    out[v < 5] = "<5"
    out[(v >= 5) & (v < 15)] = "5-15"
    out[(v >= 15) & (v < 30)] = "15-30"
    out[(v >= 30) & (v < 60)] = "30-60"
    out[v >= 60] = "60+"
    out[v.isna()] = "unknown"
    return out


def enrich_trades_with_context(
    trades_df: pd.DataFrame,
    features_df: pd.DataFrame,
    *,
    timestamp_col: str = "entry_ts_utc",
    idx_col: str = "entry_idx",
    tolerance: str | None = None,
) -> pd.DataFrame:
    """Enrich trades with known-at-entry context using features/bars.

    Join strategy:
    - If idx_col exists in trades_df and is integer-like, join by index position.
    - Else if timestamp_col exists, do an asof join on UTC timestamps.
    """
    if trades_df is None or len(trades_df) == 0:
        return pd.DataFrame()
    if features_df is None or len(features_df) == 0:
        out = trades_df.copy()
        # still compute buckets from whatever we have
        if "risk_per_share" in out.columns:
            out["risk_bucket"] = _bucket_risk(out["risk_per_share"])
        else:
            out["risk_bucket"] = "unknown"
        if "bars_held" in out.columns:
            out["bars_held_bucket"] = _bucket_bars_held(out["bars_held"])
        else:
            out["bars_held_bucket"] = "unknown"
        return out

    feat = _drop_lookahead_cols(features_df.copy())
    out = trades_df.copy()

    # Ensure time columns exist for joining.
    if "ts_utc" in feat.columns:
        feat["ts_utc"] = pd.to_datetime(feat["ts_utc"], utc=True, errors="coerce")
    if timestamp_col in out.columns:
        out[timestamp_col] = pd.to_datetime(out[timestamp_col], utc=True, errors="coerce")

    joined: pd.DataFrame
    if idx_col in out.columns and out[idx_col].notna().any():
        idx = pd.to_numeric(out[idx_col], errors="coerce").astype("Int64")
        out["_join_idx"] = idx
        feat2 = feat.reset_index(drop=True).copy()
        feat2["_join_idx"] = pd.Series(range(len(feat2)), dtype="int64")
        joined = out.merge(feat2, on="_join_idx", how="left", suffixes=("", "_feat"))
    else:
        if "ts_utc" not in feat.columns or timestamp_col not in out.columns:
            joined = out.copy()
        else:
            left = out.sort_values(timestamp_col).copy()
            right = feat.sort_values("ts_utc").copy()
            joined = pd.merge_asof(
                left,
                right,
                left_on=timestamp_col,
                right_on="ts_utc",
                direction="backward",
                tolerance=pd.Timedelta(tolerance) if tolerance else None,
                suffixes=("", "_feat"),
            )

    # Time / session convenience.
    if timestamp_col in joined.columns:
        ts = pd.to_datetime(joined[timestamp_col], utc=True, errors="coerce")
        joined["entry_ts_ny"] = ts.dt.tz_convert(NY_TZ)
        joined["session_date"] = joined["entry_ts_ny"].dt.normalize().dt.date.astype("string")

        # minute-from-open: prefer features minute_from_open if present, else compute from entry_ts_ny.
        if "minute_from_open" in joined.columns:
            joined["entry_minute_from_open"] = pd.to_numeric(joined["minute_from_open"], errors="coerce")
        else:
            mins = joined["entry_ts_ny"].dt.hour.mul(60).add(joined["entry_ts_ny"].dt.minute).sub(9 * 60 + 30)
            joined["entry_minute_from_open"] = pd.to_numeric(mins, errors="coerce")
        joined["entry_minute_bucket"] = _bucket_entry_minute(joined["entry_minute_from_open"])
    else:
        joined["entry_ts_ny"] = pd.NaT
        joined["session_date"] = pd.NA
        joined["entry_minute_from_open"] = pd.NA
        joined["entry_minute_bucket"] = "unknown"

    # Gap context (known at open).
    prior_close = None
    day_open = None
    for c in ("prior_day_close", "prior_close"):
        if c in joined.columns:
            prior_close = pd.to_numeric(joined[c], errors="coerce")
            break
    for c in ("day_open", "open"):
        if c in joined.columns:
            day_open = pd.to_numeric(joined[c], errors="coerce")
            break
    joined["prior_day_close"] = prior_close
    joined["day_open"] = day_open
    if prior_close is not None and day_open is not None:
        joined["gap_abs"] = day_open - prior_close
        joined["gap_pct"] = joined["gap_abs"] / prior_close.replace(0, pd.NA)
        ga = pd.to_numeric(joined["gap_abs"], errors="coerce")
        gd = pd.Series(index=joined.index, dtype="object")
        gd[ga > 0] = "gap_up"
        gd[ga < 0] = "gap_down"
        gd[ga == 0] = "flat"
        gd[ga.isna()] = "unknown"
        joined["gap_direction"] = gd
    else:
        joined["gap_abs"] = pd.NA
        joined["gap_pct"] = pd.NA
        joined["gap_direction"] = "unknown"

    # ATR + gap size bucket.
    atr = None
    for c in ("atr_like_15", "atr_at_entry", "atr"):
        if c in joined.columns:
            atr = pd.to_numeric(joined[c], errors="coerce")
            break
    joined["atr_at_entry"] = atr
    if atr is not None and "gap_abs" in joined.columns:
        joined["gap_size_atr"] = (pd.to_numeric(joined["gap_abs"], errors="coerce").abs()) / atr.replace(0, pd.NA)
        joined["gap_size_bucket"] = _bucket_gap_size_atr(joined["gap_size_atr"])
    else:
        joined["gap_size_atr"] = pd.NA
        joined["gap_size_bucket"] = "unknown"

    # VWAP context.
    if "vwap" in joined.columns and "close" in joined.columns:
        vwap = pd.to_numeric(joined["vwap"], errors="coerce")
        px = pd.to_numeric(joined["close"], errors="coerce")
        joined["vwap_at_entry"] = vwap
        diff = px - vwap
        side = pd.Series(index=joined.index, dtype="object")
        side[diff > 0] = "above_vwap"
        side[diff < 0] = "below_vwap"
        side[diff.abs() <= 1e-9] = "near_vwap"
        side[diff.isna()] = "unknown"
        joined["vwap_side_at_entry"] = side
    else:
        joined["vwap_at_entry"] = pd.NA
        joined["vwap_side_at_entry"] = "unknown"

    # ORB context (known ORB high/low).
    if "orb_high" in joined.columns and "orb_low" in joined.columns and "close" in joined.columns:
        oh = pd.to_numeric(joined["orb_high"], errors="coerce")
        ol = pd.to_numeric(joined["orb_low"], errors="coerce")
        px = pd.to_numeric(joined["close"], errors="coerce")
        ctx = pd.Series(index=joined.index, dtype="object")
        ctx[px > oh] = "above_orb"
        ctx[px < ol] = "below_orb"
        ctx[(px >= ol) & (px <= oh)] = "inside_orb"
        ctx[(px.isna()) | (oh.isna()) | (ol.isna())] = "unknown"
        joined["orb_high_known"] = oh
        joined["orb_low_known"] = ol
        joined["orb_context"] = ctx
    else:
        joined["orb_high_known"] = pd.NA
        joined["orb_low_known"] = pd.NA
        joined["orb_context"] = "unknown"

    # Buckets based on trade fields.
    if "risk_per_share" in joined.columns:
        joined["risk_bucket"] = _bucket_risk(joined["risk_per_share"])
    else:
        joined["risk_bucket"] = "unknown"
    if "bars_held" in joined.columns:
        joined["bars_held_bucket"] = _bucket_bars_held(joined["bars_held"])
    else:
        joined["bars_held_bucket"] = "unknown"

    return joined


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Enrich trades with bars/features context (diagnostics-only).")
    p.add_argument("--trades", required=True)
    p.add_argument("--bars-symbol", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--tolerance", default=None)
    args = p.parse_args(argv)

    trades_path = Path(args.trades)
    out_path = Path(args.out)
    if not trades_path.is_absolute():
        trades_path = Path.cwd() / trades_path
    if not out_path.is_absolute():
        out_path = Path.cwd() / out_path

    trades_df = pd.read_csv(trades_path)
    bars = read_bars(asset="equity", symbol=str(args.bars_symbol), start=str(args.start), end=str(args.end), data_dir=args.data_dir)
    feats = build_basic_features(bars, orb_open_minutes=15, copy=True, allow_overwrite=False)

    enriched = enrich_trades_with_context(trades_df, feats, tolerance=args.tolerance)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    enriched.to_csv(out_path, index=False)
    print(f"Wrote {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

