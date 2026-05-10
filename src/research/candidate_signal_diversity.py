"""Candidate signal diversity: fingerprint precomputed signal paths per Layer-1 YAML."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.features.feature_key import feature_key_from_config
from src.features.feature_store import FeatureStore
from src.strategies.loader import apply_overrides, load_strategy, load_strategy_config


def _short(obj: Any, n: int = 240) -> str:
    s = json.dumps(obj, sort_keys=True, default=str)
    return s if len(s) <= n else s[: n - 3] + "..."


def _round6(x: float) -> float:
    if not math.isfinite(float(x)):
        return float("nan")
    return round(float(x), 6)


def pure_signal_hash_entries(entries: list[tuple[str, int]]) -> str:
    """Hash (ts_iso_utc, side) tuples in bar order (precomputed valid signals)."""
    blob = "|".join(f"{ts}:{side}" for ts, side in entries).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def signal_fingerprint_entries(
    entries: list[tuple[str, int, float, float, float]],
) -> str:
    """Hash timestamps, side, rounded stop/target_preview/target_r."""
    parts = []
    for ts, side, st, tg, tr in entries:
        parts.append(f"{ts}:{side}:{_round6(st)}:{_round6(tg)}:{_round6(tr)}")
    blob = "|".join(parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def stop_target_hash_entries(entries: list[tuple[float, float, float]]) -> str:
    blob = "|".join(
        f"{_round6(a)}:{_round6(b)}:{_round6(c)}" for a, b, c in entries
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def reason_hash_stable(strategy: str) -> str:
    blob = f"{strategy}:long_mvp".encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def _behavior_quality(n_sig: int) -> str:
    if n_sig <= 0:
        return "none"
    if n_sig < 10:
        return "sparse"
    if n_sig < 50:
        return "moderate"
    return "strong"


def _mean_gap_minutes(ts: pd.Series) -> float | None:
    if ts.size < 2:
        return None
    d = pd.to_datetime(ts, utc=True).diff().dt.total_seconds() / 60.0
    d = d.iloc[1:]
    if d.empty:
        return None
    return float(d.mean())


def _load_merged_config(doc: dict[str, Any]) -> dict[str, Any]:
    strategy = str(doc.get("strategy", "")).strip()
    if not strategy:
        raise ValueError("missing strategy")
    inner = doc.get("config")
    if not isinstance(inner, dict):
        raise ValueError("missing config dict")
    base = dict(load_strategy_config(strategy))
    return apply_overrides(base, inner)


def _candidate_rows_from_parent(sel_dir: Path) -> dict[str, dict[str, Any]]:
    parent = sel_dir.parent
    csv_path = parent / "selected_candidates.csv"
    if not csv_path.is_file():
        return {}
    df = pd.read_csv(csv_path)
    out: dict[str, dict[str, Any]] = {}
    for _, r in df.iterrows():
        cid = str(r.get("candidate_id", "")).strip()
        if cid:
            out[cid] = {k: r.get(k) for k in df.columns}
    return out


_DIVERSITY_FIELDS = [
    "candidate_yaml",
    "candidate_id",
    "strategy",
    "warning",
    "candidate_rank",
    "candidate_score",
    "n_signals",
    "n_long_signals",
    "n_short_signals",
    "first_signal_ts",
    "last_signal_ts",
    "pure_signal_hash",
    "signal_hash",
    "behavior_hash_quality",
    "stop_target_hash",
    "reason_hash",
    "total_unique_timestamps",
    "mean_gap_minutes",
    "feature_key_short",
    "context_key_short",
    "status",
    "error",
]


def analyze_merged_config(
    strategy: str,
    cfg: dict[str, Any],
    *,
    store: FeatureStore,
) -> dict[str, Any]:
    """Compute signal fingerprints for an already-merged strategy config dict."""
    row: dict[str, Any] = {}
    strat = load_strategy(strategy)
    strat.validate_config(cfg)

    fk = feature_key_from_config(cfg)
    row["feature_key_short"] = _short(fk, 320)
    row["context_key_short"] = _short(strat.context_key(cfg), 320)

    feat = store.get_features(cfg)
    ctx = strat.prepare_signal_context(feat, cfg)
    arr = strat.generate_signal_arrays_from_context(ctx, cfg)
    valid = np.asarray(arr["valid"], dtype=bool)
    side = np.asarray(arr["side"], dtype=np.int8)
    stp = np.asarray(arr["stop"], dtype=np.float64)
    tgtp = np.asarray(arr["target_preview"], dtype=np.float64)
    tr = np.asarray(arr["target_r"], dtype=np.float64)

    ix = np.flatnonzero(valid)
    row["n_signals"] = int(ix.size)
    row["n_long_signals"] = int(np.sum(side[ix] == 1))
    row["n_short_signals"] = int(np.sum(side[ix] == -1))
    ts_all = feat["ts_utc"].iloc[ix]
    row["total_unique_timestamps"] = int(ts_all.nunique())
    if ix.size:
        row["first_signal_ts"] = str(ts_all.min())
        row["last_signal_ts"] = str(ts_all.max())
        mg = _mean_gap_minutes(ts_all)
        row["mean_gap_minutes"] = "" if mg is None else mg
    else:
        row["first_signal_ts"] = ""
        row["last_signal_ts"] = ""
        row["mean_gap_minutes"] = ""
    pure_entries: list[tuple[str, int]] = []
    sig_entries: list[tuple[str, int, float, float, float]] = []
    st_tgt: list[tuple[float, float, float]] = []
    for i in ix:
        tsi = feat["ts_utc"].iloc[int(i)]
        ts_iso = pd.Timestamp(tsi).isoformat()
        si = int(side[int(i)])
        pure_entries.append((ts_iso, si))
        st_tgt.append((float(stp[int(i)]), float(tgtp[int(i)]), float(tr[int(i)])))
        sig_entries.append(
            (
                ts_iso,
                si,
                float(stp[int(i)]),
                float(tgtp[int(i)]),
                float(tr[int(i)]),
            )
        )
    row["pure_signal_hash"] = (
        pure_signal_hash_entries(pure_entries) if pure_entries else ""
    )
    row["signal_hash"] = (
        signal_fingerprint_entries(sig_entries) if sig_entries else ""
    )
    row["stop_target_hash"] = stop_target_hash_entries(st_tgt) if st_tgt else ""
    row["reason_hash"] = reason_hash_stable(strategy)
    row["behavior_hash_quality"] = _behavior_quality(int(ix.size))
    row["status"] = "ok"
    row["error"] = ""
    return row


def analyze_one_yaml(
    ypath: Path,
    *,
    store: FeatureStore,
    meta_by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    row: dict[str, Any] = {k: "" for k in _DIVERSITY_FIELDS}
    row["candidate_yaml"] = ypath.name
    try:
        doc = yaml.safe_load(ypath.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            row["status"] = "invalid_yaml"
            return row
        cid = str(doc.get("candidate_id", "")).strip()
        strategy = str(doc.get("strategy", "")).strip()
        row["candidate_id"] = cid
        row["strategy"] = strategy
        m = meta_by_id.get(cid, {})
        row["candidate_rank"] = m.get("candidate_rank", "")
        row["candidate_score"] = m.get("candidate_score", "")
        sel = doc.get("selection")
        if isinstance(sel, dict) and sel.get("warning") is not None:
            row["warning"] = sel.get("warning", "")
        else:
            row["warning"] = m.get("warning", "")

        cfg = _load_merged_config(doc)
        core = analyze_merged_config(strategy, cfg, store=store)
        for k in (
            "n_signals",
            "n_long_signals",
            "n_short_signals",
            "first_signal_ts",
            "last_signal_ts",
            "pure_signal_hash",
            "signal_hash",
            "stop_target_hash",
            "reason_hash",
            "behavior_hash_quality",
            "total_unique_timestamps",
            "mean_gap_minutes",
            "feature_key_short",
            "context_key_short",
            "status",
            "error",
        ):
            row[k] = core.get(k, "")
    except Exception as e:
        row["status"] = "error"
        row["error"] = f"{type(e).__name__}: {e}"
    return row


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate-root", type=Path, required=True)
    p.add_argument("--asset", default="equity")
    p.add_argument("--symbol", default="QQQ")
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--output-root", type=Path, required=True)
    args = p.parse_args(argv)

    root = args.candidate_root
    if not root.is_absolute():
        root = Path.cwd() / root
    out = args.output_root
    if not out.is_absolute():
        out = Path.cwd() / out
    out.mkdir(parents=True, exist_ok=True)

    sel = root / "selected_candidates" if (root / "selected_candidates").is_dir() else root
    yamls = sorted(sel.glob("*.yaml"))
    if not yamls:
        print(f"ERROR no YAML under {sel}", file=sys.stderr)
        return 2

    meta = _candidate_rows_from_parent(sel)
    store = FeatureStore(
        asset=args.asset, symbol=args.symbol.upper(), start=args.start, end=args.end
    )
    rows = [analyze_one_yaml(yp, store=store, meta_by_id=meta) for yp in yamls]

    div_csv = out / "candidate_signal_diversity.csv"
    with div_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=_DIVERSITY_FIELDS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow(r)

    by_pure: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        h = str(r.get("pure_signal_hash", "")).strip()
        cid = str(r.get("candidate_id", "")).strip()
        if h and cid:
            by_pure[h].append(cid)
    dup_csv = out / "duplicate_signal_groups.csv"
    with dup_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f, fieldnames=["pure_signal_hash", "n_candidates", "candidate_ids"]
        )
        w.writeheader()
        for h, cids in sorted(by_pure.items(), key=lambda x: (-len(x[1]), x[0])):
            if len(cids) < 2:
                continue
            w.writerow(
                {
                    "pure_signal_hash": h,
                    "n_candidates": len(cids),
                    "candidate_ids": json.dumps(sorted(set(cids))),
                }
            )

    by_strat: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        by_strat[str(r.get("strategy", ""))].append(r)
    summ_rows: list[dict[str, Any]] = []
    for strat, lst in sorted(by_strat.items()):
        pure_set = {
            str(x.get("pure_signal_hash", "")) for x in lst if x.get("pure_signal_hash")
        }
        sig_set = {str(x.get("signal_hash", "")) for x in lst if x.get("signal_hash")}
        pure_set.discard("")
        sig_set.discard("")
        summ_rows.append(
            {
                "strategy": strat,
                "n_candidates": len(lst),
                "n_unique_pure_signal_hash": len(pure_set),
                "n_unique_signal_hash": len(sig_set),
                "total_signals_sum": int(
                    sum(int(x.get("n_signals") or 0) for x in lst)
                ),
            }
        )
    sum_csv = out / "strategy_diversity_summary.csv"
    with sum_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "strategy",
                "n_candidates",
                "n_unique_pure_signal_hash",
                "n_unique_signal_hash",
                "total_signals_sum",
            ],
        )
        w.writeheader()
        for r in summ_rows:
            w.writerow(r)

    lines = [
        "# Candidate signal diversity",
        "",
        f"- **candidate_root:** `{root.as_posix()}`",
        f"- **window:** {args.start} → {args.end} ({args.symbol.upper()})",
        "",
        "## Per candidate",
        "",
        "| candidate_id | strategy | n_signals | pure_signal_hash (prefix) | behavior_quality |",
        "|--------------|----------|-----------|---------------------------|------------------|",
    ]
    for r in rows:
        ph = str(r.get("pure_signal_hash", ""))[:16]
        lines.append(
            f"| {r.get('candidate_id','')} | {r.get('strategy','')} | {r.get('n_signals','')} | `{ph}` | {r.get('behavior_hash_quality','')} |"
        )
    lines.extend(["", "## Strategy summary", ""])
    lines.append(
        "| strategy | n_candidates | unique_pure_hashes | unique_signal_hashes |"
    )
    lines.append("|----------|-------------|-------------------|---------------------|")
    for r in summ_rows:
        lines.append(
            f"| {r['strategy']} | {r['n_candidates']} | {r['n_unique_pure_signal_hash']} | {r['n_unique_signal_hash']} |"
        )
    (out / "candidate_signal_diversity.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(f"Wrote {div_csv}", flush=True)
    print(f"Wrote {dup_csv}", flush=True)
    print(f"Wrote {sum_csv}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
