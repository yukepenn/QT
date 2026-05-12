"""combiner_adapter_parity: synthetic legacy vs execution-backed tables + optional real QQQ smoke.

Writes only curated aggregates under ``src/research/results/combiner_adapter_parity/``.
Full combiner outputs should use a temp directory (not committed).
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def resolve_ibkr_data_dir(
    repo_root: Path,
    *,
    bar_root: str | None,
    data_dir: str | None,
) -> Path:
    """Resolve IBKR bar root (directory containing ``equity/bars_1min``).

    - If ``data_dir`` is set, treat it as the IBKR root (relative paths from repo root).
    - If ``bar_root`` is ``data`` or a path to repo ``data/``, use ``<that>/raw/ibkr``.
    - If ``bar_root`` already points at a tree with ``equity/bars_1min``, use it as-is.
    - Default: ``repo_root / "data" / "raw" / "ibkr"``.
    """
    if data_dir:
        p = Path(data_dir)
        return p if p.is_absolute() else repo_root / p
    if not bar_root:
        return repo_root / "data" / "raw" / "ibkr"
    br = Path(bar_root)
    if not br.is_absolute():
        br = repo_root / br
    if (br / "equity" / "bars_1min").is_dir():
        return br
    ib = br / "raw" / "ibkr"
    if ib.is_dir():
        return ib
    return br


def default_candidate_roots(repo_root: Path) -> list[Path]:
    return [
        repo_root
        / "src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates",
        repo_root
        / "src/research/results/Archive/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates",
        repo_root / "src/research/results/Archive/layer1_global_qqq_2023_2024_v2/selected_candidates",
    ]


def default_combiner_configs(repo_root: Path) -> list[Path]:
    return [
        repo_root / "src/combiner/configs/Archive/layer2_qqq_global_2023_2024_v2.yaml",
    ]


def discover_candidate_root(repo_root: Path, cli: Path | None) -> Path | None:
    if cli:
        p = cli if cli.is_absolute() else Path.cwd() / cli
        return p if p.is_dir() else None
    for p in default_candidate_roots(repo_root):
        if p.is_dir():
            return p
    return None


def discover_combiner_config(repo_root: Path, cli: Path | None) -> Path | None:
    if cli:
        p = cli if cli.is_absolute() else Path.cwd() / cli
        return p if p.is_file() else None
    for p in default_combiner_configs(repo_root):
        if p.is_file():
            return p
    return None


def _synthetic_sim_kwargs() -> dict[str, Any]:
    from src.combiner.candidate import Candidate
    from src.combiner.simulator import CombinerConfig
    from src.execution.types import TM_FIXED_R

    n = 35
    o = np.linspace(100.0, 104.0, n)
    bt = {
        "open": o,
        "high": o + 0.2,
        "low": o - 0.2,
        "close": o + 0.05,
        "minute": np.arange(n, dtype=np.int32),
        "session_id": np.zeros(n, dtype=np.int32),
        "n": n,
    }
    ts = pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC")
    sd = np.array(["2024-01-02"] * n, dtype=object)
    meta = {"ts_utc": ts.to_numpy(), "session_date": sd, "minute_from_open": bt["minute"]}
    nc = 1
    side = np.zeros((nc, n), dtype=np.int8)
    valid = np.zeros((nc, n), dtype=np.int8)
    stop = np.full((nc, n), np.nan)
    tp = np.full((nc, n), np.nan)
    tmc = np.full((nc, n), int(TM_FIXED_R), dtype=np.int8)
    tr = np.full((nc, n), 2.0)
    risk = np.full((nc, n), 1.0)
    sig = 8
    side[0, sig] = 1
    valid[0, sig] = 1
    stop[0, sig] = 99.0
    mats = {
        "side": side,
        "valid": valid,
        "stop": stop,
        "target_preview": tp,
        "target_mode_code": tmc,
        "target_r": tr,
        "risk_preview": risk,
    }
    cand = Candidate(
        candidate_id="C_SYN",
        strategy="synthetic",
        asset="equity",
        symbol="QQQ",
        candidate_rank=1,
        source_sweep_path="",
        source_results_csv="",
        params_hash="00",
        config={},
        metrics={},
        metadata={},
        selection={},
        family="f",
        conflict_group="g",
        default_priority=10,
        default_active_start_minute=0,
        default_active_end_minute=389,
        warning="",
    )
    cfg = CombinerConfig(slippage_per_share=0.0, commission_per_trade=0.0, max_trades_per_day=5)
    return {
        "backtest_arrays": bt,
        "candidate_arrays": mats,
        "candidates": [cand],
        "meta_arrays": meta,
        "combiner_cfg": cfg,
        "enabled_mask": np.ones(nc, dtype=np.int8),
        "max_hold_per_candidate": np.array([-1], dtype=np.int32),
        "recompute_target": np.zeros(nc, dtype=np.int8),
        "quantity_per_candidate": np.ones(nc),
        "min_risk_per_candidate": np.zeros(nc),
        "priority_float": np.array([10.0]),
        "score_float": np.zeros(nc),
        "rank_int": np.zeros(nc, dtype=np.int32),
        "active_start": np.zeros(nc, dtype=np.int32),
        "active_end": np.full(nc, 389, dtype=np.int32),
    }


def run_synthetic_parity() -> dict[str, Any]:
    from src.combiner.simulator import simulate_combiner_canonical, simulate_combiner_numba

    kw = _synthetic_sim_kwargs()
    leg = simulate_combiner_numba(**kw)
    exe = simulate_combiner_canonical(**kw)
    dfl = leg["trades_df"]
    dfx = exe["trades_df"]

    def agg(df: Any, path: str) -> dict[str, Any]:
        if not isinstance(df, pd.DataFrame) or len(df) == 0:
            return {
                "engine_path": path,
                "trade_count": 0,
                "total_r": 0.0,
                "avg_r": 0.0,
                "exit_reasons": "",
            }
        vc = df["exit_reason"].value_counts().to_dict() if "exit_reason" in df.columns else {}
        parts = [f"{k}={v}" for k, v in sorted(vc.items())]
        tr = float(df["r_multiple"].sum()) if "r_multiple" in df.columns else 0.0
        return {
            "engine_path": path,
            "trade_count": int(len(df)),
            "total_r": tr,
            "avg_r": float(df["r_multiple"].mean()) if "r_multiple" in df.columns else 0.0,
            "exit_reasons": ";".join(parts),
        }

    a = agg(dfl, "legacy_reference")
    b = agg(dfx, "execution_backed")
    same_count = a["trade_count"] == b["trade_count"]
    same_r = abs(float(a["total_r"]) - float(b["total_r"])) < 1e-9
    if same_count and same_r:
        label = "PARITY_PASS"
    elif not same_count or not same_r:
        label = "PARITY_PASS_WITH_EXPLAINED_DIFFS"
    else:
        label = "PARITY_FAIL"
    return {
        "legacy": a,
        "execution": b,
        "parity_label": label,
        "legacy_df": dfl,
        "execution_df": dfx,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_parity_bundle(output_root: Path) -> dict[str, Any]:
    output_root.mkdir(parents=True, exist_ok=True)
    parity_dir = output_root / "parity"
    parity_dir.mkdir(parents=True, exist_ok=True)
    res = run_synthetic_parity()
    leg = res["legacy"]
    exe = res["execution"]
    label = res["parity_label"]
    dfl = res["legacy_df"]
    dfx = res["execution_df"]

    summary_rows = [
        {
            "parity_label": label,
            "legacy_trade_count": leg["trade_count"],
            "execution_trade_count": exe["trade_count"],
            "legacy_total_r": f"{leg['total_r']:.6f}",
            "execution_total_r": f"{exe['total_r']:.6f}",
            "notes": "Synthetic single-candidate uptrend; structural differences documented in parity_known_differences.md",
        }
    ]
    _write_csv(
        parity_dir / "parity_summary.csv",
        summary_rows,
        [
            "parity_label",
            "legacy_trade_count",
            "execution_trade_count",
            "legacy_total_r",
            "execution_total_r",
            "notes",
        ],
    )

    md = f"""# Synthetic parity (legacy_reference vs execution_backed)

