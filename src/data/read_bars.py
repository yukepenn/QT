"""
Read monthly IBKR bar partitions from data/raw/ibkr into a single DataFrame.

Runnable: python src/data/read_bars.py ...
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

NY_TZ = "America/New_York"
UTC_TZ = "UTC"


def _iter_candidate_months(start_ny: pd.Timestamp, end_ny_inclusive: pd.Timestamp) -> Iterable[tuple[int, int]]:
    y = int(start_ny.year)
    m = int(start_ny.month)
    y_end = int(end_ny_inclusive.year)
    m_end = int(end_ny_inclusive.month)
    while (y < y_end) or (y == y_end and m <= m_end):
        yield y, m
        m += 1
        if m > 12:
            m = 1
            y += 1


def _ny_bounds(start: str, end: str) -> tuple[pd.Timestamp, pd.Timestamp, pd.Timestamp, pd.Timestamp]:
    start_ny = pd.Timestamp(start).tz_localize(NY_TZ)
    end_day_ny = pd.Timestamp(end).tz_localize(NY_TZ)
    end_ny_inclusive = end_day_ny + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    if end_ny_inclusive < start_ny:
        raise ValueError("end must be >= start")
    start_utc = start_ny.tz_convert(UTC_TZ)
    end_utc = end_ny_inclusive.tz_convert(UTC_TZ)
    return start_ny, end_ny_inclusive, start_utc, end_utc


def read_bars(
    *,
    asset: str,
    symbol: str | None = None,
    root: str | None = None,
    start: str,
    end: str,
    data_dir: str | Path = "data/raw/ibkr",
    contract: str | None = None,
) -> pd.DataFrame:
    if asset not in ("equity", "futures"):
        raise ValueError('asset must be "equity" or "futures"')

    base = Path(data_dir)
    start_ny, end_ny_inclusive, start_utc, end_utc = _ny_bounds(start, end)
    months = list(_iter_candidate_months(start_ny, end_ny_inclusive))

    paths: list[Path] = []

    if asset == "equity":
        if not symbol:
            raise ValueError("equity requires symbol")
        sym = symbol.upper().strip()
        root_dir = base / "equity" / "bars_1min" / f"symbol={sym}"
        for y, mo in months:
            p = root_dir / f"year={y}" / f"month={mo:02d}" / "data.parquet"
            if p.is_file():
                paths.append(p)

    else:
        if not root:
            raise ValueError("futures requires root")
        r = root.upper().strip()
        root_dir = base / "futures" / "bars_1min" / f"root={r}"

        if contract:
            c = contract.strip()
            cdir = root_dir / f"contract={c}"
            for y, mo in months:
                p = cdir / f"year={y}" / f"month={mo:02d}" / "data.parquet"
                if p.is_file():
                    paths.append(p)
        else:
            for cdir in sorted(root_dir.glob("contract=*")):
                for y, mo in months:
                    p = cdir / f"year={y}" / f"month={mo:02d}" / "data.parquet"
                    if p.is_file():
                        paths.append(p)

    if not paths:
        return pd.DataFrame()

    frames = [pd.read_parquet(p) for p in paths]
    df = pd.concat(frames, ignore_index=True)

    if "ts_utc" not in df.columns:
        raise ValueError("expected column ts_utc")

    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    if "ts_ny" not in df.columns:
        df["ts_ny"] = df["ts_utc"].dt.tz_convert(NY_TZ)
    else:
        df["ts_ny"] = pd.to_datetime(df["ts_ny"])
        if df["ts_ny"].dt.tz is None:
            df["ts_ny"] = df["ts_ny"].dt.tz_localize(UTC_TZ).dt.tz_convert(NY_TZ)
        else:
            df["ts_ny"] = df["ts_ny"].dt.tz_convert(NY_TZ)

    df = df[(df["ts_utc"] >= start_utc) & (df["ts_utc"] <= end_utc)].copy()
    df = df.sort_values("ts_utc").reset_index(drop=True)

    if asset == "equity":
        key = ["symbol", "ts_utc"]
    else:
        key = ["root", "contract", "ts_utc"]

    dup_before = int(df.duplicated(subset=key).sum())
    df = df.drop_duplicates(subset=key, keep="first").reset_index(drop=True)
    dup_after = int(df.duplicated(subset=key).sum())

    if dup_after != 0:
        raise RuntimeError(f"dedupe failed: {dup_after} duplicate rows remain")

    df.attrs["_duplicates_dropped"] = dup_before
    return df


def _print_summary(df: pd.DataFrame, *, asset: str, symbol: str | None, root: str | None, contract: str | None) -> None:
    print(f"asset={asset}", flush=True)
    if asset == "equity":
        print(f"symbol={symbol}", flush=True)
    else:
        print(f"root={root} contract={contract or '*'}", flush=True)
    print(f"rows={len(df)}", flush=True)
    if df.empty:
        print("min_ts_utc=(empty) max_ts_utc=(empty)", flush=True)
        print("unique_ny_dates=0", flush=True)
        print("duplicates_dropped=0 duplicate_count_after_dedupe=0", flush=True)
        print(f"columns={[]}", flush=True)
        return
    print(f"min_ts_utc={df['ts_utc'].min().isoformat()}", flush=True)
    print(f"max_ts_utc={df['ts_utc'].max().isoformat()}", flush=True)
    ny_dates = df["ts_ny"].dt.normalize().dt.date.nunique()
    print(f"unique_ny_dates={int(ny_dates)}", flush=True)
    dropped = int(df.attrs.get("_duplicates_dropped", 0))
    print(f"duplicates_dropped={dropped} duplicate_count_after_dedupe=0", flush=True)
    print(f"columns={list(df.columns)}", flush=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Read IBKR 1-min bar partitions into one DataFrame.")
    p.add_argument("--asset", choices=["equity", "futures"], required=True)
    p.add_argument("--symbol", default=None)
    p.add_argument("--root", default=None)
    p.add_argument("--contract", default=None)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", default="data/raw/ibkr")
    p.add_argument("--out", default=None, help="Write .parquet or .csv")
    p.add_argument("--head", type=int, default=5)
    args = p.parse_args(argv)

    if args.asset == "equity" and not args.symbol:
        print("ERROR equity requires --symbol", file=sys.stderr)
        return 2
    if args.asset == "futures" and not args.root:
        print("ERROR futures requires --root", file=sys.stderr)
        return 2

    try:
        df = read_bars(
            asset=args.asset,
            symbol=args.symbol,
            root=args.root,
            start=args.start,
            end=args.end,
            data_dir=args.data_dir,
            contract=args.contract,
        )
    except Exception as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 1

    _print_summary(df, asset=args.asset, symbol=args.symbol, root=args.root, contract=args.contract)
    print("", flush=True)
    if not df.empty:
        print(df.head(int(args.head)).to_string(), flush=True)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        suf = out_path.suffix.lower()
        if suf == ".parquet":
            df.to_parquet(out_path, index=False)
        elif suf == ".csv":
            df.to_csv(out_path, index=False)
        else:
            print(f"ERROR --out must end with .parquet or .csv, got {suf}", file=sys.stderr)
            return 2
        print(f"\nWrote: {out_path.resolve()}", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
