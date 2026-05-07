"""CLI: fixed-system temporal-stability smoke (Layer 3 smoke v1)."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.combiner.run import run_combiner_fixed_config
from src.walkforward.fixed_system import (
    build_fold_combiner_config,
    candidate_yaml_paths,
    load_frozen_system,
    validate_frozen_system,
)
from src.walkforward.folds import SmokeFold, load_smoke_folds
from src.walkforward.metrics import (
    summarize_fold_results,
    summarize_system_across_folds,
    trade_number_rs_from_metrics,
    metrics_slip_row,
)
from src.walkforward.reports import interpretation_sections_markdown


def _resolve(p: Path, cwd: Path) -> Path:
    return p if p.is_absolute() else cwd / p


def _df_to_md(df: pd.DataFrame) -> str:
    if df is None or len(df) == 0:
        return "(empty)"
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def _stress_slippages(smoke: dict[str, Any]) -> tuple[float, list[float]]:
    cost = smoke.get("cost") or {}
    base = float(cost.get("slippage_per_share", 0.01))
    extra = cost.get("stress_slippage_per_share") or []
    slips = sorted({base} | {float(x) for x in extra})
    return base, slips


def _rel_to_repo(path: Path, cwd: Path) -> str:
    try:
        return path.resolve().relative_to(cwd.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def run_smoke(
    smoke: dict[str, Any],
    *,
    cwd: Path,
    validate_only: bool,
    tag: str,
    cli_use_signal_cache: bool | None,
    cli_signal_cache_root: str | None,
) -> int:
    asset = str(smoke.get("asset") or "equity")
    symbol = str(smoke.get("symbol") or "").upper()
    if symbol != "QQQ":
        print(f"ERROR: symbol must be QQQ, got {symbol}", file=sys.stderr)
        return 2

    out_cfg = smoke.get("outputs") or {}
    output_root = _resolve(Path(out_cfg.get("root") or "src/walkforward/results/smoke"), cwd)
    save_compact = bool(out_cfg.get("save_compact_trades", True))
    save_monthly = bool(out_cfg.get("save_monthly_breakdown", True))
    save_cost = bool(out_cfg.get("save_cost_stress", True))

    exec_smoke = smoke.get("execution") or {}
    use_cache_cfg = bool(exec_smoke.get("use_signal_cache", True))
    use_cache = use_cache_cfg if cli_use_signal_cache is None else bool(cli_use_signal_cache)
    sc_root = cli_signal_cache_root or exec_smoke.get("signal_cache_root") or ".cache/qt/candidate_signals"

    folds = load_smoke_folds(smoke)
    systems_cfg = smoke.get("systems") or []
    if not systems_cfg:
        print("ERROR: systems list empty", file=sys.stderr)
        return 2

    frozen_list: list[tuple[str, Path, Any]] = []
    for row in systems_cfg:
        sid = str(row["system_id"])
        fc = _resolve(Path(row["frozen_config"]), cwd)
        if not fc.is_file():
            print(f"ERROR: frozen config not found: {fc}", file=sys.stderr)
            return 2
        fr = load_frozen_system(fc)
        validate_frozen_system(fr, symbol=symbol)
        frozen_list.append((sid, fc, fr))

    if validate_only:
        print("Config valid.")
        print(f"Systems found: {len(frozen_list)}.")
        print(f"Folds found: {len(folds)}.")
        for sid, fc, fr in frozen_list:
            n = len(candidate_yaml_paths(fr))
            print(f"  Candidate YAMLs for {sid}: {n} (frozen={fc.name})")
        print(f"Symbol: {symbol}")
        print(f"Asset: {asset}")
        print(f"Signal cache root: {sc_root}")
        print(f"Output root: {output_root}")
        return 0

    base_slip, stress_slips = _stress_slippages(smoke)
    fold_rows: list[dict[str, Any]] = []
    monthly_parts: list[pd.DataFrame] = []
    daily_parts: list[pd.DataFrame] = []
    stress_parts: list[pd.DataFrame] = []

    for smoke_sid, _fc_path, frozen in frozen_list:
        template_fold = folds[0]
        comb_yaml = build_fold_combiner_config(frozen, template_fold, smoke)

        cr = frozen.candidate_root
        if not cr.is_absolute():
            cr = cwd / cr

        top_ps = int(frozen.combiner.get("top_per_strategy", 1))

        for fold in folds:
            fold_dir = output_root / f"system_{smoke_sid}" / f"fold_{fold.fold_id}"
            comb_use = copy.deepcopy(comb_yaml)
            comb_use.setdefault("execution", {})
            comb_use["execution"]["slippage_per_share"] = base_slip

            run_tag = f"{tag}_{smoke_sid}_{fold.fold_id}"
            res = run_combiner_fixed_config(
                comb_use,
                candidate_root=cr.resolve(),
                candidate_set=None,
                candidate_ids=list(frozen.candidate_ids),
                top_per_strategy=top_ps,
                asset=asset,
                symbol=symbol,
                start=fold.test_start,
                end=fold.test_end,
                output_dir=fold_dir,
                data_dir=str(smoke.get("data_dir") or "data/raw/ibkr"),
                use_signal_cache=use_cache,
                signal_cache_root=sc_root,
                refresh_signal_cache=False,
                detailed=False,
                save_compact_trades=save_compact,
                save_full_signal_logs=False,
                save_rejected_signals=False,
                stress_slippages=stress_slips if save_cost else [base_slip],
                save_monthly_breakdown=save_monthly,
                save_equity=False,
                tag=run_tag,
            )

            mbase = res["metrics"]
            mb = res.get("metrics_by_slippage") or {}
            t1, t2 = trade_number_rs_from_metrics(mbase)
            s02 = metrics_slip_row(mb, 0.02) or {}
            s03 = metrics_slip_row(mb, 0.03) or {}

            fold_rows.append(
                {
                    "system_id": smoke_sid,
                    "frozen_system_id": frozen.system_id,
                    "fold_id": fold.fold_id,
                    "fold_label": fold.label,
                    "test_start": fold.test_start,
                    "test_end": fold.test_end,
                    "trades": mbase.get("trades"),
                    "total_r": mbase.get("total_r"),
                    "profit_factor": mbase.get("profit_factor"),
                    "profit_factor_r": mbase.get("profit_factor_r"),
                    "max_drawdown_r": mbase.get("max_drawdown_r"),
                    "avg_cost_r": mbase.get("avg_cost_r"),
                    "median_cost_r": mbase.get("median_cost_r"),
                    "trade_1_total_r": t1,
                    "trade_2_total_r": t2,
                    "slip_0_02_total_r": s02.get("total_r"),
                    "slip_0_02_pf": s02.get("profit_factor"),
                    "slip_0_03_total_r": s03.get("total_r"),
                    "slip_0_03_pf": s03.get("profit_factor"),
                    "trade_2_positive": bool(t2 is not None and t2 > 0),
                    "positive_total_r": bool((mbase.get("total_r") or 0) > 0),
                    "pf_above_1": bool((mbase.get("profit_factor") or 0) >= 1.0),
                    "pf_r_above_1": bool((mbase.get("profit_factor_r") or 0) >= 1.0),
                    "cost_0_02_survives": bool((s02.get("total_r") or 0) > 0 and (s02.get("profit_factor") or 0) >= 1.0),
                    "cost_0_03_survives": bool((s03.get("total_r") or 0) > 0 and (s03.get("profit_factor") or 0) >= 1.0),
                    "drawdown_exceeds_insample": False,
                    "output_dir": _rel_to_repo(fold_dir, cwd),
                }
            )

            if save_monthly and res.get("monthly_breakdown_path") and Path(res["monthly_breakdown_path"]).is_file():
                md = pd.read_csv(res["monthly_breakdown_path"])
                md.insert(0, "fold_id", fold.fold_id)
                md.insert(0, "system_id", smoke_sid)
                monthly_parts.append(md)

            daily_p = fold_dir / "daily_trade_number_breakdown.csv"
            if daily_p.is_file():
                dd = pd.read_csv(daily_p)
                dd.insert(0, "fold_id", fold.fold_id)
                dd.insert(0, "system_id", smoke_sid)
                daily_parts.append(dd)

            if save_cost and res.get("cost_stress_path") and Path(res["cost_stress_path"]).is_file():
                cs = pd.read_csv(res["cost_stress_path"])
                cs.insert(0, "fold_id", fold.fold_id)
                cs.insert(0, "system_id", smoke_sid)
                stress_parts.append(cs)

    output_root.mkdir(parents=True, exist_ok=True)
    fold_df = summarize_fold_results(fold_rows)
    fold_df.to_csv(output_root / "fold_summary.csv", index=False)

    stitched_parts: list[dict[str, Any]] = []
    for sid in fold_df["system_id"].unique():
        sub = fold_df[fold_df["system_id"] == sid].copy()
        sub["running_total_r"] = pd.to_numeric(sub["total_r"], errors="coerce").fillna(0.0).cumsum()
        stitched_parts.extend(sub.to_dict("records"))
    pd.DataFrame(stitched_parts).to_csv(output_root / "stitched_summary.csv", index=False)

    sys_df = summarize_system_across_folds(fold_df)
    sys_df.to_csv(output_root / "system_summary.csv", index=False)

    if monthly_parts:
        pd.concat(monthly_parts, ignore_index=True).to_csv(output_root / "monthly_breakdown_all.csv", index=False)
    if daily_parts:
        pd.concat(daily_parts, ignore_index=True).to_csv(output_root / "daily_trade_number_by_fold.csv", index=False)
    if stress_parts:
        pd.concat(stress_parts, ignore_index=True).to_csv(output_root / "cost_stress_by_fold.csv", index=False)

    _write_main_summary_md(output_root, smoke, fold_df, sys_df, tag, use_cache, sc_root)
    print(f"[walkforward] wrote {output_root}", flush=True)
    return 0


def _write_main_summary_md(
    output_root: Path,
    smoke: dict[str, Any],
    fold_df: pd.DataFrame,
    sys_df: pd.DataFrame,
    tag: str,
    use_cache: bool,
    sc_root: str,
) -> None:
    lines: list[str] = []
    lines.append("# Layer 3 Smoke v1 — QQQ Fixed Systems")
    lines.append("")
    lines.append("## 1. Purpose")
    lines.append("")
    lines.append(
        "Fixed-system **temporal-stability smoke** over calendar segments. "
        "**Not** full walk-forward. **Not** a profitability claim. **Not** live-ready."
    )
    lines.append("")
    lines.append("## 2. Systems tested")
    lines.append("")
    for _, r in fold_df.drop_duplicates("system_id")[["system_id", "frozen_system_id"]].iterrows():
        lines.append(f"- `{r['system_id']}` (frozen: `{r['frozen_system_id']}`)")
    lines.append("")
    lines.append("## 3. Fold definitions")
    lines.append("")
    for fold_id in fold_df["fold_id"].unique():
        sub = fold_df[fold_df["fold_id"] == fold_id].iloc[0]
        lines.append(f"- **{fold_id}**: {sub.get('test_start')} → {sub.get('test_end')} ({sub.get('fold_label')})")
    lines.append("")
    lines.append("## 4. Validation status")
    lines.append("")
    lines.append("- Runner tag: `%s`" % tag)
    lines.append(f"- Signal cache: **{'on' if use_cache else 'off'}** (root chosen at run time; default `.cache/qt/candidate_signals` or CLI `--signal-cache-root`).")
    lines.append("")
    lines.append("## 5. System-level results")
    lines.append("")
    lines.append(_df_to_md(sys_df))
    lines.append("")
    lines.append("## 6. Fold-level results")
    lines.append("")
    lines.append(_df_to_md(fold_df))
    lines.append("")
    lines.append(interpretation_sections_markdown(sys_df, fold_df))
    lines.append("")
    (output_root / "layer3_smoke_summary.md").write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layer 3 fixed-system temporal smoke.")
    p.add_argument("--config", required=True, help="Smoke YAML config.")
    p.add_argument("--tag", default="layer3_smoke")
    p.add_argument("--validate-only", action="store_true")
    p.add_argument("--use-signal-cache", dest="use_signal_cache", action="store_true", default=None)
    p.add_argument("--no-use-signal-cache", dest="use_signal_cache", action="store_false")
    p.add_argument("--signal-cache-root", default=None, help="Override signal cache directory.")
    args = p.parse_args(argv)

    cwd = Path.cwd()
    cfg_path = _resolve(Path(args.config), cwd)
    if not cfg_path.is_file():
        print(f"ERROR: config not found: {cfg_path}", file=sys.stderr)
        return 2

    smoke = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}

    return run_smoke(
        smoke,
        cwd=cwd,
        validate_only=bool(args.validate_only),
        tag=str(args.tag),
        cli_use_signal_cache=args.use_signal_cache,
        cli_signal_cache_root=args.signal_cache_root,
    )


if __name__ == "__main__":
    raise SystemExit(main())