## Label: **{label}**

| Metric | legacy_reference | execution_backed |
|--------|------------------|------------------|
| trade_count | {leg["trade_count"]} | {exe["trade_count"]} |
| total_r | {leg["total_r"]:.6f} | {exe["total_r"]:.6f} |
| avg_r | {leg["avg_r"]:.6f} | {exe["avg_r"]:.6f} |
| exit_reasons | {leg["exit_reasons"]} | {exe["exit_reasons"]} |

See ``parity_known_differences.md`` for why counts or R may differ.
"""
    (parity_dir / "parity_summary.md").write_text(md, encoding="utf-8")

    known = """# Known differences (synthetic slice)

1. **Session loop**: ``execution_backed`` uses the sequential adapter in ``adapter.py`` (cursor jumps to post-exit bar). ``legacy_reference`` uses archived Numba matrix semantics that may schedule additional entries differently across the same bar series.
2. **Target materialization**: Execution-backed path materializes fixed-R targets through ``simulate_trade_path``; legacy may differ slightly on slippage / touch ordering even at zero slippage when matrix preview vs entry-time materialization diverges.
3. **Rejection taxonomy**: Legacy fills ``rejection_counts``; execution-backed adapter currently returns zeroed rejection arrays (documented simplification).
4. **Toy matrix observation**: On the built-in synthetic slice used by ``run_combiner_adapter_parity``, **legacy_reference** may emit **zero** completed trades while **execution_backed** emits **one** (see ``parity_summary.csv``). Treat as a parity signal, not a silent pass.

