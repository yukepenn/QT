"""Export a diversity-repaired candidate root from sweep results + raw diversity audit CSVs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.research.scoring import candidate_score, safe_float
from src.research.select_candidates import (
    _validate_results_df,
    params_hash_from_config,
    strategy_metadata,
    unflatten_config_from_row,
)


def _strategy_slug_upper(strategy: str) -> str:
    return strategy.upper().replace("-", "_")


def _yaml_body(
    *,
    strategy: str,
    csv_path: Path,
    row: pd.Series,
    candidate_id: str,
    filters_used: str,
    warning: str,
) -> dict[str, Any]:
    meta = strategy_metadata(strategy)
    cfg = unflatten_config_from_row(row)
    if not cfg.get("strategy"):
        cfg = {"strategy": strategy, **cfg} if strategy else cfg
    score_v = float(row["_candidate_score"])

    return {
        "candidate_id": candidate_id,
        "strategy": strategy,
        "asset": str(row.get("asset", "equity")),
        "symbol": str(row.get("symbol", "")),
        "strategy_family": meta["strategy_family"],
        "conflict_group": meta.get("conflict_group", "QQQ_directional"),
        "default_priority": int(meta["default_priority"]),
        "default_active_start_minute": int(meta["default_active_start_minute"]),
        "default_active_end_minute": int(meta["default_active_end_minute"]),
        "metadata": {
            "family": meta["strategy_family"],
            "conflict_group": str(meta.get("conflict_group", "QQQ_directional")),
            "default_priority": int(meta["default_priority"]),
            "default_active_start_minute": int(meta["default_active_start_minute"]),
            "default_active_end_minute": int(meta["default_active_end_minute"]),
        },
        "selection": {
            "score": score_v,
            "filters_used": filters_used,
            "warning": warning,
        },
        "source": {
            "results_csv": str(csv_path.resolve()),
            "row_index": int(row["__source_row__"]),
            "sweep_folder": str(csv_path.parent.resolve()),
        },
        "metrics": {
            "trades": int(safe_float(row.get("trades"), 0)),
            "profit_factor": safe_float(row.get("profit_factor")),
            "total_r": safe_float(row.get("total_r")),
            "win_rate": safe_float(row.get("win_rate")),
            "total_net_pnl": safe_float(row.get("total_net_pnl")),
            "avg_r": safe_float(row.get("avg_r")),
            "avg_net_pnl": safe_float(row.get("avg_net_pnl")),
            "max_drawdown_pnl": safe_float(row.get("max_drawdown_pnl")),
            "max_drawdown_r": safe_float(row.get("max_drawdown_r")),
            "avg_bars_held": safe_float(row.get("avg_bars_held")),
            "stop_count": int(safe_float(row.get("stop_count"), 0)),
            "target_count": int(safe_float(row.get("target_count"), 0)),
            "eod_count": int(safe_float(row.get("eod_count"), 0)),
            "end_of_data_count": int(safe_float(row.get("end_of_data_count"), 0)),
            "max_hold_count": int(safe_float(row.get("max_hold_count"), 0)),
        },
        "config": cfg,
    }


def _row_by_source_index(df: pd.DataFrame, source_ix: int) -> pd.Series:
    m = df["__source_row__"] == int(source_ix)
    if not bool(m.any()):
        raise KeyError(f"no row with __source_row__={source_ix}")
    return df.loc[m].iloc[0]


def _pick_from_unique_csv(
    uniq_df: pd.DataFrame,
    *,
    max_n: int,
    require_unique_hash: bool,
    cap_one_path: bool,
) -> tuple[list[int], list[str]]:
    """Return (source_row_indices, notes)."""
    if uniq_df.empty:
        return [], ["empty_unique_csv"]
    if "hash_pick_rank" in uniq_df.columns:
        r1 = uniq_df[uniq_df["hash_pick_rank"] == 1].copy()
    else:
        r1 = uniq_df.copy()
    if r1.empty:
        r1 = uniq_df.copy()
    r1 = r1.sort_values("candidate_score", ascending=False)
    if cap_one_path:
        best = r1.iloc[0]
        return [int(best["source_row_index"])], ["climax_capped_one_path"]

    picked: list[int] = []
    seen_h: set[str] = set()
    notes: list[str] = []
    for _, r in r1.iterrows():
        h = str(r.get("pure_signal_hash", "") or r.get("pure_signal_hash_key", ""))
        if require_unique_hash and h in seen_h:
            continue
        if h:
            seen_h.add(h)
        picked.append(int(r["source_row_index"]))
        if len(picked) >= max_n:
            break
    if len(picked) < max_n and not require_unique_hash:
        for _, r in r1.iterrows():
            ix = int(r["source_row_index"])
            if ix not in picked:
                picked.append(ix)
                notes.append("duplicate_fill")
                if len(picked) >= max_n:
                    break
    return picked, notes


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--close-trend-results-csv", type=Path, required=True)
    p.add_argument("--climax-results-csv", type=Path, required=True)
    p.add_argument("--raw-diversity-dir", type=Path, required=True)
    p.add_argument("--output-root", type=Path, required=True)
    p.add_argument("--top-close-trend", type=int, default=3)
    p.add_argument("--top-climax", type=int, default=3)
    p.add_argument(
        "--fill-duplicates-if-needed",
        action="store_true",
        help="If fewer unique hashes than slots, add lower-ranked rows.",
    )
    args = p.parse_args(argv)

    div_dir = args.raw_diversity_dir
    if not div_dir.is_absolute():
        div_dir = Path.cwd() / div_dir
    out_root = args.output_root
    if not out_root.is_absolute():
        out_root = Path.cwd() / out_root
    sel_dir = out_root / "selected_candidates"
    sel_dir.mkdir(parents=True, exist_ok=True)

    ct_csv = (
        args.close_trend_results_csv
        if args.close_trend_results_csv.is_absolute()
        else Path.cwd() / args.close_trend_results_csv
    )
    cx_csv = (
        args.climax_results_csv
        if args.climax_results_csv.is_absolute()
        else Path.cwd() / args.climax_results_csv
    )

    uniq_ct = div_dir / "unique_signal_hash_candidates_pa_buy_sell_close_trend.csv"
    uniq_cx = div_dir / "unique_signal_hash_candidates_pa_climax_reversal.csv"
    if not uniq_ct.is_file() or not uniq_cx.is_file():
        print(f"ERROR missing unique CSV under {div_dir}", file=sys.stderr)
        return 2

    df_ct = pd.read_csv(ct_csv)
    _validate_results_df(df_ct, path=ct_csv)
    df_ct = df_ct.copy()
    if "__source_row__" not in df_ct.columns:
        df_ct.insert(0, "__source_row__", range(len(df_ct)))
    df_ct["_candidate_score"] = df_ct.apply(candidate_score, axis=1)

    df_cx = pd.read_csv(cx_csv)
    _validate_results_df(df_cx, path=cx_csv)
    df_cx = df_cx.copy()
    if "__source_row__" not in df_cx.columns:
        df_cx.insert(0, "__source_row__", range(len(df_cx)))
    df_cx["_candidate_score"] = df_cx.apply(candidate_score, axis=1)

    uct = pd.read_csv(uniq_ct)
    ucx = pd.read_csv(uniq_cx)

    if "hash_pick_rank" in ucx.columns:
        r1cx = ucx[ucx["hash_pick_rank"] == 1]
    else:
        r1cx = ucx
    _hcol = (
        "pure_signal_hash_key"
        if "pure_signal_hash_key" in r1cx.columns
        else "pure_signal_hash"
    )
    n_unique_climax = int(r1cx[_hcol].nunique()) if not r1cx.empty and _hcol in r1cx.columns else 0
    cap_one = n_unique_climax < 2

    picks_ct, notes_ct = _pick_from_unique_csv(
        uct,
        max_n=int(args.top_close_trend),
        require_unique_hash=True,
        cap_one_path=False,
    )
    if len(picks_ct) < int(args.top_close_trend) and args.fill_duplicates_if_needed:
        picks2, n2 = _pick_from_unique_csv(
            uct,
            max_n=int(args.top_close_trend),
            require_unique_hash=False,
            cap_one_path=False,
        )
        for ix in picks2:
            if ix not in picks_ct:
                picks_ct.append(ix)
                notes_ct.extend(n2)
            if len(picks_ct) >= int(args.top_close_trend):
                break

    picks_cx, notes_cx = _pick_from_unique_csv(
        ucx,
        max_n=1 if cap_one else int(args.top_climax),
        require_unique_hash=not cap_one,
        cap_one_path=cap_one,
    )
    if not cap_one and len(picks_cx) < int(args.top_climax) and args.fill_duplicates_if_needed:
        picks2, n2 = _pick_from_unique_csv(
            ucx,
            max_n=int(args.top_climax),
            require_unique_hash=False,
            cap_one_path=False,
        )
        for ix in picks2:
            if ix not in picks_cx:
                picks_cx.append(ix)
                notes_cx.extend(n2)
            if len(picks_cx) >= int(args.top_climax):
                break

    summary_rows: list[dict[str, Any]] = []
    dup_warn: list[str] = []

    for strategy, df, csv_path, picks in (
        ("pa_buy_sell_close_trend", df_ct, ct_csv, picks_ct),
        ("pa_climax_reversal", df_cx, cx_csv, picks_cx),
    ):
        meta = strategy_metadata(strategy)
        for i, src_ix in enumerate(picks, start=1):
            row = _row_by_source_index(df, src_ix)
            cid = f"{_strategy_slug_upper(strategy)}_DIVERSE_{i:03d}"
            cfg = unflatten_config_from_row(row)
            if not cfg.get("strategy"):
                cfg = {"strategy": strategy, **cfg}
            ph = params_hash_from_config(cfg)
            score_v = float(row["_candidate_score"])
            warn = ""
            body = _yaml_body(
                strategy=strategy,
                csv_path=csv_path,
                row=row,
                candidate_id=cid,
                filters_used="diversity_repair",
                warning=warn,
            )
            ypath = sel_dir / f"{cid}.yaml"
            with ypath.open("w", encoding="utf-8") as f:
                yaml.safe_dump(body, f, sort_keys=False, default_flow_style=False)
            rel_yaml = f"selected_candidates/{cid}.yaml"
            summary_rows.append(
                {
                    "candidate_id": cid,
                    "strategy": strategy,
                    "symbol": str(row.get("symbol", "")),
                    "asset": str(row.get("asset", "equity")),
                    "source_results_csv": str(csv_path.resolve()),
                    "source_row_index": int(src_ix),
                    "source_sweep_folder": str(csv_path.parent.resolve()),
                    "candidate_rank": i,
                    "candidate_score": score_v,
                    "strategy_family": meta["strategy_family"],
                    "default_priority": meta["default_priority"],
                    "default_active_start_minute": meta["default_active_start_minute"],
                    "default_active_end_minute": meta["default_active_end_minute"],
                    "params_hash": ph,
                    "params_json": row.get("params_json", ""),
                    "config_yaml": rel_yaml,
                    "filters_used": "diversity_repair",
                    "warning": warn,
                    "trades": int(safe_float(row.get("trades"), 0)),
                    "win_rate": safe_float(row.get("win_rate")),
                    "total_net_pnl": safe_float(row.get("total_net_pnl")),
                    "total_r": safe_float(row.get("total_r")),
                    "avg_r": safe_float(row.get("avg_r")),
                    "profit_factor": safe_float(row.get("profit_factor")),
                    "max_drawdown_pnl": safe_float(row.get("max_drawdown_pnl")),
                    "max_drawdown_r": safe_float(row.get("max_drawdown_r")),
                    "avg_bars_held": safe_float(row.get("avg_bars_held")),
                    "stop_count": int(safe_float(row.get("stop_count"), 0)),
                    "target_count": int(safe_float(row.get("target_count"), 0)),
                    "eod_count": int(safe_float(row.get("eod_count"), 0)),
                    "end_of_data_count": int(
                        safe_float(row.get("end_of_data_count"), 0)
                    ),
                    "max_hold_count": int(safe_float(row.get("max_hold_count"), 0)),
                }
            )

    if notes_ct or notes_cx:
        dup_warn.append(" ".join(notes_ct + notes_cx))

    pd.DataFrame(summary_rows).to_csv(out_root / "selected_candidates.csv", index=False)

    lines = [
        "# Diversity repair export",
        "",
        f"- **close-trend picks:** {len(picks_ct)} (source rows {picks_ct})",
        f"- **climax picks:** {len(picks_cx)} (source rows {picks_cx})",
        f"- **climax unique strict hashes (hash_pick_rank==1):** {n_unique_climax}",
        f"- **climax one-path cap:** {cap_one}",
        "",
    ]
    (out_root / "diversity_repair_summary.md").write_text("\n".join(lines), encoding="utf-8")

    if dup_warn:
        (out_root / "duplicate_fill_warning.txt").write_text(
            "\n".join(dup_warn) + "\n", encoding="utf-8"
        )

    if cap_one:
        (out_root / "CLIMAX_CAPPED_ONE_PATH.md").write_text(
            "# Climax capped to one signal path\n\n"
            "Raw strict pool shows a single `pure_signal_hash` at `hash_pick_rank==1`. "
            "Exported **one** best climax row; close-trend remains the primary diversity driver.\n",
            encoding="utf-8",
        )

    print(json.dumps({"n_exported": len(summary_rows), "cap_one": cap_one}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
