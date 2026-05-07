"""Layer 2 candidate overlap / conflict diagnostics (post-precompute)."""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def write_candidate_diagnostics(
    csm: Any,
    out_dir: Path,
    *,
    enabled_mask: np.ndarray | None = None,
) -> None:
    """Write overlap / conflict CSVs (fast; vectorized)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    nc, n = csm.side.shape
    mask = np.ones(nc, dtype=np.bool_) if enabled_mask is None else enabled_mask.astype(np.bool_)
    minute = csm.meta_arrays["minute_from_open"].astype(np.int64)
    ts = csm.meta_arrays["ts_utc"]

    t0 = time.perf_counter()
    print(f"[diagnostics] writing candidate_signal_summary.csv... C={nc} N={n}", flush=True)
    rows_sig = []
    med_by_ci = np.full(nc, np.nan, dtype=np.float64)
    for ci in range(nc):
        if not mask[ci]:
            continue
        c = csm.candidates[ci]
        v = csm.valid[ci] & (csm.side[ci] != 0)
        sig_n = int(np.sum(v))
        long_n = int(np.sum(v & (csm.side[ci] == 1)))
        short_n = int(np.sum(v & (csm.side[ci] == -1)))
        ix = np.flatnonzero(v)
        first_ts = ""
        last_ts = ""
        if sig_n:
            first_ts = str(pd.Timestamp(ts[ix[0]]))
            last_ts = str(pd.Timestamp(ts[ix[-1]]))
        avg_m = float(np.mean(minute[ix])) if sig_n else np.nan
        med_m = float(np.median(minute[ix])) if sig_n else np.nan
        med_by_ci[ci] = med_m
        rows_sig.append(
            {
                "candidate_id": c.candidate_id,
                "strategy": c.strategy,
                "family": c.family,
                "warning": c.warning,
                "candidate_rank": c.candidate_rank,
                "priority": c.default_priority,
                "score": float(c.selection.get("score", 0) or 0),
                "signals": sig_n,
                "long_signals": long_n,
                "short_signals": short_n,
                "first_signal_ts": first_ts,
                "last_signal_ts": last_ts,
                "avg_signal_minute": avg_m,
                "median_signal_minute": med_m,
                "active_start": c.default_active_start_minute,
                "active_end": c.default_active_end_minute,
            }
        )
    pd.DataFrame(rows_sig).to_csv(out_dir / "candidate_signal_summary.csv", index=False)

    print("[diagnostics] building overlap matrices...", flush=True)
    vmask = (csm.valid & (csm.side != 0) & mask.reshape(-1, 1)).astype(np.int8, copy=False)
    lmask = (csm.valid & (csm.side == 1) & mask.reshape(-1, 1)).astype(np.int8, copy=False)
    smask = (csm.valid & (csm.side == -1) & mask.reshape(-1, 1)).astype(np.int8, copy=False)

    v_i32 = vmask.astype(np.int32, copy=False)
    l_i32 = lmask.astype(np.int32, copy=False)
    s_i32 = smask.astype(np.int32, copy=False)

    same_bar_overlap = v_i32 @ v_i32.T
    same_direction_same_bar = (l_i32 @ l_i32.T) + (s_i32 @ s_i32.T)
    opposite_side_same_bar = (l_i32 @ s_i32.T) + (s_i32 @ l_i32.T)

    session_id = np.asarray(csm.meta_arrays["session_date"])
    _, inv = np.unique(session_id, return_inverse=True)
    s_cnt = int(inv.max() + 1) if inv.size else 0
    print(f"[diagnostics] building session overlap... S={s_cnt}", flush=True)
    session_mat = np.zeros((nc, s_cnt), dtype=np.int8)
    for ci in range(nc):
        if not mask[ci]:
            continue
        ix = np.flatnonzero(vmask[ci].astype(np.bool_, copy=False))
        if ix.size == 0:
            continue
        np.maximum.at(session_mat[ci], inv[ix], 1)
    session_i32 = session_mat.astype(np.int32, copy=False)
    same_day_overlap = session_i32 @ session_i32.T

    print("[diagnostics] writing candidate_overlap_matrix.csv...", flush=True)
    ids = [csm.candidates[i].candidate_id for i in range(nc)]
    pd.DataFrame(same_bar_overlap.astype(np.int32), index=ids, columns=ids).to_csv(
        out_dir / "candidate_overlap_matrix.csv"
    )

    print("[diagnostics] writing candidate_conflict_summary.csv...", flush=True)
    pairs: list[dict[str, Any]] = []
    for ci in range(nc):
        if not mask[ci]:
            continue
        a = csm.candidates[ci]
        for cj in range(ci + 1, nc):
            if not mask[cj]:
                continue
            b = csm.candidates[cj]
            approx_md = (
                float(abs(med_by_ci[ci] - med_by_ci[cj]))
                if np.isfinite(med_by_ci[ci]) and np.isfinite(med_by_ci[cj])
                else float("nan")
            )
            pairs.append(
                {
                    "candidate_a": a.candidate_id,
                    "candidate_b": b.candidate_id,
                    "strategy_a": a.strategy,
                    "strategy_b": b.strategy,
                    "family_a": a.family,
                    "family_b": b.family,
                    "same_bar_overlap": int(same_bar_overlap[ci, cj]),
                    "same_day_overlap": int(same_day_overlap[ci, cj]),
                    "opposite_side_same_bar": int(opposite_side_same_bar[ci, cj]),
                    "same_direction_same_bar": int(same_direction_same_bar[ci, cj]),
                    "approx_abs_median_signal_minute_diff": approx_md,
                }
            )
    pd.DataFrame(pairs).to_csv(out_dir / "candidate_conflict_summary.csv", index=False)
    print(f"[diagnostics] done in {time.perf_counter() - t0:.2f}s", flush=True)
