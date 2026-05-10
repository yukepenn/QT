"""Sanity-check Layer 1 candidate YAMLs: fast context + signal arrays on a bar window."""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.features.feature_store import FeatureStore
from src.strategies.loader import load_strategy


def _check_one(
    ypath: Path,
    *,
    store: FeatureStore,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "candidate_yaml": str(ypath.name),
        "strategy": "",
        "candidate_id": "",
        "status": "",
        "detail": "",
        "n_bars": "",
        "array_len": "",
    }
    try:
        with ypath.open(encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        if not isinstance(doc, dict):
            row["status"] = "invalid_yaml"
            row["detail"] = "not_a_dict"
            return row
        strategy = str(doc.get("strategy", "")).strip()
        cid = str(doc.get("candidate_id", "")).strip()
        cfg = doc.get("config")
        row["strategy"] = strategy
        row["candidate_id"] = cid
        if not strategy or not isinstance(cfg, dict):
            row["status"] = "missing_strategy_or_config"
            return row

        strat = load_strategy(strategy)
        feat = store.get_features(cfg)
        n = len(feat)
        row["n_bars"] = n
        ctx = strat.prepare_signal_context(feat, cfg)
        arrs = strat.generate_signal_arrays_from_context(ctx, cfg)
        if not isinstance(arrs, dict) or not arrs:
            row["status"] = "empty_arrays"
            return row
        lens = {k: len(v) for k, v in arrs.items() if hasattr(v, "__len__")}
        if not lens:
            row["status"] = "no_array_values"
            return row
        L = next(iter(lens.values()))
        if any(l != L for l in lens.values()):
            row["status"] = "length_mismatch"
            row["detail"] = str(lens)
            return row
        if L != n:
            row["status"] = "len_neq_bars"
            row["array_len"] = L
            row["detail"] = f"bars={n} arrays={L}"
            return row
        # finite smoke on first non-zero signal slice if present
        for k in ("sig_valid", "side"):
            v = arrs.get(k)
            if v is None:
                continue
            a = np.asarray(v)
            if a.size and not np.all(np.isfinite(a.astype(float, copy=False))):
                row["status"] = "non_finite_array"
                row["detail"] = k
                return row
        row["status"] = "ok"
        row["array_len"] = L
    except Exception as e:
        row["status"] = "exception"
        row["detail"] = f"{type(e).__name__}: {e}"
    return row


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Fast-context check for selected candidate YAMLs.")
    p.add_argument("--candidate-root", type=Path, required=True)
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--out-csv", type=Path, default=None)
    p.add_argument("--out-md", type=Path, default=None)
    args = p.parse_args(argv)

    root = args.candidate_root
    if not root.is_absolute():
        root = Path.cwd() / root
    sel = root / "selected_candidates" if (root / "selected_candidates").is_dir() else root
    yamls = sorted(sel.glob("*.yaml"))
    if not yamls:
        print(f"ERROR no YAML under {sel}", file=sys.stderr)
        return 2

    store = FeatureStore(asset=args.asset, symbol=args.symbol.upper(), start=args.start, end=args.end)
    rows = [_check_one(yp, store=store) for yp in yamls]

    bad = [r for r in rows if r.get("status") != "ok"]
    for r in rows:
        print(f"{r.get('candidate_id','')} {r.get('strategy','')} -> {r.get('status')}", flush=True)

    out_csv = args.out_csv
    out_md = args.out_md
    if out_csv:
        if not out_csv.is_absolute():
            out_csv = Path.cwd() / out_csv
        out_csv.parent.mkdir(parents=True, exist_ok=True)
        fields = list(rows[0].keys()) if rows else []
        with out_csv.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        print(f"Wrote {out_csv}", flush=True)
    if out_md:
        if not out_md.is_absolute():
            out_md = Path.cwd() / out_md
        out_md.parent.mkdir(parents=True, exist_ok=True)
        lines = ["# Candidate fast-context check", ""]
        lines.append("| candidate_id | strategy | status | detail |")
        lines.append("|--------------|----------|--------|--------|")
        for r in rows:
            lines.append(
                f"| {r.get('candidate_id','')} | {r.get('strategy','')} | {r.get('status','')} | {r.get('detail','')} |"
            )
        out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {out_md}", flush=True)

    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())