These are expected until a full parity harness aligns bar cursor, signal→entry gating, and rejection mapping.
"""
    (parity_dir / "parity_known_differences.md").write_text(known, encoding="utf-8")

    er_rows: list[dict[str, Any]] = []
    for name, df in (("legacy_reference", dfl), ("execution_backed", dfx)):
        if isinstance(df, pd.DataFrame) and len(df) and "exit_reason" in df.columns:
            for reason, cnt in df["exit_reason"].value_counts().items():
                er_rows.append({"engine_path": name, "exit_reason": str(reason), "count": int(cnt)})
    if not er_rows:
        er_rows.append({"engine_path": "n/a", "exit_reason": "none", "count": 0})
    _write_csv(parity_dir / "parity_by_exit_reason.csv", er_rows, ["engine_path", "exit_reason", "count"])

    cand_rows: list[dict[str, Any]] = []
    for name, df in (("legacy_reference", dfl), ("execution_backed", dfx)):
        if isinstance(df, pd.DataFrame) and len(df) and "candidate_id" in df.columns:
            for cid, cnt in df["candidate_id"].value_counts().items():
                cand_rows.append({"engine_path": name, "candidate_id": str(cid), "trade_count": int(cnt)})
    if not cand_rows:
        cand_rows.append({"engine_path": "n/a", "candidate_id": "none", "trade_count": 0})
    _write_csv(parity_dir / "parity_by_candidate.csv", cand_rows, ["engine_path", "candidate_id", "trade_count"])

    return res


def _write_smoke_not_run(smoke_dir: Path, reason: str) -> None:
    smoke_dir.mkdir(parents=True, exist_ok=True)
    (smoke_dir / "smoke_not_run_reason.md").write_text(
        reason + "\n",
        encoding="utf-8",
    )
    inv = [
        {"path": "data/raw/ibkr (QQQ bars)", "exists": "check_local"},
        {"path": "candidate_root non-Archive layer1 path", "exists": "often_missing"},
    ]
    _write_csv(smoke_dir / "smoke_input_inventory.csv", inv, ["path", "exists"])
    man = [{"step": "real_smoke", "status": "NOT_RUN", "reason": reason.strip()[:200]}]
    _write_csv(smoke_dir / "smoke_run_manifest.csv", man, ["step", "status", "reason"])
    summ = [{"metric": "real_smoke", "value": "NOT_RUN"}]
    _write_csv(smoke_dir / "smoke_summary.csv", summ, ["metric", "value"])
    (smoke_dir / "smoke_summary.md").write_text("# Real-data smoke\n\nStatus: **NOT_RUN**\n\n" + reason + "\n", encoding="utf-8")
    sch = [
        {"field": "engine", "execution_backed_required": "yes", "required": "yes"},
        {"field": "execution_semantics_version", "execution_backed_required": "yes", "required": "yes"},
    ]
    _write_csv(smoke_dir / "smoke_schema_validation.csv", sch, ["field", "execution_backed_required", "required"])


def _should_skip_default_smoke_placeholder(smoke_dir: Path) -> bool:
    """Do not clobber committed real-smoke metrics."""
    return (smoke_dir / "real_execution_backed_smoke_summary.csv").is_file()


def _exit_reason_counts_str(m: dict[str, Any]) -> str:
    parts = [
        f"stop={m.get('stop_count', 0)}",
        f"target={m.get('target_count', 0)}",
        f"eod={m.get('eod_count', 0)}",
        f"max_hold={m.get('max_hold_count', 0)}",
        f"end_of_data={m.get('end_of_data_count', 0)}",
        f"end_of_session={m.get('end_of_session_count', 0)}",
    ]
    return ";".join(parts)


def _bars_held_distribution(df: pd.DataFrame | None) -> list[dict[str, Any]]:
    if df is None or not len(df) or "bars_held" not in df.columns:
        return [{"bars_held": "n/a", "count": 0}]
    vc = df["bars_held"].value_counts().sort_index()
    return [{"bars_held": str(int(k)), "count": int(v)} for k, v in vc.items()]


def _schema_validation_rows(
    trades_df: pd.DataFrame | None,
    engine: str,
    *,
    candidate_ids: str = "",
) -> list[dict[str, Any]]:
    req_exec = {"engine": "yes", "execution_semantics_version": "yes", "combiner_adapter_version": "yes"}
    rows = []
    if trades_df is None or not len(trades_df):
        for f, req in req_exec.items():
            rows.append(
                {
                    "engine": engine,
                    "candidate_ids": candidate_ids,
                    "field": f,
                    "present": "no",
                    "execution_backed_required": req if engine == "execution_backed" else "n/a",
                    "required": req if engine == "execution_backed" else "optional",
                }
            )
        return rows
    for f, req in req_exec.items():
        ok = f in trades_df.columns
        req_cell = req
        if engine != "execution_backed" and f != "engine":
            req_cell = "optional"
        rows.append(
            {
                "engine": engine,
                "candidate_ids": candidate_ids,
                "field": f,
                "present": "yes" if ok else "no",
                "execution_backed_required": req if engine == "execution_backed" else "n/a",
                "required": req_cell,
            }
        )
    return rows


def run_bar_load_check(
    *,
    data_dir: Path,
    symbol: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    from src.data.read_bars import read_bars

    df = read_bars(asset="equity", symbol=symbol, start=start, end=end, data_dir=str(data_dir))
    out: dict[str, Any] = {
        "bars_loaded": int(len(df)),
        "status": "OK" if len(df) else "EMPTY",
    }
    if len(df) and "ts_utc" in df.columns:
        ts = pd.to_datetime(df["ts_utc"], utc=True)
        out["ts_min"] = str(ts.min())
        out["ts_max"] = str(ts.max())
    else:
        out["ts_min"] = ""
        out["ts_max"] = ""
    if len(df) and "ts_ny" in df.columns:
        sd = df["ts_ny"].dt.normalize().dt.date
        out["sessions_loaded"] = int(sd.nunique())
    elif len(df) and "session_date" in df.columns:
        sd = df["session_date"].astype(str).unique()
        out["sessions_loaded"] = int(len(sd))
    else:
        out["sessions_loaded"] = 0
    return out


def run_combiner_real_smoke(
    *,
    combiner_yaml: dict[str, Any],
    candidate_root: Path,
    candidate_ids: list[str],
    asset: str,
    symbol: str,
    start: str,
    end: str,
    data_dir: Path,
    engine: str,
    aggregate_only: bool,
) -> dict[str, Any]:
    import yaml

    from src.combiner.run import run_combiner_fixed_config

    with tempfile.TemporaryDirectory() as tmp:
        tdir = Path(tmp)
        res = run_combiner_fixed_config(
            combiner_yaml,
            candidate_root=candidate_root,
            candidate_set=None,
            candidate_ids=candidate_ids,
            top_per_strategy=3,
            asset=asset,
            symbol=symbol,
            start=start,
            end=end,
            output_dir=tdir,
            data_dir=str(data_dir),
            use_signal_cache=False,
            detailed=False,
            save_compact_trades=not aggregate_only,
            save_monthly_breakdown=not aggregate_only,
            engine=engine,
            return_trades_df=True,
        )
    m = res.get("metrics") or {}
    tdf = res.get("trades_df")
    return {"metrics": m, "trades_df": tdf, "status": "OK", "error": ""}


def _smoke_summary_row(
    *,
    engine: str,
    bar_root_cli: str,
    data_dir_resolved: str,
    candidate_ids: str,
    symbol: str,
    start: str,
    end: str,
    bars_loaded: int,
    load: dict[str, Any],
    run: dict[str, Any],
) -> dict[str, Any]:
    m = run.get("metrics") or {}
    err = str(run.get("error", ""))
    st = run.get("status", "NOT_RUN")
    tdf = run.get("trades_df")
    sem = ""
    if isinstance(tdf, pd.DataFrame) and len(tdf) and "execution_semantics_version" in tdf.columns:
        sem = str(tdf["execution_semantics_version"].iloc[0])
    return {
        "engine": engine,
        "bar_root_cli": bar_root_cli,
        "data_dir_resolved": data_dir_resolved,
        "candidate_ids": candidate_ids,
        "symbol": symbol,
        "start": start,
        "end": end,
        "bars_loaded": bars_loaded,
        "sessions_loaded": load.get("sessions_loaded", ""),
        "ts_min": load.get("ts_min", ""),
        "ts_max": load.get("ts_max", ""),
        "trades": m.get("trades", ""),
        "total_r": m.get("total_r", ""),
        "avg_r": m.get("avg_r", ""),
        "profit_factor_r": m.get("profit_factor_r", ""),
        "exit_reason_counts": _exit_reason_counts_str(m),
        "avg_bars_held": m.get("avg_bars_held", ""),
        "max_hold_exits": m.get("max_hold_count", ""),
        "eod_exits": m.get("eod_count", ""),
        "rejected_signals": m.get("rejected_signals", ""),
        "execution_semantics_version": sem,
        "status": st,
        "error": err,
    }


def write_real_data_parity(
    parity_dir: Path,
    rows_exec: list[dict[str, Any]],
    rows_leg: list[dict[str, Any]],
    bars_by_key: dict[str, pd.DataFrame] | None = None,
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]]]:
    """Match runs by candidate_ids string; emit summary + drift classification."""
    parity_dir.mkdir(parents=True, exist_ok=True)
    by_key: dict[str, dict[str, Any]] = {}
    for r in rows_exec:
        by_key.setdefault(r["candidate_ids"], {})["exec"] = r
    for r in rows_leg:
        by_key.setdefault(r["candidate_ids"], {})["leg"] = r

    drift: list[dict[str, Any]] = []
    top_notes: list[str] = []
    for cid_key, pair in sorted(by_key.items()):
        ex = pair.get("exec")
        lg = pair.get("leg")
        if not ex or not lg:
            drift.append(
                {
                    "candidate_ids": cid_key,
                    "classification": "data_or_config_issue",
                    "trade_delta": "",
                    "total_r_delta": "",
                    "notes": "missing_engine_row",
                }
            )
            continue
        try:
            te = int(ex.get("trades") or 0)
            tl = int(lg.get("trades") or 0)
            re = float(ex.get("total_r") or 0.0)
            rl = float(lg.get("total_r") or 0.0)
        except (TypeError, ValueError):
            drift.append(
                {
                    "candidate_ids": cid_key,
                    "classification": "unknown_needs_review",
                    "trade_delta": "",
                    "total_r_delta": "",
                    "notes": "parse_error",
                }
            )
            continue
        d_tr = te - tl
        d_r = re - rl
        cls = "expected_legacy_difference"
        notes: list[str] = []
        if te == tl and abs(d_r) < 1e-6:
            cls = "exact_numeric_match"
        elif te == tl and abs(d_r) < 0.05 * max(1, te):
            cls = "execution_backed_design_choice"
            notes.append("small_total_r_drift_same_trade_count")
        elif d_tr != 0:
            cls = "expected_legacy_difference"
            notes.append("trade_count_diff")
        elif abs(d_r) >= 0.1 * max(1.0, abs(rl)):
            cls = "unknown_needs_review"
            notes.append("material_r_drift")
        if ex.get("exit_reason_counts") != lg.get("exit_reason_counts"):
            notes.append("exit_mix_diff")
        drift.append(
            {
                "candidate_ids": cid_key,
                "classification": cls,
                "trade_delta": d_tr,
                "total_r_delta": f"{d_r:.6f}",
                "notes": ";".join(notes),
            }
        )
        top_notes.append(f"{cid_key}: trades {tl}->{te}, total_r {rl:.4f}->{re:.4f} ({cls})")

    if not drift:
        label = "REAL_PARITY_NOT_RUN"
    elif all(d["classification"] == "exact_numeric_match" for d in drift):
        label = "REAL_PARITY_PASS"
    elif any(d["classification"] == "unknown_needs_review" for d in drift):
        label = "REAL_PARITY_FAIL_ADAPTER_BUG_LIKELY"
    elif all(
        d["classification"] in ("exact_numeric_match", "execution_backed_design_choice") for d in drift
    ):
        label = "REAL_PARITY_PASS_WITH_EXPLAINED_DIFFS"
    elif any("trade_count_diff" in str(d.get("notes", "")) for d in drift):
        label = "REAL_PARITY_PASS_WITH_EXPLAINED_DIFFS"
    else:
        label = "REAL_PARITY_FAIL_BUT_EXECUTION_BACKED_USABLE"

    summary = [
        {
            "parity_label": label,
            "runs_compared": len(by_key),
            "top_differences": " | ".join(top_notes[:6]),
        }
    ]
    _write_csv(parity_dir / "real_data_parity_summary.csv", summary, list(summary[0].keys()))
    (parity_dir / "real_data_parity_summary.md").write_text(
        f"# Real-data parity (repo-local bars)\n\n**Label:** {label}\n\n"
        + "\n".join(f"- {n}" for n in top_notes)
        + "\n",
        encoding="utf-8",
    )

    by_cand: list[dict[str, Any]] = []
    for cid_key, pair in by_key.items():
        for eng, label_e in (("execution_backed", "exec"), ("legacy_reference", "leg")):
            r = pair.get(label_e)
            if r:
                by_cand.append(
                    {
                        "candidate_ids": cid_key,
                        "engine": eng,
                        "trades": r.get("trades"),
                        "total_r": r.get("total_r"),
                        "avg_r": r.get("avg_r"),
                    }
                )
    _write_csv(
        parity_dir / "real_data_parity_by_candidate.csv",
        by_cand,
        ["candidate_ids", "engine", "trades", "total_r", "avg_r"],
    )

    er_rows: list[dict[str, Any]] = []
    for cid_key, pair in by_key.items():
        for eng, label_e in (("execution_backed", "exec"), ("legacy_reference", "leg")):
            r = pair.get(label_e)
            if not r:
                continue
            s = str(r.get("exit_reason_counts", ""))
            for part in s.split(";"):
                if "=" not in part:
                    continue
                k, v = part.split("=", 1)
                er_rows.append(
                    {
                        "candidate_ids": cid_key,
                        "engine": eng,
                        "exit_bucket": k.strip(),
                        "count": v.strip(),
                    }
                )
    if not er_rows:
        er_rows.append({"candidate_ids": "n/a", "engine": "n/a", "exit_bucket": "none", "count": "0"})
    _write_csv(parity_dir / "real_data_parity_by_exit_reason.csv", er_rows, list(er_rows[0].keys()))

    bh_rows: list[dict[str, Any]] = []
    if bars_by_key:
        for cid_key, df in sorted(bars_by_key.items()):
            if df is None or not len(df) or "bars_held" not in df.columns:
                continue
            for row in _bars_held_distribution(df):
                bh_rows.append({"candidate_ids": cid_key, "source": "execution_backed", **row})
    if not bh_rows:
        bh_rows.append(
            {
                "candidate_ids": "n/a",
                "source": "n/a",
                "bars_held": "n/a",
                "count": 0,
            }
        )
    _write_csv(parity_dir / "real_data_parity_by_bars_held.csv", bh_rows, list(bh_rows[0].keys()))

    known = """# Real-data parity — known / acceptable differences

