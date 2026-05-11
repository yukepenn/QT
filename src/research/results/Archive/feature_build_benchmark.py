"""Benchmark build_features_from_config wall time and pandas warnings."""

from __future__ import annotations

import argparse
import statistics
import sys
import time
import warnings
from pathlib import Path

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config


def _count_frag(warns: list[warnings.WarningMessage]) -> int:
    n = 0
    for w in warns:
        msg = str(w.message)
        if "DataFrame is highly fragmented" in msg or "highly fragmented" in msg:
            n += 1
    return n


def _bench_one(
    raw: pd.DataFrame,
    cfg: dict,
    *,
    repeat: int,
) -> tuple[list[float], int, int, int, int]:
    times: list[float] = []
    frag_max = 0
    warn_max = 0
    rows = len(raw)
    cols_final = 0
    for _ in range(repeat):
        with warnings.catch_warnings(record=True) as wrec:
            warnings.simplefilter("always")
            t0 = time.perf_counter()
            feat = build_features_from_config(raw, cfg)
            elapsed = time.perf_counter() - t0
        times.append(elapsed)
        frag_max = max(frag_max, _count_frag(list(wrec)))
        warn_max = max(warn_max, len(wrec))
        cols_final = feat.shape[1]
    return times, frag_max, warn_max, rows, cols_final


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument(
        "--configs",
        nargs="+",
        type=Path,
        required=True,
        help="Strategy parameter YAML paths",
    )
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--repeat", type=int, default=3)
    args = p.parse_args(argv)

    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    raw = read_bars(
        asset=args.asset,
        symbol=args.symbol.upper(),
        start=args.start,
        end=args.end,
    )
    if raw.empty:
        print("ERROR read_bars returned empty", file=sys.stderr)
        return 2

    rows: list[dict[str, object]] = []
    for cfg_path in args.configs:
        cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        if not isinstance(cfg, dict):
            print(f"ERROR bad yaml {cfg_path}", file=sys.stderr)
            return 2
        times, frag_n, warn_n, n_rows, n_cols = _bench_one(
            raw, cfg, repeat=int(args.repeat)
        )
        rows.append(
            {
                "config": str(cfg_path.as_posix()),
                "rows": n_rows,
                "final_column_count": n_cols,
                "wall_sec_mean": round(statistics.mean(times), 4),
                "wall_sec_min": round(min(times), 4),
                "wall_sec_max": round(max(times), 4),
                "warnings_count": warn_n,
                "fragmentation_warnings_count": frag_n,
                "notes": f"repeat={args.repeat}",
            }
        )

    csv_path = out_root / "feature_build_benchmark.csv"
    md_path = out_root / "feature_build_benchmark.md"
    pdf = pd.DataFrame(rows)
    pdf.to_csv(csv_path, index=False)

    lines = [
        "# Feature build benchmark",
        "",
        f"- asset={args.asset} symbol={args.symbol} window={args.start}..{args.end}",
        f"- repeat={args.repeat}",
        "",
        "| config | rows | cols | mean_s | min_s | max_s | warns | frag |",
        "|--------|------|------|--------|-------|-------|-------|------|",
    ]
    for r in rows:
        lines.append(
            f"| `{Path(str(r['config'])).name}` | {r['rows']} | {r['final_column_count']} | "
            f"{r['wall_sec_mean']} | {r['wall_sec_min']} | {r['wall_sec_max']} | "
            f"{r['warnings_count']} | {r['fragmentation_warnings_count']} |"
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {csv_path}", flush=True)
    print(f"Wrote {md_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
