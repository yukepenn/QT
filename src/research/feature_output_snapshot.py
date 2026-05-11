"""Compact snapshot stats/hashes for feature columns (no full frame commit)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config


def _col_digest(s: pd.Series) -> dict[str, object]:
    v = pd.to_numeric(s, errors="coerce").to_numpy(dtype=np.float64, copy=False)
    finite = np.isfinite(v)
    if not finite.any():
        return {
            "n_nan": int(np.sum(~finite)),
            "n_finite": 0,
            "sum": None,
            "mean": None,
            "std": None,
            "first": None,
            "last": None,
        }
    vf = v[finite]
    return {
        "n_nan": int(np.sum(~finite)),
        "n_finite": int(vf.size),
        "sum": float(np.nansum(vf)),
        "mean": float(np.nanmean(vf)),
        "std": float(np.nanstd(vf)),
        "first": float(vf[0]),
        "last": float(vf[-1]),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--config", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument(
        "--max-cols",
        type=int,
        default=120,
        help="Cap columns listed in detail CSV (sorted by name).",
    )
    args = p.parse_args(argv)

    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root
    out_root.mkdir(parents=True, exist_ok=True)

    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if not isinstance(cfg, dict):
        print("ERROR bad yaml", file=sys.stderr)
        return 2

    raw = read_bars(
        asset=args.asset,
        symbol=args.symbol.upper(),
        start=args.start,
        end=args.end,
    )
    feat = build_features_from_config(raw, cfg).sort_values("ts_utc", ignore_index=True)

    cols = sorted(feat.columns.astype(str).tolist())
    col_rows = []
    blob_parts: list[str] = []
    for c in cols[: int(args.max_cols)]:
        dig = _col_digest(feat[c])
        col_rows.append({"column": c, **dig})
        blob_parts.append(json.dumps({"c": c, **dig}, sort_keys=True))

    summary = {
        "config": str(args.config.resolve()),
        "rows": int(len(feat)),
        "total_columns": len(cols),
        "ts_utc_sorted": bool(feat["ts_utc"].is_monotonic_increasing)
        if "ts_utc" in feat.columns
        else None,
        "columns_digest_sha256": hashlib.sha256(
            "\n".join(blob_parts).encode("utf-8")
        ).hexdigest(),
    }

    (out_root / "feature_snapshot_summary.csv").write_text(
        pd.DataFrame([summary]).to_csv(index=False),
        encoding="utf-8",
    )
    pd.DataFrame(col_rows).to_csv(out_root / "feature_snapshot_columns.csv", index=False)
    (out_root / "feature_snapshot_hash.json").write_text(
        json.dumps(
            {
                "summary": summary,
                "column_names_sha256": hashlib.sha256(
                    "\n".join(cols).encode("utf-8")
                ).hexdigest(),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"Wrote under {out_root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