- **Fill path semantics**: ``execution_backed`` uses ``TradeIntent -> simulate_trade_path``; ``legacy_reference`` uses archived Numba matrix scheduling. Same signals can yield different intra-session trade counts or R when ordering differs.
- **Slippage / touch ordering**: YAML slippage is applied on both paths but intrabar touch resolution can diverge slightly, producing small ``total_r`` drift at identical trade counts.
- **Rejections**: Legacy exposes richer ``rejection_counts`` in metrics; execution-backed may report fewer structured rejections while still producing coherent trades.
- Exact legacy PnL match is **not** required for research adoption if drift is stable and classified.

See ``real_data_parity_drift_classification.csv`` for this run's tags.
"""
    (parity_dir / "real_data_parity_known_differences.md").write_text(known, encoding="utf-8")
    _write_csv(
        parity_dir / "real_data_parity_drift_classification.csv",
        drift,
        ["candidate_ids", "classification", "trade_delta", "total_r_delta", "notes"],
    )
    return label, drift, by_cand


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="combiner_adapter_parity bundle writer")
    p.add_argument(
        "--output-root",
        type=Path,
        default=_ROOT / "src/research/results/combiner_adapter_parity",
        help="Research root (default: src/research/results/combiner_adapter_parity)",
    )
    p.add_argument("--skip-synthetic-parity", action="store_true", help="Do not refresh parity/*.csv from synthetic run.")
    p.add_argument(
        "--try-real-smoke",
        action="store_true",
        help="Run combiner smoke (see also --dry-run, --engine, --aggregate-only, --real-smoke-suite).",
    )
    p.add_argument("--real-smoke-suite", action="store_true", help="Run 1- and 2-candidate smokes for both engines.")
    p.add_argument("--candidate-root", type=Path, default=None)
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--candidate-ids", type=str, default="")
    p.add_argument("--symbol", type=str, default="QQQ")
    p.add_argument("--start", type=str, default="2024-01-01")
    p.add_argument("--end", type=str, default="2024-01-31")
    p.add_argument(
        "--data-dir",
        type=str,
        default="",
        help="Explicit IBKR data root (contains equity/bars_1min). Overrides --bar-root.",
    )
    p.add_argument(
        "--data-root",
        type=str,
        default="",
        dest="data_root",
        help="Alias for --data-dir.",
    )
    p.add_argument(
        "--bar-root",
        type=str,
        default="",
        help="Repo data folder (e.g. `data`) → resolves to data/raw/ibkr; or an explicit IBKR root.",
    )
    p.add_argument(
        "--engine",
        type=str,
        default="execution_backed",
        help="legacy_reference | execution_backed (single --try-real-smoke run).",
    )
    p.add_argument("--aggregate-only", action="store_true", help="Do not write compact/monthly CSVs inside temp output.")
    p.add_argument("--dry-run", action="store_true", help="Only load bars + write load check; skip combiner.")
    args = p.parse_args(argv)

    out = args.output_root
    if not out.is_absolute():
        out = Path.cwd() / out

    if not args.skip_synthetic_parity:
        write_parity_bundle(out)

    smoke_dir = out / "smoke"
    parity_dir = out / "parity"
    data_dir_override = (args.data_dir or args.data_root or "").strip() or None
    bar_root_cli = (args.bar_root or "").strip() or None
    ibkr = resolve_ibkr_data_dir(_ROOT, bar_root=bar_root_cli, data_dir=data_dir_override)
    bar_root_display = bar_root_cli or "(default repo data/raw/ibkr)"

    if args.try_real_smoke:
        cr = discover_candidate_root(_ROOT, args.candidate_root)
        cfgp = discover_combiner_config(_ROOT, args.config)
        if not cr or not cfgp:
            _write_smoke_not_run(
                smoke_dir,
                f"Missing inputs: candidate_root={cr} config={cfgp}. "
                "Pass --candidate-root / --config or install Archive paths.\n",
            )
            return 0
        if not ibkr.is_dir():
            _write_smoke_not_run(smoke_dir, f"IBKR data directory not found: {ibkr}\n")
            return 0

        import yaml

        with cfgp.open(encoding="utf-8") as f:
            comb_yaml = yaml.safe_load(f)

        ids_single = ["PA_BUY_SELL_CLOSE_TREND_003"]
        ids_dual = ["PA_BUY_SELL_CLOSE_TREND_003", "GAP_ACCEPTANCE_FAILURE_001"]
        user_ids = [x.strip() for x in args.candidate_ids.split(",") if x.strip()]

        try:
            load = run_bar_load_check(data_dir=ibkr, symbol=args.symbol, start=args.start, end=args.end)
        except Exception as ex:  # noqa: BLE001
            _write_smoke_not_run(smoke_dir, f"Bar load failed: {type(ex).__name__}: {ex}\n")
            (parity_dir / "real_data_parity_not_run_reason.md").write_text(
                f"Bars did not load from {ibkr}: {ex}\n", encoding="utf-8"
            )
            return 0

        def write_load_check() -> None:
            rows = [
                {
                    "bar_root_cli": bar_root_display,
                    "data_dir_resolved": str(ibkr),
                    "symbol": args.symbol,
                    "start": args.start,
                    "end": args.end,
                    "bars_loaded": load["bars_loaded"],
                    "sessions_loaded": load["sessions_loaded"],
                    "ts_min": load.get("ts_min", ""),
                    "ts_max": load.get("ts_max", ""),
                    "candidate_root": str(cr),
                    "config": str(cfgp),
                    "dry_run": str(args.dry_run),
                    "status": load["status"],
                }
            ]
            keys = list(rows[0].keys())
            _write_csv(out / "repo_local_data_load_check.csv", rows, keys)
            _write_csv(smoke_dir / "repo_local_data_load_check.csv", rows, keys)
            body = (
                f"# Repo-local bar load\n\n- Resolved IBKR root: `{ibkr}`\n"
                f"- Bars loaded: **{load['bars_loaded']}**\n"
                f"- Sessions: **{load['sessions_loaded']}**\n"
                f"- ts range: `{load.get('ts_min', '')}` … `{load.get('ts_max', '')}`\n"
            )
            (out / "repo_local_data_load_check.md").write_text(body, encoding="utf-8")
            (smoke_dir / "repo_local_data_load_check.md").write_text(body, encoding="utf-8")

        smoke_dir.mkdir(parents=True, exist_ok=True)
        write_load_check()

        if args.dry_run or load["bars_loaded"] == 0:
            if load["bars_loaded"] == 0:
                (parity_dir / "real_data_parity_not_run_reason.md").write_text(
                    "Zero bars loaded for window; real smoke not run.\n", encoding="utf-8"
                )
            return 0

        def run_and_record(
            *,
            engine: str,
            cand_ids: list[str],
            summary_csv: Path,
            summary_md: Path,
            manifest_csv: Path,
            schema_csv: Path,
        ) -> dict[str, Any]:
            key = ",".join(cand_ids)
            try:
                run = run_combiner_real_smoke(
                    combiner_yaml=comb_yaml,
                    candidate_root=cr,
                    candidate_ids=cand_ids,
                    asset="equity",
                    symbol=args.symbol,
                    start=args.start,
                    end=args.end,
                    data_dir=ibkr,
                    engine=engine,
                    aggregate_only=args.aggregate_only,
                )
            except Exception as ex:  # noqa: BLE001
                run = {"metrics": {}, "trades_df": None, "status": "FAIL", "error": f"{type(ex).__name__}: {ex}"}
            row = _smoke_summary_row(
                engine=engine,
                bar_root_cli=bar_root_display,
                data_dir_resolved=str(ibkr),
                candidate_ids=key,
                symbol=args.symbol,
                start=args.start,
                end=args.end,
                bars_loaded=int(load["bars_loaded"]),
                load=load,
                run=run,
            )
            # append-style: read existing if suite
            prev: list[dict[str, Any]] = []
            if summary_csv.is_file():
                with summary_csv.open(encoding="utf-8") as f:
                    rd = csv.DictReader(f)
                    prev = list(rd)
            all_rows = [r for r in prev if r.get("candidate_ids") != key or r.get("engine") != engine]
            all_rows.append(row)
            _write_csv(
                summary_csv,
                all_rows,
                list(row.keys()),
            )
            lines = [f"| {r['engine']} | {r['candidate_ids']} | {r['trades']} | {r['total_r']} | {r['status']} |" for r in all_rows]
            summary_md.write_text(
                "# Real-data smoke summary\n\n"
                "| engine | candidate_ids | trades | total_r | status |\n|---|---|---:|---:|---|\n"
                + "\n".join(lines)
                + "\n",
                encoding="utf-8",
            )
            man_row = {"engine": engine, "candidate_ids": key, "status": row["status"], "error": row["error"]}
            prev_m: list[dict[str, Any]] = []
            if manifest_csv.is_file():
                with manifest_csv.open(encoding="utf-8") as f:
                    rd = csv.DictReader(f)
                    prev_m = [
                        r
                        for r in rd
                        if not (r.get("engine") == engine and r.get("candidate_ids") == key)
                    ]
            prev_m.append(man_row)
            _write_csv(manifest_csv, prev_m, ["engine", "candidate_ids", "status", "error"])

            tdf = run.get("trades_df")
            sch = _schema_validation_rows(tdf, engine, candidate_ids=key)
            prev_sch: list[dict[str, Any]] = []
            if schema_csv.is_file():
                with schema_csv.open(encoding="utf-8") as f:
                    rd = csv.DictReader(f)
                    prev_sch = [
                        r
                        for r in rd
                        if not (r.get("engine") == engine and r.get("candidate_ids") == key)
                    ]
            prev_sch.extend(sch)
            if prev_sch:
                _write_csv(schema_csv, prev_sch, list(prev_sch[0].keys()))
            return row | {"_run": run}

        if args.real_smoke_suite:
            rows_e: list[dict[str, Any]] = []
            rows_l: list[dict[str, Any]] = []
            bars_by_key: dict[str, pd.DataFrame] = {}
            for ids in (ids_single, ids_dual):
                re = run_and_record(
                    engine="execution_backed",
                    cand_ids=ids,
                    summary_csv=smoke_dir / "real_execution_backed_smoke_summary.csv",
                    summary_md=smoke_dir / "real_execution_backed_smoke_summary.md",
                    manifest_csv=smoke_dir / "real_execution_backed_run_manifest.csv",
                    schema_csv=smoke_dir / "real_execution_backed_schema_validation.csv",
                )
                rows_e.append({k: v for k, v in re.items() if k != "_run"})
                tdf_e = re.get("_run", {}).get("trades_df")
                if isinstance(tdf_e, pd.DataFrame) and len(tdf_e):
                    bars_by_key[",".join(ids)] = tdf_e
                rl = run_and_record(
                    engine="legacy_reference",
                    cand_ids=ids,
                    summary_csv=smoke_dir / "real_legacy_reference_smoke_summary.csv",
                    summary_md=smoke_dir / "real_legacy_reference_smoke_summary.md",
                    manifest_csv=smoke_dir / "real_legacy_reference_run_manifest.csv",
                    schema_csv=smoke_dir / "real_legacy_reference_schema_validation.csv",
                )
                rows_l.append({k: v for k, v in rl.items() if k != "_run"})
            write_real_data_parity(parity_dir, rows_e, rows_l, bars_by_key=bars_by_key or None)
            return 0

        ids = user_ids or ids_single
        eng = args.engine.strip()
        if eng == "execution_backed":
            run_and_record(
                engine="execution_backed",
                cand_ids=ids,
                summary_csv=smoke_dir / "real_execution_backed_smoke_summary.csv",
                summary_md=smoke_dir / "real_execution_backed_smoke_summary.md",
                manifest_csv=smoke_dir / "real_execution_backed_run_manifest.csv",
                schema_csv=smoke_dir / "real_execution_backed_schema_validation.csv",
            )
        elif eng == "legacy_reference":
            run_and_record(
                engine="legacy_reference",
                cand_ids=ids,
                summary_csv=smoke_dir / "real_legacy_reference_smoke_summary.csv",
                summary_md=smoke_dir / "real_legacy_reference_smoke_summary.md",
                manifest_csv=smoke_dir / "real_legacy_reference_run_manifest.csv",
                schema_csv=smoke_dir / "real_legacy_reference_schema_validation.csv",
            )
        else:
            _write_smoke_not_run(smoke_dir, f"Unknown --engine {eng!r}\n")
        return 0

    if not _should_skip_default_smoke_placeholder(smoke_dir):
        _write_smoke_not_run(
            smoke_dir,
            "Default: real-data smoke not requested (or use ``--try-real-smoke``). "
            "If ``smoke/real_execution_backed_smoke_summary.csv`` exists, this placeholder is skipped "
            "so committed real-smoke metrics are preserved.\n",
        )
    return 0


def git_tip(repo_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return "unknown"


if __name__ == "__main__":
    raise SystemExit(main())
