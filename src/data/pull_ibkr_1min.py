"""
Minimal IBKR historical downloader for 1-minute bars (equities + explicit futures).

Runnable directly:
  python src/data/pull_ibkr_1min.py ...

No package-relative imports. No dependencies beyond stdlib + pandas + ib_insync.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Literal, Sequence

import pandas as pd
from ib_insync import IB, Future, Stock, util

Asset = Literal["equity", "futures"]

NY_TZ = "America/New_York"
UTC_TZ = "UTC"


@dataclass(frozen=True)
class DateBounds:
    start_ny: pd.Timestamp
    end_ny_inclusive: pd.Timestamp
    start_utc: pd.Timestamp
    end_utc_inclusive: pd.Timestamp


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Download IBKR historical 1-min bars (equity + explicit futures).")

    p.add_argument("--host", default=os.getenv("IB_HOST", "127.0.0.1"))
    p.add_argument("--port", type=int, default=int(os.getenv("IB_PORT", "4002")))
    p.add_argument("--client-id", type=int, default=int(os.getenv("IB_CLIENT_ID", "19")))
    p.add_argument("--connect-timeout", type=float, default=10.0)

    p.add_argument("--asset", choices=["equity", "futures"], required=True)
    p.add_argument("--start", required=True, help="YYYY-MM-DD (interpreted in America/New_York)")
    p.add_argument("--end", required=True, help="YYYY-MM-DD (inclusive, interpreted in America/New_York)")
    p.add_argument("--chunk-days", type=int, default=5)
    p.add_argument("--sleep", type=float, default=1.0)
    p.add_argument("--what", default="TRADES")
    p.add_argument("--bar-size", default="1 min")

    rth = p.add_mutually_exclusive_group()
    rth.add_argument("--rth", action="store_true")
    rth.add_argument("--no-rth", action="store_true")

    p.add_argument("--symbols", nargs="+", default=None, help="Equity symbols (e.g. SPY QQQ)")

    p.add_argument("--roots", nargs="+", default=None, help="Futures roots (e.g. NQ ES)")
    p.add_argument("--expiry", default=None, help="Futures expiry YYYYMM (e.g. 202606)")
    p.add_argument("--auto-expiries", action="store_true")
    p.add_argument(
        "--active-only",
        action="store_true",
        help="(Futures + --auto-expiries) download each contract only for its active window.",
    )
    p.add_argument("--roll-buffer-days", type=int, default=0, help="Extend active window by N days on both sides.")

    args = p.parse_args(argv)
    return args


def connect_ib(host: str, port: int, client_id: int, timeout: float) -> tuple[IB, int]:
    last_err: Exception | None = None
    for cid in range(client_id, client_id + 20):
        ib = IB()
        try:
            ib.connect(host, port, clientId=cid, timeout=timeout, readonly=True)
            if ib.isConnected():
                print(f"CONNECTED host={host} port={port} client_id={cid}", flush=True)
                return ib, cid
        except Exception as e:  # noqa: BLE001 (keep simple)
            last_err = e
            try:
                ib.disconnect()
            except Exception:
                pass
            continue

    msg = (
        "Failed to connect to IBKR. Make sure IB Gateway/TWS is running, API socket is enabled, "
        "paper port is usually 4002, and client IDs are free."
    )
    if last_err is not None:
        msg += f" Last error: {last_err}"
    raise RuntimeError(msg)


def ensure_ib_connected(ib: IB, host: str, port: int, client_id: int, timeout: float) -> None:
    if ib.isConnected():
        return
    print("WARN IB disconnected; reconnecting...", flush=True)
    try:
        ib.disconnect()
    except Exception:
        pass
    ib.connect(host, port, clientId=client_id, timeout=timeout, readonly=True)


def parse_ny_date_bounds(start_ymd: str, end_ymd: str) -> DateBounds:
    start_ny = pd.Timestamp(start_ymd).tz_localize(NY_TZ)
    end_ny = pd.Timestamp(end_ymd).tz_localize(NY_TZ)
    end_ny_inclusive = end_ny + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)

    start_utc = start_ny.tz_convert(UTC_TZ)
    end_utc_inclusive = end_ny_inclusive.tz_convert(UTC_TZ)

    if end_utc_inclusive < start_utc:
        raise ValueError("--end must be >= --start")

    return DateBounds(
        start_ny=start_ny,
        end_ny_inclusive=end_ny_inclusive,
        start_utc=start_utc,
        end_utc_inclusive=end_utc_inclusive,
    )


def iter_ny_chunks(bounds: DateBounds, chunk_days: int) -> Iterable[tuple[pd.Timestamp, pd.Timestamp, int]]:
    """
    Yield (chunk_start_ny, chunk_end_ny_inclusive, dur_days).

    We request each chunk with endDateTime in UTC and durationStr in days.
    """
    if chunk_days <= 0:
        raise ValueError("--chunk-days must be > 0")

    cur = bounds.start_ny
    end_day = bounds.end_ny_inclusive.floor("D")
    while cur.floor("D") <= end_day:
        chunk_end_day = min(cur.floor("D") + pd.Timedelta(days=chunk_days - 1), end_day)
        chunk_end_ny_inclusive = chunk_end_day + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
        dur_days = int((chunk_end_day - cur.floor("D")).days + 1)
        yield cur, min(chunk_end_ny_inclusive, bounds.end_ny_inclusive), dur_days
        cur = (chunk_end_day + pd.Timedelta(days=1)).tz_localize(None).tz_localize(NY_TZ)


def bars_to_canonical_df(
    bars,
    *,
    asset: Asset,
    use_rth: bool,
    bar_size: str,
    symbol: str | None = None,
    root: str | None = None,
    contract: str | None = None,
    expiry: str | None = None,
) -> pd.DataFrame:
    if not bars:
        return pd.DataFrame()

    raw = util.df(bars)
    if raw.empty:
        return raw

    if "date" not in raw.columns:
        raise RuntimeError("Unexpected IBKR bars DataFrame: missing 'date' column")

    ts_utc = pd.to_datetime(raw["date"], utc=True)
    ts_ny = ts_utc.dt.tz_convert(NY_TZ)

    df = pd.DataFrame(
        {
            "ts_utc": ts_utc,
            "ts_ny": ts_ny,
            "asset": asset,
            "source": "ibkr",
            "bar_size": bar_size,
            "useRTH": bool(use_rth),
            "open": raw.get("open"),
            "high": raw.get("high"),
            "low": raw.get("low"),
            "close": raw.get("close"),
            "volume": raw.get("volume"),
            "average": raw.get("average", pd.NA),
            "barCount": raw.get("barCount", pd.NA),
        }
    )

    if asset == "equity":
        df["symbol"] = symbol
    else:
        df["root"] = root
        df["contract"] = contract
        df["expiry"] = expiry

    df = df.sort_values("ts_utc").reset_index(drop=True)

    if asset == "equity":
        df = df.drop_duplicates(subset=["symbol", "ts_utc"])
    else:
        df = df.drop_duplicates(subset=["root", "contract", "ts_utc"])

    return df.reset_index(drop=True)


def atomic_write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp.{uuid.uuid4().hex}.parquet")
    try:
        df.to_parquet(tmp, index=False)
        os.replace(tmp, path)
    finally:
        try:
            if tmp.exists():
                tmp.unlink()
        except Exception:
            pass


def month_partitions(df: pd.DataFrame) -> Iterable[tuple[int, int, pd.DataFrame]]:
    ts = pd.to_datetime(df["ts_utc"], utc=True)
    for (y, m), idx in df.groupby([ts.dt.year, ts.dt.month]).groups.items():
        yield int(y), int(m), df.loc[idx].copy()


def merge_and_write_partition(df_new: pd.DataFrame, path: Path, *, asset: Asset) -> int:
    if df_new.empty:
        return 0

    if path.exists():
        df_old = pd.read_parquet(path)
        df_old["ts_utc"] = pd.to_datetime(df_old["ts_utc"], utc=True)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new.copy()

    if asset == "equity":
        dedupe_key = ["symbol", "ts_utc"]
    else:
        dedupe_key = ["root", "contract", "ts_utc"]

    df["ts_utc"] = pd.to_datetime(df["ts_utc"], utc=True)
    df = df.drop_duplicates(subset=dedupe_key).sort_values("ts_utc").reset_index(drop=True)

    atomic_write_parquet(df, path)
    print(f"WROTE {path.as_posix()} rows={len(df)}", flush=True)
    return int(len(df_new))


def write_monthly_partitions_equity(df: pd.DataFrame, symbol: str) -> int:
    base = Path("data/raw/ibkr/equity/bars_1min") / f"symbol={symbol}"
    written = 0
    for y, m, part in month_partitions(df):
        path = base / f"year={y}" / f"month={m:02d}" / "data.parquet"
        written += merge_and_write_partition(part, path, asset="equity")
    return written


def write_monthly_partitions_futures(df: pd.DataFrame, root: str, contract: str) -> int:
    base = Path("data/raw/ibkr/futures/bars_1min") / f"root={root}" / f"contract={contract}"
    written = 0
    for y, m, part in month_partitions(df):
        path = base / f"year={y}" / f"month={m:02d}" / "data.parquet"
        written += merge_and_write_partition(part, path, asset="futures")
    return written


def quarterly_expiries(start_ny: pd.Timestamp, end_ny_inclusive: pd.Timestamp) -> list[str]:
    """
    Generate quarterly YYYYMM from the quarter containing start through the quarter after end.
    Quarter months: 03, 06, 09, 12
    """

    def q_end_month(m: int) -> int:
        if m <= 3:
            return 3
        if m <= 6:
            return 6
        if m <= 9:
            return 9
        return 12

    start_y = int(start_ny.year)
    start_m = q_end_month(int(start_ny.month))

    # quarter containing end, then include one quarter after
    end_y = int(end_ny_inclusive.year)
    end_m = q_end_month(int(end_ny_inclusive.month))

    # add one quarter after
    end_m_plus = end_m + 3
    end_y_plus = end_y
    if end_m_plus > 12:
        end_m_plus -= 12
        end_y_plus += 1

    expiries: list[str] = []
    y, m = start_y, start_m
    while (y < end_y_plus) or (y == end_y_plus and m <= end_m_plus):
        expiries.append(f"{y}{m:02d}")
        m += 3
        if m > 12:
            m -= 12
            y += 1
    return expiries


def third_friday(year: int, month: int) -> date:
    # Find the first Friday, then advance 2 weeks.
    d = date(year, month, 1)
    # weekday: Mon=0..Sun=6, Friday=4
    offset = (4 - d.weekday()) % 7
    first_friday = d + timedelta(days=offset)
    return first_friday + timedelta(days=14)


def roll_date_for_expiry(expiry: str) -> pd.Timestamp:
    """
    Roll date is the Monday before the third Friday of the expiry month,
    at midnight America/New_York.
    """
    expiry = str(expiry)
    if len(expiry) != 6:
        raise ValueError(f"Bad expiry YYYYMM: {expiry}")
    y = int(expiry[:4])
    m = int(expiry[4:6])
    tf = third_friday(y, m)
    roll = tf - timedelta(days=4)  # Friday -> Monday
    return pd.Timestamp(roll).tz_localize(NY_TZ)


def next_quarter_expiry(expiry: str) -> str:
    expiry = str(expiry)
    y = int(expiry[:4])
    m = int(expiry[4:6])
    m += 3
    if m > 12:
        m -= 12
        y += 1
    return f"{y}{m:02d}"


@dataclass(frozen=True)
class ActivePlanItem:
    expiry: str
    interval_start_ny: pd.Timestamp
    interval_end_ny_inclusive: pd.Timestamp


def build_active_futures_plan(
    start_ny: pd.Timestamp, end_ny_inclusive: pd.Timestamp, *, roll_buffer_days: int = 0
) -> list[ActivePlanItem]:
    """
    Build (expiry -> active interval) plan using roll dates:
      - expiry YYYYMM is active until roll_date(expiry)
      - switches to next quarterly contract at roll_date(expiry)
    We generate expiries from quarter containing start through quarter after end,
    then assign intervals and cap to requested range (optionally buffered).
    """
    expiries = quarterly_expiries(start_ny, end_ny_inclusive)
    if not expiries:
        return []

    # Use roll dates of each expiry to determine boundaries.
    roll_dates = {e: roll_date_for_expiry(e) for e in expiries}

    cap_start = start_ny - pd.Timedelta(days=int(roll_buffer_days))
    cap_end = end_ny_inclusive + pd.Timedelta(days=int(roll_buffer_days))

    items: list[ActivePlanItem] = []
    for idx, expiry in enumerate(expiries):
        if idx == 0:
            interval_start = start_ny
        else:
            interval_start = roll_dates[expiries[idx - 1]]

        # End at this expiry's roll date - 1us, unless it's beyond requested end.
        interval_end = roll_dates[expiry] - pd.Timedelta(microseconds=1)
        interval_end = min(interval_end, end_ny_inclusive)

        # Apply buffer (extend interval), then cap.
        if roll_buffer_days and roll_buffer_days > 0:
            interval_start = interval_start - pd.Timedelta(days=int(roll_buffer_days))
            interval_end = interval_end + pd.Timedelta(days=int(roll_buffer_days))

        interval_start = max(interval_start, cap_start)
        interval_end = min(interval_end, cap_end)

        if interval_end < interval_start:
            continue
        items.append(
            ActivePlanItem(
                expiry=str(expiry),
                interval_start_ny=interval_start,
                interval_end_ny_inclusive=interval_end,
            )
        )

    # Drop trailing plan items that start after requested end.
    items = [it for it in items if it.interval_start_ny <= end_ny_inclusive]
    return items


def infer_use_rth(asset: Asset, args: argparse.Namespace) -> bool:
    if args.rth:
        return True
    if args.no_rth:
        return False
    return True if asset == "equity" else False


def validate_args(args: argparse.Namespace) -> None:
    asset: Asset = args.asset
    if asset == "equity":
        if not args.symbols:
            raise ValueError("asset=equity requires --symbols")
    if asset == "futures":
        if not args.roots:
            raise ValueError("asset=futures requires --roots")
        if not args.expiry and not args.auto_expiries:
            raise ValueError("asset=futures requires either --expiry or --auto-expiries")
        if args.active_only and not args.auto_expiries:
            raise ValueError("--active-only requires --auto-expiries")


def qualify_or_warn(
    ib: IB,
    contract,
    label: str,
    *,
    host: str,
    port: int,
    client_id: int,
    timeout: float,
) -> object | None:
    for attempt in range(2):
        ensure_ib_connected(ib, host, port, client_id, timeout)
        qualified = ib.qualifyContracts(contract)
        if qualified:
            return qualified[0]
        if attempt == 0:
            print(f"WARN qualify retry after reconnect: {label}", flush=True)
            try:
                ib.disconnect()
            except Exception:
                pass
            time.sleep(max(0.0, 1.0))
            ib.connect(host, port, clientId=client_id, timeout=timeout, readonly=True)
    print(f"WARN could not qualify: {label}", flush=True)
    return None


def download_for_label(
    ib: IB,
    *,
    contract,
    asset: Asset,
    label: str,
    bounds: DateBounds,
    use_rth: bool,
    chunk_days: int,
    sleep_s: float,
    what: str,
    bar_size: str,
    host: str,
    port: int,
    client_id: int,
    connect_timeout: float,
    symbol: str | None = None,
    root: str | None = None,
    contract_name: str | None = None,
    expiry: str | None = None,
    per_chunk_write: object | None = None,
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    chunks = list(iter_ny_chunks(bounds, chunk_days))
    n = len(chunks)

    for i, (chunk_start_ny, chunk_end_ny_inclusive, dur_days) in enumerate(chunks, start=1):
        ensure_ib_connected(ib, host, port, client_id, connect_timeout)
        end_dt_utc = chunk_end_ny_inclusive.tz_convert(UTC_TZ).to_pydatetime()
        duration = f"{dur_days} D"
        print(
            f"[{asset}] {label} chunk {i}/{n} "
            f"start={chunk_start_ny.isoformat()} end={chunk_end_ny_inclusive.isoformat()} "
            f"duration={duration} useRTH={use_rth}",
            flush=True,
        )

        bars = None
        for attempt in range(2):
            try:
                bars = ib.reqHistoricalData(
                    contract=contract,
                    endDateTime=end_dt_utc,
                    durationStr=duration,
                    barSizeSetting=bar_size,
                    whatToShow=what,
                    useRTH=use_rth,
                    keepUpToDate=False,
                    formatDate=2,
                )
                break
            except Exception as e:  # noqa: BLE001
                print(f"ERROR request failed for {label} chunk {i}/{n} (try {attempt + 1}/2): {e}", flush=True)
                ensure_ib_connected(ib, host, port, client_id, connect_timeout)
                time.sleep(max(0.0, sleep_s))
        if bars is None:
            continue

        if not bars:
            print(f"WARN no bars returned for {label} chunk {i}/{n}", flush=True)
            time.sleep(max(0.0, sleep_s))
            continue

        df = bars_to_canonical_df(
            bars,
            asset=asset,
            use_rth=use_rth,
            bar_size=bar_size,
            symbol=symbol,
            root=root,
            contract=contract_name,
            expiry=expiry,
        )
        print(f"[{asset}] {label} chunk {i}/{n} rows={len(df)}", flush=True)
        if not df.empty:
            # Filter to requested bounds and optionally write immediately.
            df = df[(df["ts_utc"] >= bounds.start_utc) & (df["ts_utc"] <= bounds.end_utc_inclusive)].reset_index(
                drop=True
            )
            frames.append(df)
            if per_chunk_write is not None and not df.empty:
                try:
                    per_chunk_write(df)
                except Exception as e:  # noqa: BLE001
                    print(f"ERROR write failed for {label} chunk {i}/{n}: {e}", flush=True)

        time.sleep(max(0.0, sleep_s))

    if not frames:
        return pd.DataFrame()

    out = pd.concat(frames, ignore_index=True)
    out["ts_utc"] = pd.to_datetime(out["ts_utc"], utc=True)
    out = out.sort_values("ts_utc").reset_index(drop=True)

    # Filter to the full requested UTC inclusive window.
    out = out[(out["ts_utc"] >= bounds.start_utc) & (out["ts_utc"] <= bounds.end_utc_inclusive)].reset_index(drop=True)

    # Dedupe again after concat
    if asset == "equity":
        out = out.drop_duplicates(subset=["symbol", "ts_utc"]).sort_values("ts_utc").reset_index(drop=True)
    else:
        out = out.drop_duplicates(subset=["root", "contract", "ts_utc"]).sort_values("ts_utc").reset_index(drop=True)

    return out


def bounds_from_ny_interval(start_ny: pd.Timestamp, end_ny_inclusive: pd.Timestamp) -> DateBounds:
    start_ny = pd.Timestamp(start_ny).tz_convert(NY_TZ)
    end_ny_inclusive = pd.Timestamp(end_ny_inclusive).tz_convert(NY_TZ)
    return DateBounds(
        start_ny=start_ny,
        end_ny_inclusive=end_ny_inclusive,
        start_utc=start_ny.tz_convert(UTC_TZ),
        end_utc_inclusive=end_ny_inclusive.tz_convert(UTC_TZ),
    )


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        validate_args(args)
    except Exception as e:
        print(f"ERROR {e}", file=sys.stderr)
        return 2

    asset: Asset = args.asset
    use_rth = infer_use_rth(asset, args)
    bounds = parse_ny_date_bounds(args.start, args.end)

    ib, used_client_id = connect_ib(args.host, int(args.port), int(args.client_id), float(args.connect_timeout))
    conn_host = str(args.host)
    conn_port = int(args.port)
    conn_timeout = float(args.connect_timeout)

    attempted = 0
    written_labels = 0
    total_rows_written = 0

    try:
        if asset == "equity":
            for sym in (args.symbols or []):
                symbol = sym.upper().strip()
                attempted += 1
                c = Stock(symbol, "SMART", "USD")
                q = qualify_or_warn(
                    ib,
                    c,
                    label=f"equity:{symbol}",
                    host=conn_host,
                    port=conn_port,
                    client_id=used_client_id,
                    timeout=conn_timeout,
                )
                if q is None:
                    continue

                label = symbol
                df = download_for_label(
                    ib,
                    contract=c,
                    asset="equity",
                    label=label,
                    bounds=bounds,
                    use_rth=use_rth,
                    chunk_days=int(args.chunk_days),
                    sleep_s=float(args.sleep),
                    what=str(args.what),
                    bar_size=str(args.bar_size),
                    host=conn_host,
                    port=conn_port,
                    client_id=used_client_id,
                    connect_timeout=conn_timeout,
                    symbol=symbol,
                    per_chunk_write=lambda part, s=symbol: write_monthly_partitions_equity(part, symbol=s),
                )

                if df.empty:
                    print(f"WARN no data for {label} in requested range", flush=True)
                    continue

                total_rows_written += int(len(df))
                written_labels += 1

        else:
            if args.auto_expiries and args.active_only:
                plan = build_active_futures_plan(
                    bounds.start_ny,
                    bounds.end_ny_inclusive,
                    roll_buffer_days=int(args.roll_buffer_days),
                )
                if not plan:
                    print("WARN active futures plan is empty", flush=True)
            else:
                plan = []
                expiries: list[str]
                if args.auto_expiries:
                    expiries = quarterly_expiries(bounds.start_ny, bounds.end_ny_inclusive)
                else:
                    expiries = [str(args.expiry)]
                for e in expiries:
                    plan.append(
                        ActivePlanItem(
                            expiry=str(e),
                            interval_start_ny=bounds.start_ny,
                            interval_end_ny_inclusive=bounds.end_ny_inclusive,
                        )
                    )

            for r in (args.roots or []):
                root = r.upper().strip()
                if args.auto_expiries and args.active_only:
                    for it in plan:
                        print(
                            f"root={root} expiry={it.expiry} active_start={it.interval_start_ny.isoformat()} "
                            f"active_end={it.interval_end_ny_inclusive.isoformat()}",
                            flush=True,
                        )

                for it in plan:
                    attempted += 1
                    c = Future(
                        symbol=root,
                        lastTradeDateOrContractMonth=str(it.expiry),
                        exchange="CME",
                        currency="USD",
                        includeExpired=True,
                    )
                    q = qualify_or_warn(
                        ib,
                        c,
                        label=f"futures:{root}:{it.expiry}",
                        host=conn_host,
                        port=conn_port,
                        client_id=used_client_id,
                        timeout=conn_timeout,
                    )
                    if q is None:
                        continue

                    local = getattr(q, "localSymbol", None)
                    contract_name = (
                        str(local).strip() if isinstance(local, str) and local.strip() else f"{root}{it.expiry}"
                    )

                    label = f"{root}:{contract_name}"
                    df = download_for_label(
                        ib,
                        contract=c,
                        asset="futures",
                        label=label,
                        bounds=bounds_from_ny_interval(it.interval_start_ny, it.interval_end_ny_inclusive),
                        use_rth=use_rth,
                        chunk_days=int(args.chunk_days),
                        sleep_s=float(args.sleep),
                        what=str(args.what),
                        bar_size=str(args.bar_size),
                        host=conn_host,
                        port=conn_port,
                        client_id=used_client_id,
                        connect_timeout=conn_timeout,
                        root=root,
                        contract_name=contract_name,
                        expiry=str(it.expiry),
                        per_chunk_write=lambda part, r=root, cn=contract_name: write_monthly_partitions_futures(
                            part, root=r, contract=cn
                        ),
                    )

                    if df.empty:
                        print(f"WARN no data for {label} in requested range", flush=True)
                        continue

                    total_rows_written += int(len(df))
                    written_labels += 1

    finally:
        try:
            ib.disconnect()
        except Exception:
            pass

    print(
        f"SUMMARY attempted={attempted} written={written_labels} total_rows_written={total_rows_written}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

