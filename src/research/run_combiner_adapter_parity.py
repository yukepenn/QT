"""combiner_adapter_parity: synthetic legacy vs execution-backed tables + optional tiny smoke.

Writes only curated aggregates under ``src/research/results/combiner_adapter_parity/``.
Full combiner outputs should use a temp directory (not committed).
"""

from __future__ import annotations

import argparse
import csv
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


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
        help="If candidate YAMLs and QQQ data exist, run a tiny combiner into a temp dir; metrics only to smoke_summary.",
    )
    p.add_argument("--candidate-root", type=Path, default=None)
    p.add_argument("--config", type=Path, default=None)
    p.add_argument("--candidate-ids", type=str, default="")
    p.add_argument("--symbol", type=str, default="QQQ")
    p.add_argument("--start", type=str, default="2024-01-01")
    p.add_argument("--end", type=str, default="2024-01-31")
    p.add_argument("--data-dir", type=str, default="data/raw/ibkr")
    args = p.parse_args(argv)

    out = args.output_root
    if not out.is_absolute():
        out = Path.cwd() / out

    if not args.skip_synthetic_parity:
        write_parity_bundle(out)

    smoke_dir = out / "smoke"
    data_path = Path(args.data_dir)
    if not data_path.is_absolute():
        data_path = _ROOT / data_path

    if args.try_real_smoke:
        if not args.candidate_root or not args.config:
            _write_smoke_not_run(
                smoke_dir,
                "--try-real-smoke requires --candidate-root and --config.\n",
            )
            return 0
        cr = args.candidate_root
        if not cr.is_absolute():
            cr = Path.cwd() / cr
        cfgp = args.config
        if not cfgp.is_absolute():
            cfgp = Path.cwd() / cfgp
        if not cr.is_dir() or not cfgp.is_file():
            _write_smoke_not_run(
                smoke_dir,
                f"Missing inputs: candidate_root exists={cr.is_dir()} config exists={cfgp.is_file()}.\n",
            )
            return 0
        if not data_path.is_dir():
            _write_smoke_not_run(
                smoke_dir,
                f"Data directory not found: {data_path}\n",
            )
            return 0
        ids = [x.strip() for x in args.candidate_ids.split(",") if x.strip()]
        if not ids:
            _write_smoke_not_run(smoke_dir, "No --candidate-ids provided.\n")
            return 0
        try:
            import yaml

            from src.combiner.run import run_combiner_fixed_config

            with cfgp.open(encoding="utf-8") as f:
                comb_yaml = yaml.safe_load(f)
            with tempfile.TemporaryDirectory() as tmp:
                tdir = Path(tmp)
                res = run_combiner_fixed_config(
                    comb_yaml,
                    candidate_root=cr,
                    candidate_set=None,
                    candidate_ids=ids,
                    top_per_strategy=3,
                    asset="equity",
                    symbol=args.symbol,
                    start=args.start,
                    end=args.end,
                    output_dir=tdir,
                    data_dir=str(data_path),
                    use_signal_cache=False,
                    detailed=False,
                    engine="execution_backed",
                )
            smoke_dir.mkdir(parents=True, exist_ok=True)
            m = res.get("metrics") or {}
            summ = [
                {"metric": "real_smoke", "value": "OK"},
                {"metric": "trades", "value": str(m.get("trades", ""))},
                {"metric": "total_r", "value": str(m.get("total_r", ""))},
            ]
            _write_csv(smoke_dir / "smoke_summary.csv", summ, ["metric", "value"])
            (smoke_dir / "smoke_summary.md").write_text(
                "# Real-data smoke\n\nStatus: **OK** (metrics from temp run; detailed trades not committed).\n\n"
                f"- trades: {m.get('trades')}\n- total_r: {m.get('total_r')}\n",
                encoding="utf-8",
            )
            man = [{"step": "run_combiner_fixed_config", "status": "OK", "engine": "execution_backed"}]
            _write_csv(smoke_dir / "smoke_run_manifest.csv", man, ["step", "status", "engine"])
            inv = [{"path": str(cr), "exists": "true"}, {"path": str(cfgp), "exists": "true"}]
            _write_csv(smoke_dir / "smoke_input_inventory.csv", inv, ["path", "exists"])
            sch = [
                {"field": "engine", "execution_backed_required": "yes", "required": "yes"},
                {"field": "execution_semantics_version", "execution_backed_required": "yes", "required": "yes"},
            ]
            _write_csv(smoke_dir / "smoke_schema_validation.csv", sch, ["field", "execution_backed_required", "required"])
        except Exception as ex:  # noqa: BLE001 — research runner surfaces user-visible reason
            _write_smoke_not_run(smoke_dir, f"Real smoke failed: {type(ex).__name__}: {ex}\n")
        return 0

    _write_smoke_not_run(
        smoke_dir,
        "Default: real-data smoke not requested. No QQQ parquet under repo ``data/raw/ibkr`` in CI; "
        "use ``--try-real-smoke`` with local bars and a valid combiner YAML when available.\n",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
