"""Summarize local equity 1-min parquet coverage (read_bars + session stats)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.read_bars import read_bars

NY_TZ = "America/New_York"


def _expected_months(start: str, end: str) -> list[tuple[int, int]]:
    s = pd.Timestamp(start).tz_localize(NY_TZ)
    e = pd.Timestamp(end).tz_localize(NY_TZ)
    y, m = int(s.year), int(s.month)
    y_end, m_end = int(e.year), int(e.month)
    out: list[tuple[int, int]] = []
    while (y < y_end) or (y == y_end and m <= m_end):
        out.append((y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1
    return out


def _parquet_month_files(symbol: str, data_dir: Path) -> tuple[int, list[tuple[int, int]]]:
    base = data_dir / "equity" / "bars_1min" / f"symbol={symbol.upper()}"
    if not base.is_dir():
        return 0, []
    paths = list(base.rglob("data.parquet"))
    months: set[tuple[int, int]] = set()
    for p in paths:
        try:
            rel = p.relative_to(base)
            parts = rel.parts
            y = int(parts[0].split("=")[1])
            mo = int(parts[1].split("=")[1])
            months.add((y, mo))
        except (IndexError, ValueError):
            continue
    return len(paths), sorted(months)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Equity bar coverage report for IBKR parquet layout.")
    p.add_argument("--symbols", nargs="+", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--data-dir", type=Path, default=Path("data/raw/ibkr"))
    p.add_argument("--output-dir", type=Path, required=True)
    args = p.parse_args(argv)

    cwd = Path.cwd()
    data_dir = args.data_dir if args.data_dir.is_absolute() else cwd / args.data_dir
    out_dir = args.output_dir if args.output_dir.is_absolute() else cwd / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    expected = _expected_months(args.start, args.end)
    rows_out: list[dict] = []
    md_lines = [
        "# Equity data coverage",
        "",
        f"- Range: **{args.start}** — **{args.end}** (NY calendar months for file check)",
        f"- Data dir: `{data_dir.as_posix()}`",
        "",
    ]

    for sym in args.symbols:
        symbol = sym.upper().strip()
        df = read_bars(
            asset="equity",
            symbol=symbol,
            start=args.start,
            end=args.end,
            data_dir=data_dir,
        )
        n_files, months_have = _parquet_month_files(symbol, data_dir)
        months_set = set(months_have)
        missing_m = [f"{y}-{m:02d}" for y, m in expected if (y, m) not in months_set]

        dup_ct = 0
        low_row_sessions: list[tuple] = []
        high_row_sessions: list[tuple] = []
        n_sessions = 0
        min_ny = max_ny = None
        if not df.empty:
            dup_ct = int(df.attrs.get("_duplicates_dropped", 0))
            d = df["ts_ny"].dt.normalize().dt.date
            vc = d.value_counts()
            n_sessions = int(len(vc))
            for day, cnt in vc.items():
                if cnt < 300:
                    low_row_sessions.append((str(day), int(cnt)))
                if cnt > 400:
                    high_row_sessions.append((str(day), int(cnt)))
            low_row_sessions.sort(key=lambda x: x[0])
            high_row_sessions.sort(key=lambda x: x[0])
            min_ny = df["ts_ny"].min()
            max_ny = df["ts_ny"].max()

        rows_out.append(
            {
                "symbol": symbol,
                "rows": len(df),
                "min_ts_utc": df["ts_utc"].min().isoformat() if len(df) else "",
                "max_ts_utc": df["ts_utc"].max().isoformat() if len(df) else "",
                "min_ts_ny": min_ny.isoformat() if min_ny is not None else "",
                "max_ts_ny": max_ny.isoformat() if max_ny is not None else "",
                "unique_session_dates": n_sessions,
                "duplicate_ts_dropped_by_read_bars": dup_ct,
                "monthly_parquet_files": n_files,
                "months_with_parquet": len(months_set),
                "expected_months": len(expected),
                "missing_months_count": len(missing_m),
                "low_row_sessions_lt_300": sum(1 for _ in low_row_sessions),
                "high_row_sessions_gt_400": sum(1 for _ in high_row_sessions),
                "first_20_low_row_sessions": str(low_row_sessions[:20]),
                "last_20_low_row_sessions": str(low_row_sessions[-20:]),
                "missing_months_sample": "; ".join(missing_m[:24]) + ("; ..." if len(missing_m) > 24 else ""),
            }
        )

        md_lines.extend(
            [
                f"## {symbol}",
                "",
                f"- **rows:** {len(df)}",
                f"- **min_ts_ny / max_ts_ny:** {rows_out[-1]['min_ts_ny']} → {rows_out[-1]['max_ts_ny']}",
                f"- **unique_session_dates:** {n_sessions}",
                f"- **duplicate_ts dropped (read_bars):** {dup_ct}",
                f"- **monthly parquet files:** {n_files} ({len(months_set)} distinct year/month)",
                f"- **missing months (no parquet dir):** {len(missing_m)}",
                f"- **sessions with row_count < 300:** {rows_out[-1]['low_row_sessions_lt_300']}",
                f"- **sessions with row_count > 400:** {rows_out[-1]['high_row_sessions_gt_400']}",
                "",
                "**First 20 low-row sessions:**",
                "",
                "```",
                str(low_row_sessions[:20]),
                "```",
                "",
                "**Last 20 low-row sessions:**",
                "",
                "```",
                str(low_row_sessions[-20:]),
                "```",
                "",
            ]
        )
        if missing_m:
            md_lines.append(f"**Missing months (sample):** {', '.join(missing_m[:36])}")
            md_lines.append("")

    csv_path = out_dir / "data_coverage.csv"
    pd.DataFrame(rows_out).to_csv(csv_path, index=False)
    (out_dir / "data_coverage_summary.md").write_text("\n".join(md_lines), encoding="utf-8")
    print(f"Wrote {csv_path}", flush=True)
    print(f"Wrote {out_dir / 'data_coverage_summary.md'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
