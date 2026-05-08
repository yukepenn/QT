"""Layer 3 causal mini-WFO runner (single train/test split)."""

from __future__ import annotations

# =============================================================================
# Imports
# =============================================================================

import argparse
import json
import numbers
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.combiner.postprocess import _merged_cfg_for_row, cost_stress
from src.combiner.run import run_combiner_fixed_config
from src.utils.config_validation import validate_common_combiner_config

from src.walkforward.mini_wfo_selection import (
    ComparisonRow,
    MiniWFOValidationError,
    explain_row_eligibility,
    layer2_raw_combo_count,
    load_candidate_warnings,
    pick_best_row,
    render_mini_wfo_summary_md,
    validate_mini_wfo_config,
)

# =============================================================================
# Config loading + CLI
# =============================================================================

def load_mini_wfo_config(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f)
    if not isinstance(doc, dict):
        raise ValueError("mini-WFO config must be a YAML mapping")
    return doc


def run(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Layer 3 causal mini-WFO (QQQ).")
    p.add_argument("--config", required=True, help="Path to mini-WFO YAML config.")
    p.add_argument("--tag", default="mini_wfo", help="Tag for subprocess logs.")
    p.add_argument("--validate-only", action="store_true")
    p.add_argument("--use-signal-cache", action="store_true", help="Forward to Layer 2 / test.")
    p.add_argument("--signal-cache-root", default=None)
    p.add_argument("--refresh-signal-cache", action="store_true")
    p.add_argument(
        "--layer2-detail-top",
        type=int,
        default=160,
        help="Layer 2 sweep detailed reruns for postprocess mapping (default 160).",
    )
    p.add_argument(
        "--resume-from",
        choices=("all", "layer2", "after_sweep"),
        default="all",
        help=(
            "layer2: skip Layer 1 + candidate select. "
            "after_sweep: skip through Layer 2 sweep; reuse latest sweep_* under train_layer2 (postprocess onward)."
        ),
    )
    args = p.parse_args(argv)

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = Path.cwd() / cfg_path
    cfg = load_mini_wfo_config(cfg_path)

    try:
        validate_mini_wfo_config(cfg)
    except MiniWFOValidationError as e:
        print(f"[mini_wfo] VALIDATION FAIL: {e}", file=sys.stderr)
        return 2

    paths = cfg["paths"]
    exp_root = Path(paths["output_root"])
    if not exp_root.is_absolute():
        exp_root = Path.cwd() / exp_root

    cache_yaml = (cfg.get("cache") or {}).get("signal_cache_root") or ".cache/qt/mini_wfo_candidate_signals"
    use_cache = bool(args.use_signal_cache or (cfg.get("cache") or {}).get("use_signal_cache"))
    sc_root = args.signal_cache_root or cache_yaml

    grid = (cfg.get("layer2") or {}).get("grid") or {}
    n_combo = layer2_raw_combo_count(grid)

    if args.validate_only:
        print("[mini_wfo] Config valid.")
        print(f"  symbol={cfg.get('symbol')} asset={cfg.get('asset')}")
        print(f"  train={cfg['train']['start']} .. {cfg['train']['end']}")
        print(f"  test={cfg['test']['start']} .. {cfg['test']['end']}")
        print(f"  Layer 2 raw grid size: {n_combo}")
        print(f"  output_root={exp_root}")
        print(f"  strategies primary={(cfg.get('layer1') or {}).get('strategies')}")
        print(f"  optional diagnostics={(cfg.get('layer1') or {}).get('allow_optional_diagnostics')}")
        print(f"  signal_cache: use={use_cache} root={sc_root}")
        return 0

    rc = _run_full_pipeline(
        cfg,
        exp_root=exp_root,
        tag=args.tag,
        use_signal_cache=use_cache,
        signal_cache_root=sc_root,
        refresh_signal_cache=bool(args.refresh_signal_cache),
        layer2_detail_top=int(args.layer2_detail_top),
        resume_from=str(args.resume_from),
    )
    return rc


# =============================================================================
# Small utilities (filesystem / YAML / typing hygiene)
# =============================================================================

def _run_cmd(cmd: list[str], *, cwd: Path) -> None:
    print(f"[mini_wfo] CMD: {' '.join(cmd)}", flush=True)
    rc = subprocess.run(cmd, cwd=str(cwd))
    if rc.returncode != 0:
        raise RuntimeError(f"command failed exit={rc.returncode}: {' '.join(cmd)}")


def _resolve(p: Path | str, cwd: Path) -> Path:
    x = Path(p)
    return x if x.is_absolute() else cwd / x


def _write_yaml(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False)


def _to_yaml_plain(obj: Any) -> Any:
    """Convert numpy / pandas scalars for PyYAML safe_dump."""
    if obj is None or isinstance(obj, bool):
        return obj
    if isinstance(obj, str):
        return obj
    if isinstance(obj, numbers.Integral):
        return int(obj)
    if isinstance(obj, numbers.Real):
        return float(obj)
    if hasattr(obj, "item"):
        try:
            return _to_yaml_plain(obj.item())
        except Exception:
            pass
    if isinstance(obj, dict):
        return {str(k): _to_yaml_plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_yaml_plain(v) for v in obj]
    return str(obj)

# =============================================================================
# Train Layer 2 config builder
# =============================================================================

def _build_layer2_train_configs(
    cfg: dict[str, Any], *, exp_root: Path, cwd: Path, signal_cache_root_override: str | None = None
) -> tuple[Path, Path]:
    """Return paths (base_config, sweep_config) under train_layer2."""
    paths = cfg["paths"]
    tl2 = _resolve(paths["train_layer2_root"], cwd)
    cand_sel = exp_root / "train_candidates" / "selected_candidates"

    layer2_block = cfg.get("layer2") or {}
    exec_cfg = cfg.get("execution") or {}

    base: dict[str, Any] = {
        "name": "layer2_mini_wfo_train",
        "candidate_root": str(cand_sel.relative_to(cwd) if cand_sel.is_relative_to(cwd) else cand_sel),
        "execution": {
            "commission_per_trade": float(exec_cfg.get("commission_per_trade", 0.0)),
            "slippage_per_share": float(exec_cfg.get("slippage_per_share", 0.01)),
            "eod_exit_minute": int(exec_cfg.get("eod_exit_minute", 389)),
            "no_new_after_minute": int(exec_cfg.get("no_new_after_minute", 360)),
            "recompute_target_from_entry": bool(exec_cfg.get("recompute_target_from_entry", True)),
            "min_risk_per_share": float(exec_cfg.get("min_risk_per_share", 0.03)),
        },
        "system": {
            "max_open_positions": int(exec_cfg.get("max_open_positions", 1)),
            "max_trades_per_day": 2,
            "daily_max_loss_r": -2.0,
            "cooldown_after_loss_minutes": 15,
        },
        "conflict": {
            "priority_policy": "metadata_priority",
            "same_bar_policy": "priority",
            "tie_breakers": ["candidate_score", "candidate_rank", "candidate_index"],
            "opposite_direction_policy": "",
        },
        "candidate_sets": layer2_block.get("candidate_sets") or {},
    }

    if bool((cfg.get("cache") or {}).get("use_signal_cache")):
        root = signal_cache_root_override or str(cfg["cache"]["signal_cache_root"])
        base["precompute"] = {"use_signal_cache": True, "signal_cache_root": root}

    sweep_doc: dict[str, Any] = {
        "name": "layer2_mini_wfo_train_sweep",
        "base_config": "layer2_train_config.yaml",
        "grid": layer2_block.get("grid") or {},
        "fixed": {
            "execution.commission_per_trade": float(exec_cfg.get("commission_per_trade", 0.0)),
            "execution.slippage_per_share": float(exec_cfg.get("slippage_per_share", 0.01)),
            "execution.eod_exit_minute": int(exec_cfg.get("eod_exit_minute", 389)),
            "execution.no_new_after_minute": int(exec_cfg.get("no_new_after_minute", 360)),
            "execution.recompute_target_from_entry": bool(exec_cfg.get("recompute_target_from_entry", True)),
            "execution.min_risk_per_share": float(exec_cfg.get("min_risk_per_share", 0.03)),
            "system.max_open_positions": int(exec_cfg.get("max_open_positions", 1)),
        },
    }

    base_path = tl2 / "layer2_train_config.yaml"
    sweep_path = tl2 / "layer2_train_sweep_config.yaml"
    abs_sel = (exp_root / "train_candidates" / "selected_candidates").resolve()
    try:
        base["candidate_root"] = str(abs_sel.relative_to(cwd.resolve()))
    except ValueError:
        base["candidate_root"] = str(abs_sel)
    _write_yaml(base_path, base)
    sweep_doc["base_config"] = str(base_path.resolve().relative_to(cwd.resolve()))
    _write_yaml(sweep_path, sweep_doc)
    return base_path, sweep_path

# =============================================================================
# Candidate ID hygiene (avoid collisions across experiments)
# =============================================================================

def _rename_candidate_prefix(selected_dir: Path, *, prefix: str) -> None:
    """Rename FAILED_ORB_001 -> MINIWFO_FAILED_ORB_001 and update YAML bodies + selected_candidates.csv."""
    csv_path = selected_dir.parent / "selected_candidates.csv"
    if not csv_path.is_file():
        raise FileNotFoundError(csv_path)
    df = pd.read_csv(csv_path)
    mapping: dict[str, str] = {}
    new_docs: dict[str, dict[str, Any]] = {}

    for y in sorted(selected_dir.glob("*.yaml")):
        with y.open(encoding="utf-8") as f:
            doc = yaml.safe_load(f)
        if not isinstance(doc, dict):
            continue
        old_id = str(doc.get("candidate_id", y.stem))
        strat = str(doc.get("strategy") or "unknown")
        slug = strat.upper().replace("-", "_")
        rank = old_id.split("_")[-1] if "_" in old_id else "001"
        if old_id.startswith(prefix + "_"):
            continue
        new_id = f"{prefix}_{slug}_{rank}"
        mapping[old_id] = new_id
        doc["candidate_id"] = new_id
        new_docs[new_id] = doc

    for old_id, new_id in mapping.items():
        old_p = selected_dir / f"{old_id}.yaml"
        new_p = selected_dir / f"{new_id}.yaml"
        if old_p == new_p:
            continue
        new_p.write_text(
            yaml.safe_dump(new_docs[new_id], sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        old_p.unlink(missing_ok=True)

    if not mapping:
        return

    def _rewrite_cell(x: Any) -> Any:
        if isinstance(x, str):
            for a, b in mapping.items():
                x = x.replace(a, b)
        return x

    df["candidate_id"] = df["candidate_id"].map(lambda z: mapping.get(str(z), z))
    if "config_yaml" in df.columns:
        df["config_yaml"] = df["config_yaml"].map(_rewrite_cell)
    df.to_csv(csv_path, index=False)

# =============================================================================
# Layer 2 sweep helpers / curated export
# =============================================================================

def _latest_sweep_dir(root: Path) -> Path | None:
    if not root.is_dir():
        return None
    dirs = [p for p in root.iterdir() if p.is_dir() and p.name.startswith("sweep_")]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime)


def _copy_curated_train_outputs(exp_root: Path, analysis: Path) -> None:
    pairs = [
        ("behavior_unique_systems.csv", "train_layer2_behavior_unique.csv"),
        ("behavior_unique_systems.md", "train_layer2_behavior_unique.md"),
        ("cost_stress/cost_stress_results.csv", "train_layer2_cost_stress.csv"),
        ("cost_stress/cost_stress_summary.md", "train_layer2_cost_stress.md"),
        ("cost_robust_systems.csv", "train_layer2_cost_robust_systems.csv"),
        ("cost_robust_systems.md", "train_layer2_cost_robust_systems.md"),
        ("top_unique_systems.csv", "train_layer2_top_unique_systems.csv"),
        ("top_unique_systems.md", "train_layer2_top_unique_systems.md"),
    ]
    for rel_src, dst_name in pairs:
        src = analysis / rel_src
        if src.is_file():
            shutil.copy2(src, exp_root / dst_name)

# =============================================================================
# Reference comparisons (from previously recorded smoke baselines)
# =============================================================================

def _reference_comparison_rows(test_window: str) -> list[ComparisonRow]:
    return [
        ComparisonRow(
            system="trap_recent_top1 (smoke ref)",
            source_type="fixed_smoke_reference",
            selected_using="recent_window_in_sample",
            test_window=test_window,
            trades=323,
            total_r=69.057,
            PF=1.516,
            PF_R=">1 (ref)",
            maxDD_r=-12.082,
            slip_0_02_total_r="(see smoke)",
            slip_0_03_total_r="(see smoke)",
            interpretation="High headline R; selected on recent window — not causal train→test.",
        ),
        ComparisonRow(
            system="opening_pair_full_history (smoke ref)",
            source_type="fixed_smoke_reference",
            selected_using="full_history_pair",
            test_window=test_window,
            trades=204,
            total_r=7.547,
            PF=1.146,
            PF_R=">1 (ref)",
            maxDD_r=-18.888,
            slip_0_02_total_r="(see smoke)",
            slip_0_03_total_r="(see smoke)",
            interpretation="Lower R; broader selection context — use as sanity anchor only.",
        ),
    ]

# =============================================================================
# Main pipeline: Layer 1 → candidates → Layer 2 → postprocess → freeze → test
# =============================================================================

def _run_full_pipeline(
    cfg: dict[str, Any],
    *,
    exp_root: Path,
    tag: str,
    use_signal_cache: bool,
    signal_cache_root: str | None,
    refresh_signal_cache: bool,
    layer2_detail_top: int,
    resume_from: str,
) -> int:
    cwd = _ROOT
    train = cfg["train"]
    test = cfg["test"]
    paths = cfg["paths"]
    layer1_root = _resolve(paths["train_layer1_root"], cwd)
    layer2_root = _resolve(paths["train_layer2_root"], cwd)
    frozen_dir = _resolve(paths["frozen_system_dir"], cwd)
    test_root = _resolve(paths["test_root"], cwd)

    exp_root.mkdir(parents=True, exist_ok=True)
    train_candidates = exp_root / "train_candidates"
    sel_dir = train_candidates / "selected_candidates"
    analysis_root = layer2_root / "train_layer2_postprocess"

    l1 = cfg.get("layer1") or {}
    primary = [str(x) for x in (l1.get("strategies") or [])]
    diag = [str(x) for x in (l1.get("allow_optional_diagnostics") or [])]
    strategies_csv = ",".join(primary + diag)
    tag_l1 = str(l1.get("tag") or tag)

    if resume_from == "all":
        _run_cmd(
            [
                sys.executable,
                str(cwd / "src/research/run_layer1_focused.py"),
                "--asset",
                str(cfg.get("asset", "equity")),
                "--symbols",
                "QQQ",
                "--start",
                str(train["start"]),
                "--end",
                str(train["end"]),
                "--strategies",
                strategies_csv,
                "--tag",
                tag_l1,
                "--output-root",
                str(layer1_root),
                "--top",
                str(int(l1.get("top_per_strategy", 5)) * 20),
                "--min-trades",
                "20",
            ],
            cwd=cwd,
        )

        shutil.copy2(layer1_root / "sweep_manifest.csv", exp_root / "train_layer1_manifest.csv")

        cs = cfg.get("candidate_selection") or {}
        strict = cs.get("strict") or {}
        relaxed = cs.get("relaxed") or {}

        sel_cmd = [
            sys.executable,
            str(cwd / "src/research/select_candidates.py"),
            "--manifest",
            str(layer1_root / "sweep_manifest.csv"),
            "--output-root",
            str(train_candidates),
            "--top-per-strategy",
            str(int(cs.get("max_candidates_per_strategy") or l1.get("top_per_strategy") or 5)),
            "--min-trades",
            str(int(strict.get("min_trades", 40))),
            "--min-profit-factor",
            str(float(strict.get("min_profit_factor", 1.02))),
            "--min-total-r",
            str(float(strict.get("min_total_r", 0.0))),
            "--max-drawdown-r",
            str(float(strict.get("max_drawdown_r", -50.0))),
            "--max-avg-bars-held",
            str(float(strict.get("max_avg_bars_held", 120))),
            "--max-eod-count",
            str(int(strict.get("max_eod_count", 0))),
            "--max-end-of-data-count",
            str(int(strict.get("max_end_of_data_count", 0))),
            "--tag",
            tag,
        ]
        if relaxed.get("enabled"):
            sel_cmd.append("--allow-relaxed-fallback")
            sel_cmd.extend(
                [
                    "--relaxed-min-trades",
                    str(int(relaxed.get("min_trades", 25))),
                    "--relaxed-min-profit-factor",
                    str(float(relaxed.get("min_profit_factor", 1.0))),
                    "--relaxed-min-total-r",
                    str(float(relaxed.get("min_total_r", -5.0))),
                    "--relaxed-max-drawdown-r",
                    str(float(relaxed.get("max_drawdown_r", -70.0))),
                ]
            )
        _run_cmd(sel_cmd, cwd=cwd)

        shutil.copy2(train_candidates / "candidate_summary.md", exp_root / "train_candidate_summary.md")

        _rename_candidate_prefix(sel_dir, prefix="MINIWFO")

        shutil.copy2(train_candidates / "selected_candidates.csv", exp_root / "train_selected_candidates.csv")
    else:
        if resume_from in ("layer2", "after_sweep"):
            if not sel_dir.is_dir() or not any(sel_dir.glob("*.yaml")):
                raise FileNotFoundError(
                    f"--resume-from {resume_from} requires existing YAMLs under {sel_dir}"
                )
            man_csv = layer1_root / "sweep_manifest.csv"
            if man_csv.is_file() and not (exp_root / "train_layer1_manifest.csv").is_file():
                shutil.copy2(man_csv, exp_root / "train_layer1_manifest.csv")
            csum = train_candidates / "candidate_summary.md"
            if csum.is_file() and not (exp_root / "train_candidate_summary.md").is_file():
                shutil.copy2(csum, exp_root / "train_candidate_summary.md")
            scsv = train_candidates / "selected_candidates.csv"
            if scsv.is_file():
                shutil.copy2(scsv, exp_root / "train_selected_candidates.csv")

    base_cfg_path, sweep_cfg_path = _build_layer2_train_configs(
        cfg, exp_root=exp_root, cwd=cwd, signal_cache_root_override=signal_cache_root if use_signal_cache else None
    )

    if resume_from == "after_sweep":
        sweep_dir = _latest_sweep_dir(layer2_root)
        if sweep_dir is None:
            raise FileNotFoundError(
                f"--resume-from after_sweep: no sweep_* under {layer2_root}; run with layer2 first."
            )
    else:
        sweep_cmd = [
            sys.executable,
            str(cwd / "src/combiner/sweep.py"),
            "--candidate-root",
            str(sel_dir),
            "--config",
            str(sweep_cfg_path.relative_to(cwd)),
            "--asset",
            str(cfg.get("asset", "equity")),
            "--symbol",
            str(cfg.get("symbol", "QQQ")),
            "--start",
            str(train["start"]),
            "--end",
            str(train["end"]),
            "--output-root",
            str(layer2_root),
            "--tag",
            f"{tag}_layer2_train",
            "--top",
            "400",
            "--detail-top",
            str(layer2_detail_top),
            "--progress-every",
            "50",
        ]
        if use_signal_cache:
            sweep_cmd.append("--use-signal-cache")
            if signal_cache_root:
                sweep_cmd.extend(["--signal-cache-root", str(signal_cache_root)])
            if refresh_signal_cache:
                sweep_cmd.append("--refresh-signal-cache")
        _run_cmd(sweep_cmd, cwd=cwd)

        sweep_dir = _latest_sweep_dir(layer2_root)
        if sweep_dir is None:
            raise RuntimeError("Layer 2 sweep produced no sweep_* directory")

    shutil.copy2(sweep_dir / "results.csv", exp_root / "train_layer2_results.csv")
    if (sweep_dir / "summary.md").is_file():
        shutil.copy2(sweep_dir / "summary.md", exp_root / "train_layer2_summary.md")

    sel_l2 = cfg.get("layer2", {}).get("selection") or {}
    bh_top = int(sel_l2.get("behavior_dedupe_top", 50))
    cs_top = int(sel_l2.get("cost_stress_top", 10))

    pp_cmd = [
        sys.executable,
        str(cwd / "src/combiner/postprocess.py"),
        "--sweep-dir",
        str(sweep_dir),
        "--output-root",
        str(analysis_root),
        "--dedupe-top",
        str(bh_top),
        "--cost-stress-top",
        str(cs_top),
        "--candidate-root",
        str(sel_dir),
        "--config",
        str(base_cfg_path.relative_to(cwd)),
        "--asset",
        str(cfg.get("asset", "equity")),
        "--symbol",
        str(cfg.get("symbol", "QQQ")),
        "--start",
        str(train["start"]),
        "--end",
        str(train["end"]),
        "--behavior-dedupe-top",
        str(bh_top),
        "--cost-robust-min-trades",
        str(int(sel_l2.get("require_min_trades", 80)) // 2),
        "--min-trades-cost-rank",
        str(max(40, int(sel_l2.get("require_min_trades", 80)) // 2)),
    ]
    if use_signal_cache:
        pp_cmd.append("--use-signal-cache")
        if signal_cache_root:
            pp_cmd.extend(["--signal-cache-root", str(signal_cache_root)])
        if refresh_signal_cache:
            pp_cmd.append("--refresh-signal-cache")
    _run_cmd(pp_cmd, cwd=cwd)

    _copy_curated_train_outputs(exp_root, analysis_root)

    bh_path = analysis_root / "behavior_unique_systems.csv"
    tu_path = analysis_root / "top_unique_systems.csv"
    cost_path = analysis_root / "cost_stress" / "cost_stress_results.csv"

    behavior_df = pd.read_csv(bh_path) if bh_path.is_file() else pd.DataFrame()
    if behavior_df.empty and tu_path.is_file():
        behavior_df = pd.read_csv(tu_path)

    cost_df = pd.read_csv(cost_path) if cost_path.is_file() else None

    warnings_map = load_candidate_warnings(train_candidates / "selected_candidates.csv")
    layer2_meta = cfg.get("layer2") or {}
    best, audit = pick_best_row(
        behavior_df,
        primary_sets=list(layer2_meta.get("primary_candidate_sets") or []),
        diagnostic_sets=list(layer2_meta.get("diagnostic_candidate_sets") or []),
        sel=layer2_meta.get("selection") or {},
        warnings_by_candidate=warnings_map,
        cost_df=cost_df,
    )

    if best is None:
        raise RuntimeError(
            "mini-WFO: no eligible Layer 2 system after train-only gates; check sweep/postprocess outputs."
        )

    _write_selection_audit(
        exp_root=exp_root,
        cfg=cfg,
        behavior_df=behavior_df.head(bh_top) if len(behavior_df) else behavior_df,
        cost_df=cost_df,
        selected_row=best,
        selection_meta=audit,
    )

    with base_cfg_path.open(encoding="utf-8") as f:
        base_yaml = yaml.safe_load(f)
    validate_common_combiner_config(base_yaml)
    merged = _merged_cfg_for_row(base_yaml, best)

    frozen_dir.mkdir(parents=True, exist_ok=True)
    cand_ids = json.loads(str(best["candidate_ids_json"]))
    exp_name = str(cfg["experiment"].get("name") or "mini_wfo")
    sys_id = f"{exp_name}_frozen_rank1"

    metrics_train = {k: best.get(k) for k in ("trades", "total_r", "profit_factor", "profit_factor_r", "max_drawdown_r", "combiner_score")}

    frozen_doc = _to_yaml_plain(
        {
        "system_id": sys_id,
        "source": {
            "train_start": train["start"],
            "train_end": train["end"],
            "selected_from": "train_layer2_behavior_unique",
            "selected_rank": 1,
        },
        "candidate_root": str(sel_dir.resolve().as_posix()),
        "candidate_ids": cand_ids,
        "combiner": merged,
        "cost": {
            "commission_per_trade": merged.get("execution", {}).get("commission_per_trade"),
            "slippage_per_share": merged.get("execution", {}).get("slippage_per_share"),
            "stress_slippage_per_share": (cfg.get("execution") or {}).get("stress_slippage_per_share") or [0.02, 0.03],
        },
        "selection_reason": (
            "Train-only gates + primary-set preference + MTD/cooldown/priority policy scoring "
            f"(audit={json.dumps(audit, default=str)})"
        ),
        "selection_metrics_train": metrics_train,
        "live_ready": False,
        "research_status": "mini_wfo_selected_train_only",
        }
    )
    _write_yaml(frozen_dir / "selected_frozen_system.yaml", frozen_doc)

    decision_md = [
        "# Train-only frozen system decision",
        "",
        f"- Selected candidate_set: **{best.get('candidate_set')}**",
        f"- top_per_strategy={best.get('top_per_strategy')} max_trades_per_day={best.get('max_trades_per_day')}",
        f"- daily_max_loss_r={best.get('daily_max_loss_r')} cooldown={best.get('cooldown_after_loss_minutes')}",
        f"- priority_policy={best.get('priority_policy')}",
        "",
        "## Why",
        "",
        "- Filters: min trades / PF_R / total_r / drawdown floor / optional 0.02 cost stress from postprocess.",
        "- Prefer primary candidate sets (`failed_only`, `gap_only`, `failed_gap`) over `failed_gap_with_prior_day_diagnostic` unless diagnostic clearly dominates.",
        "- Prefer `max_trades_per_day=1` when scores are close (train stability).",
        "",
        "## Caveat",
        "",
        "Selection uses **train 2023–2024 only**; test performance is out-of-sample for this YAML.",
        "",
    ]
    (frozen_dir / "selection_decision.md").write_text("\n".join(decision_md), encoding="utf-8")

    (exp_root / "train_layer2_selection_audit.md").write_text(
        "# Train Layer 2 selection audit\n\n```json\n"
        + json.dumps(audit, indent=2)
        + "\n```\n",
        encoding="utf-8",
    )

    exec_o = cfg.get("execution") or {}
    stress = [float(x) for x in (exec_o.get("stress_slippage_per_share") or [0.02, 0.03])]
    out_o = cfg.get("outputs") or {}

    test_root.mkdir(parents=True, exist_ok=True)
    run_combiner_fixed_config(
        merged,
        candidate_root=sel_dir,
        candidate_set=None,
        candidate_ids=cand_ids,
        top_per_strategy=int(best["top_per_strategy"]),
        asset=str(cfg.get("asset", "equity")),
        symbol=str(cfg.get("symbol", "QQQ")),
        start=str(test["start"]),
        end=str(test["end"]),
        output_dir=test_root,
        data_dir="data/raw/ibkr",
        include_warnings=None,
        use_signal_cache=use_signal_cache,
        signal_cache_root=signal_cache_root,
        refresh_signal_cache=refresh_signal_cache,
        detailed=False,
        save_compact_trades=bool(out_o.get("save_compact_trades")),
        save_full_signal_logs=bool(out_o.get("save_full_signal_logs")),
        save_rejected_signals=bool(out_o.get("save_rejected_signals")),
        stress_slippages=sorted(set([float(exec_o.get("slippage_per_share", 0.01))] + stress)),
        save_monthly_breakdown=bool(out_o.get("save_monthly_breakdown", True)),
        save_equity=False,
        tag=f"{tag}_test",
    )

    if (test_root / "summary.csv").is_file():
        shutil.copy2(test_root / "summary.csv", test_root / "test_fold_metrics.csv")
    if (test_root / "cost_stress.csv").is_file():
        shutil.copy2(test_root / "cost_stress.csv", test_root / "test_cost_stress.csv")
    if (test_root / "monthly_breakdown.csv").is_file():
        shutil.copy2(test_root / "monthly_breakdown.csv", test_root / "test_monthly_breakdown.csv")
    if (test_root / "daily_trade_number_breakdown.csv").is_file():
        shutil.copy2(test_root / "daily_trade_number_breakdown.csv", test_root / "test_daily_trade_number_breakdown.csv")

    metrics_json = test_root / "metrics.json"
    summary_txt = ["# Mini-WFO test summary", ""]
    if metrics_json.is_file():
        with metrics_json.open(encoding="utf-8") as f:
            mj = json.load(f)
        for k in sorted(mj.keys()):
            summary_txt.append(f"- **{k}**: {mj[k]}")
    (test_root / "test_summary.md").write_text("\n".join(summary_txt) + "\n", encoding="utf-8")

    test_win = f"{test['start']} — {test['end']}"
    rows = _reference_comparison_rows(test_win)
    m_last = {}
    if metrics_json.is_file():
        with metrics_json.open(encoding="utf-8") as f:
            m_last = json.load(f)

    slip02 = slip03 = ""
    if (test_root / "cost_stress.csv").is_file():
        cdf = pd.read_csv(test_root / "cost_stress.csv")
        if "slippage_per_share" in cdf.columns and "total_r" in cdf.columns:
            s2 = cdf[cdf["slippage_per_share"].astype(float).between(0.019, 0.021)]
            s3 = cdf[cdf["slippage_per_share"].astype(float).between(0.029, 0.031)]
            if len(s2):
                slip02 = s2.iloc[0]["total_r"]
            if len(s3):
                slip03 = s3.iloc[0]["total_r"]

    rows.append(
        ComparisonRow(
            system=sys_id,
            source_type="mini_wfo_frozen",
            selected_using="train_2023_2024_only",
            test_window=test_win,
            trades=m_last.get("trades", ""),
            total_r=m_last.get("total_r", ""),
            PF=m_last.get("profit_factor", ""),
            PF_R=m_last.get("profit_factor_r", ""),
            maxDD_r=m_last.get("max_drawdown_r", ""),
            slip_0_02_total_r=slip02,
            slip_0_03_total_r=slip03,
            interpretation="Causal path: Layer 1+2 on train only, frozen for test.",
        )
    )
    pd.DataFrame([r.as_dict() for r in rows]).to_csv(exp_root / "comparison_to_fixed_smoke.csv", index=False)
    cmp_md = ["# Comparison to fixed smoke references", "", "| system | trades | total_r | PF_R | note |", "|---|---:|---:|---|---|"]
    for r in rows:
        cmp_md.append(
            f"| {r.system} | {r.trades} | {r.total_r} | {r.PF_R} | {r.interpretation[:80]}… |"
        )
    (exp_root / "comparison_to_fixed_smoke.md").write_text("\n".join(cmp_md) + "\n", encoding="utf-8")

    # LOOKAHEAD diagnostic only (never used for selection).
    _write_oracle_diagnostic(
        exp_root=exp_root,
        cfg=cfg,
        base_layer2_config_path=base_cfg_path,
        behavior_df=behavior_df,
        cost_df_train=cost_df,
        selected_row=best,
        top_n=min(50, len(behavior_df)) if len(behavior_df) else 0,
        signal_cache_root_override=str(signal_cache_root) if signal_cache_root else None,
    )

    decision = _classify_decision(m_last, test_root / "monthly_breakdown.csv", test_root / "cost_stress.csv")
    fill = _enrich_summary_placeholders(exp_root, best)
    summary_md = _build_final_summary(cfg, exp_root, decision, m_last, fill)
    (exp_root / "mini_wfo_summary.md").write_text(summary_md, encoding="utf-8")

    print(f"[mini_wfo] DONE decision={decision} root={exp_root}", flush=True)
    return 0

# =============================================================================
# Reporting helpers (summary fill + decision heuristics)
# =============================================================================


def _md_table(df: pd.DataFrame) -> str:
    try:
        return df.to_markdown(index=False)
    except Exception:
        return df.to_string(index=False)


def _write_selection_audit(
    *,
    exp_root: Path,
    cfg: dict[str, Any],
    behavior_df: pd.DataFrame,
    cost_df: pd.DataFrame | None,
    selected_row: pd.Series,
    selection_meta: dict[str, Any],
) -> None:
    """Write selection_audit.{csv,md,json} under the run root."""
    layer2_meta = cfg.get("layer2") or {}
    sel = (layer2_meta.get("selection") or {}).copy()
    primary_sets = set(layer2_meta.get("primary_candidate_sets") or [])
    diagnostic_sets = set(layer2_meta.get("diagnostic_candidate_sets") or [])

    warnings_map = load_candidate_warnings(exp_root / "train_selected_candidates.csv")

    slip002_by_ur: dict[int, float] | None = None
    if cost_df is not None and len(cost_df) and "unique_rank" in cost_df.columns:
        sub = cost_df[cost_df["slippage_per_share"].astype(float).sub(0.02).abs() < 1e-9]
        slip002_by_ur = {}
        for ur, g in sub.groupby("unique_rank"):
            slip002_by_ur[int(ur)] = float(g.iloc[0].get("total_r", 0.0) or 0.0)

    rows: list[dict[str, Any]] = []
    for _, r in behavior_df.iterrows():
        eligible, reasons, _ann = explain_row_eligibility(
            r,
            sel=sel,
            cost_slip_002_by_unique_rank=slip002_by_ur,
            warnings_by_candidate=warnings_map,
            primary_candidate_sets=primary_sets,
            diagnostic_candidate_sets=diagnostic_sets,
        )
        rows.append(
            {
                "unique_rank": int(r.get("unique_rank", -1) or -1),
                "candidate_set": r.get("candidate_set"),
                "top_per_strategy": r.get("top_per_strategy"),
                "max_trades_per_day": r.get("max_trades_per_day"),
                "daily_max_loss_r": r.get("daily_max_loss_r"),
                "cooldown_after_loss_minutes": r.get("cooldown_after_loss_minutes"),
                "priority_policy": r.get("priority_policy"),
                "candidate_ids_json": r.get("candidate_ids_json"),
                "train_trades": r.get("trades"),
                "train_total_r": r.get("total_r"),
                "train_profit_factor_r": r.get("profit_factor_r", r.get("profit_factor")),
                "train_max_drawdown_r": r.get("max_drawdown_r"),
                "train_slip_0_02_total_r": (
                    slip002_by_ur.get(int(r.get("unique_rank") or -1)) if slip002_by_ur else None
                ),
                "eligible": bool(eligible),
                "rejection_reasons": "|".join(reasons),
            }
        )

    df_out = pd.DataFrame(rows)
    df_out.to_csv(exp_root / "selection_audit.csv", index=False)

    md_lines = [
        "# Mini-WFO selection audit (train-only)",
        "",
        "This audit explains why the frozen system was selected **using train only**.",
        "",
        "## Selected system (train-selected)",
        "",
        f"- candidate_set: **{selected_row.get('candidate_set')}**",
        f"- candidate_ids_json: `{selected_row.get('candidate_ids_json')}`",
        f"- train_trades: {selected_row.get('trades')} train_total_r: {selected_row.get('total_r')} "
        f"train_pf_r: {selected_row.get('profit_factor_r', selected_row.get('profit_factor'))} "
        f"train_maxDD_r: {selected_row.get('max_drawdown_r')}",
        "",
        "## Systems considered (behavior-unique table → eligibility)",
        "",
        _md_table(df_out.head(80)) if len(df_out) else "*(no rows)*",
        "",
        "## Key question",
        "",
        "Did mini-WFO select a narrow candidate_set because it was truly best on train, or because filters eliminated broader systems?",
        "",
        f"- behavior_unique_rows_available: **{len(behavior_df)}**",
        f"- eligible_rows_after_filters: **{int(df_out['eligible'].sum()) if 'eligible' in df_out.columns and len(df_out) else 0}**",
        "",
    ]
    (exp_root / "selection_audit.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    out_json = {
        "train_window": cfg.get("train") or {},
        "test_window": cfg.get("test") or {},
        "strategy_universe_layer1": (cfg.get("layer1") or {}).get("strategies") or [],
        "optional_diagnostics_layer1": (cfg.get("layer1") or {}).get("allow_optional_diagnostics") or [],
        "layer2_grid_raw_size": layer2_raw_combo_count((layer2_meta.get("grid") or {})),
        "selection_rules": sel,
        "selection_meta": selection_meta,
        "selected_candidate_set": str(selected_row.get("candidate_set", "")),
        "selected_candidate_ids": json.loads(str(selected_row.get("candidate_ids_json"))),
        "systems_considered": df_out.to_dict(orient="records"),
    }
    (exp_root / "selection_audit.json").write_text(json.dumps(out_json, indent=2, default=str), encoding="utf-8")


def _write_oracle_diagnostic(
    *,
    exp_root: Path,
    cfg: dict[str, Any],
    base_layer2_config_path: Path,
    behavior_df: pd.DataFrame,
    cost_df_train: pd.DataFrame | None,
    selected_row: pd.Series,
    top_n: int = 50,
    signal_cache_root_override: str | None = None,
) -> None:
    """LOOKAHEAD diagnostic: evaluate top-N train systems on test; never used for selection."""
    out_csv = exp_root / "oracle_diagnostic.csv"
    out_md = exp_root / "oracle_diagnostic.md"

    if behavior_df is None or len(behavior_df) == 0:
        out_csv.write_text("", encoding="utf-8")
        out_md.write_text("# ORACLE / LOOKAHEAD DIAGNOSTIC (empty)\n\nNo behavior-unique rows available.\n", encoding="utf-8")
        return

    # Train cost stress at 0.02 (for reporting only).
    train_slip002_by_ur: dict[int, float] = {}
    if cost_df_train is not None and len(cost_df_train) and "unique_rank" in cost_df_train.columns:
        sub = cost_df_train[cost_df_train["slippage_per_share"].astype(float).sub(0.02).abs() < 1e-9]
        for ur, g in sub.groupby("unique_rank"):
            train_slip002_by_ur[int(ur)] = float(g.iloc[0].get("total_r", 0.0) or 0.0)

    # Evaluate on test using existing cost_stress helper (precompute once; loop over top-N rows).
    oracle_root = exp_root / "_oracle_tmp"
    oracle_root.mkdir(parents=True, exist_ok=True)
    test = cfg["test"]

    # cost_stress expects unique_rank and the config knobs present.
    head = behavior_df.head(int(top_n)).copy()
    if "unique_rank" not in head.columns:
        head.insert(0, "unique_rank", range(1, len(head) + 1))

    test_stress_df = cost_stress(
        unique_df=head,
        output_root=oracle_root,
        candidate_root=Path(str((cfg.get("paths") or {}).get("output_root", exp_root)))  # unused; overwritten below
        if False
        else Path(exp_root / "train_candidates" / "selected_candidates"),
        base_config_path=base_layer2_config_path,
        asset=str(cfg.get("asset", "equity")),
        symbol=str(cfg.get("symbol", "QQQ")),
        start=str(test["start"]),
        end=str(test["end"]),
        data_dir="data/raw/ibkr",
        top_n=int(top_n),
        use_signal_cache=True,
        signal_cache_root=signal_cache_root_override or (cfg.get("cache") or {}).get("signal_cache_root"),
    )

    def _pick(df: pd.DataFrame, *, slip: float) -> pd.DataFrame:
        return df[(df["slippage_per_share"].astype(float) - slip).abs() < 1e-9].copy()

    base01 = _pick(test_stress_df, slip=0.01)
    base02 = _pick(test_stress_df, slip=0.02)

    def _best_row(df: pd.DataFrame, col: str, *, require_pos: bool = False) -> pd.Series | None:
        if df is None or len(df) == 0 or col not in df.columns:
            return None
        d = df.copy()
        if require_pos:
            d = d[d[col].astype(float) > 0]
        if len(d) == 0:
            return None
        return d.sort_values(col, ascending=False, na_position="last").iloc[0]

    r_selected = selected_row
    r_best_tr = _best_row(base01, "total_r")
    r_best_pf = _best_row(base01, "profit_factor_r")
    r_best_cost02 = _best_row(base02, "total_r", require_pos=True)

    def _row_out(rank_type: str, r: pd.Series | None) -> dict[str, Any]:
        if r is None:
            return {"rank_type": rank_type}
        ur = int(r.get("unique_rank", -1) or -1)
        return {
            "rank_type": rank_type,
            "candidate_set": r.get("candidate_set"),
            "top_per_strategy": r.get("top_per_strategy"),
            "max_trades_per_day": r.get("max_trades_per_day"),
            "daily_max_loss_r": r.get("daily_max_loss_r"),
            "cooldown": r.get("cooldown_after_loss_minutes"),
            "priority_policy": r.get("priority_policy"),
            "candidate_ids": r.get("candidate_ids_json"),
            "train_total_r": float(behavior_df[behavior_df["unique_rank"] == ur].iloc[0].get("total_r"))
            if "unique_rank" in behavior_df.columns and len(behavior_df[behavior_df["unique_rank"] == ur])
            else None,
            "train_pf_r": float(behavior_df[behavior_df["unique_rank"] == ur].iloc[0].get("profit_factor_r"))
            if "unique_rank" in behavior_df.columns and len(behavior_df[behavior_df["unique_rank"] == ur])
            else None,
            "train_maxdd_r": float(behavior_df[behavior_df["unique_rank"] == ur].iloc[0].get("max_drawdown_r"))
            if "unique_rank" in behavior_df.columns and len(behavior_df[behavior_df["unique_rank"] == ur])
            else None,
            "train_0_02_total_r": train_slip002_by_ur.get(ur),
            "test_total_r": r.get("total_r"),
            "test_pf_r": r.get("profit_factor_r"),
            "test_maxdd_r": r.get("max_drawdown_r"),
            "test_0_02_total_r": float(
                base02[base02["unique_rank"] == ur].iloc[0].get("total_r")
            )
            if len(base02[base02["unique_rank"] == ur])
            else None,
            "interpretation": "ORACLE (LOOKAHEAD): evaluated on test; never selectable.",
        }

    out = pd.DataFrame(
        [
            _row_out("selected_train", r_selected),
            _row_out("oracle_best_test_total_r", r_best_tr),
            _row_out("oracle_best_test_pf_r", r_best_pf),
            _row_out("oracle_best_test_cost_0_02", r_best_cost02),
        ]
    )
    out.to_csv(out_csv, index=False)
    md = [
        "# ORACLE / LOOKAHEAD DIAGNOSTIC ONLY",
        "",
        "**NOT SELECTABLE.** This is a diagnostic that evaluates train-derived candidate systems on the held-out test window.",
        "",
        f"- evaluated_top_n: **{int(top_n)}**",
        f"- test_window: **{cfg['test']['start']} → {cfg['test']['end']}**",
        "",
        _md_table(out),
        "",
    ]
    out_md.write_text("\n".join(md) + "\n", encoding="utf-8")


def _enrich_summary_placeholders(exp_root: Path, best: pd.Series | None) -> dict[str, str]:
    """Replace placeholder lines in render_mini_wfo_summary_md."""
    out: dict[str, str] = {}

    tsel = exp_root / "train_selected_candidates.csv"
    if tsel.is_file():
        df = pd.read_csv(tsel)
        g = (
            df.groupby("strategy", as_index=False)
            .agg(
                n_candidates=("candidate_id", "count"),
                best_total_r=("total_r", "max"),
                best_pf=("profit_factor", "max"),
                max_trades=("trades", "max"),
                worst_mdd=("max_drawdown_r", "min"),
            )
            .sort_values("strategy")
        )
        out["l1"] = _md_table(g) + "\n"
    else:
        out["l1"] = "*(train_selected_candidates.csv missing)*\n"

    bh = exp_root / "train_layer2_behavior_unique.csv"
    if bh.is_file() and Path(bh).stat().st_size > 0:
        bdf = pd.read_csv(bh)
        cols = [c for c in ("behavior_rank", "candidate_set", "top_per_strategy", "max_trades_per_day", "trades", "total_r", "profit_factor_r", "max_drawdown_r") if c in bdf.columns]
        out["l2"] = _md_table(bdf.head(15)[cols]) + "\n"
    else:
        out["l2"] = "*(no behavior-unique table)*\n"

    if best is not None:
        out["frozen"] = (
            f"- **candidate_set:** {best.get('candidate_set')}\n"
            f"- **candidate_ids:** {best.get('candidate_ids_json')}\n"
            f"- **top_per_strategy:** {best.get('top_per_strategy')}; **max_trades_per_day:** {best.get('max_trades_per_day')}\n"
            f"- **daily_max_loss_r:** {best.get('daily_max_loss_r')}; **cooldown_after_loss_minutes:** {best.get('cooldown_after_loss_minutes')}\n"
            f"- **priority_policy:** {best.get('priority_policy')}\n"
            f"- **Train-window metrics:** trades={best.get('trades')} total_r={best.get('total_r')} "
            f"PF_R={best.get('profit_factor_r')} maxDD_r={best.get('max_drawdown_r')}\n"
        )
    else:
        out["frozen"] = "*(selection row missing)*\n"

    test_root = exp_root / "test"
    mj = test_root / "metrics.json"
    if mj.is_file():
        m = json.loads(mj.read_text(encoding="utf-8"))
        out["test"] = (
            f"| metric | value |\n|---|---:|\n"
            f"| trades | {m.get('trades')} |\n"
            f"| total_r | {m.get('total_r')} |\n"
            f"| profit_factor | {m.get('profit_factor')} |\n"
            f"| profit_factor_r | {m.get('profit_factor_r')} |\n"
            f"| max_drawdown_r | {m.get('max_drawdown_r')} |\n"
            f"| avg_cost_r | {m.get('avg_cost_r')} |\n"
            f"| median_cost_r | {m.get('median_cost_r')} |\n"
        )
        dc = test_root / "cost_stress.csv"
        if dc.is_file():
            cdf = pd.read_csv(dc)
            for slip in (0.02, 0.03):
                row = cdf[(cdf["slippage_per_share"].astype(float) - slip).abs() < 1e-9]
                if len(row):
                    out["test"] += f"| slip_{slip:g}_total_r | {row.iloc[0]['total_r']} |\n"
    else:
        out["test"] = "*(test metrics missing)*\n"

    mb = test_root / "test_monthly_breakdown.csv"
    if not mb.is_file():
        mb = test_root / "monthly_breakdown.csv"
    if mb.is_file():
        mo = pd.read_csv(mb)
        if "total_r" in mo.columns and len(mo):
            mo2 = mo.copy()
            mo2["abs_r"] = mo2["total_r"].astype(float).abs()
            dom = mo2.loc[mo2["abs_r"].idxmax(), "period"] if len(mo2) else ""
            frac = _monthly_concentration(mb)
            out["monthly"] = _md_table(mo[["period", "trades", "total_r", "profit_factor_r", "max_drawdown_r"]]) + "\n\n"
            out["monthly"] += f"- **Largest |monthly total_r|:** {dom} (concentration ratio max|R|/sum|R| ≈ {frac:.2f} if defined).\n"
        else:
            out["monthly"] = "*(empty monthly breakdown)*\n"
    else:
        out["monthly"] = "*(no monthly breakdown)*\n"

    dly = test_root / "test_daily_trade_number_breakdown.csv"
    if not dly.is_file():
        dly = test_root / "daily_trade_number_breakdown.csv"
    if dly.is_file():
        out["daily"] = _md_table(pd.read_csv(dly)) + "\n"
    else:
        out["daily"] = "*(no daily trade number breakdown)*\n"

    cmp_csv = exp_root / "comparison_to_fixed_smoke.csv"
    if cmp_csv.is_file():
        out["cmp"] = _md_table(pd.read_csv(cmp_csv)) + "\n"
    else:
        out["cmp"] = ""

    return out


def _monthly_concentration(mb_path: Path) -> float | None:
    if not mb_path.is_file():
        return None
    df = pd.read_csv(mb_path)
    if "total_r" not in df.columns or len(df) < 2:
        return None
    tr = df["total_r"].astype(float).abs()
    top = float(tr.max())
    s = float(tr.sum()) or 1.0
    return top / s


def _classify_decision(metrics: dict[str, Any], monthly_csv: Path, cost_csv: Path | None = None) -> str:
    tr = float(metrics.get("total_r") or 0.0)
    pfr = float(metrics.get("profit_factor_r") or metrics.get("profit_factor") or 0.0)
    mc = _monthly_concentration(monthly_csv)
    slip02_neg = False
    if cost_csv is not None and cost_csv.is_file():
        cdf = pd.read_csv(cost_csv)
        if "slippage_per_share" in cdf.columns and "total_r" in cdf.columns:
            row02 = cdf[(cdf["slippage_per_share"].astype(float) - 0.02).abs() < 1e-9]
            if len(row02):
                slip02_neg = float(row02.iloc[0]["total_r"]) < 0

    if tr < 0 or pfr < 1.0:
        return "FAIL"
    if slip02_neg:
        return "CAUTION"
    if mc is not None and mc > 0.55:
        return "CAUTION"
    return "PASS"


def _build_final_summary(
    cfg: dict[str, Any],
    exp_root: Path,
    decision: str,
    metrics: dict[str, Any],
    fill: dict[str, str] | None = None,
) -> str:
    tw = f"{cfg['test']['start']} — {cfg['test']['end']}"
    base = render_mini_wfo_summary_md(
        decision=decision,
        train_window=(cfg["train"]["start"], cfg["train"]["end"]),
        test_window=(cfg["test"]["start"], cfg["test"]["end"]),
        body_extra="",
    )
    if fill:
        base = base.replace(
            "(Filled by mini-WFO runner from manifest + selected candidates.)",
            fill.get("l1", ""),
        )
        base = base.replace("(Filled by runner from behavior-unique / cost tables.)", fill.get("l2", ""))
        base = base.replace("(Filled by runner.)", fill.get("frozen", ""), 1)
        base = base.replace("(Filled by runner.)", fill.get("test", ""), 1)
        base = base.replace("(Filled by runner.)", fill.get("monthly", ""), 1)
        base = base.replace("(Filled by runner.)", fill.get("cmp", ""), 1)
        base = base.replace("(Filled by runner based on decision.)", "")
        # Daily trade profile (section 7 follow-up — insert before section 8 if placeholder left)
        if "## 8. Monthly stability" in base and fill.get("daily"):
            base = base.replace(
                "## 8. Monthly stability",
                "### Daily trade-number profile\n\n" + fill["daily"] + "\n## 8. Monthly stability",
            )
    extra = [
        "---",
        "",
        "### Automated classification",
        "",
        f"- Decision: **{decision}**",
        f"- Key test metrics (aggregated): {json.dumps(metrics, indent=2, default=str)}",
        "",
        "### Recommendation",
        "",
    ]
    if decision == "PASS":
        extra.append("Proceed toward **full Layer 3 WFO v1** with a **reduced grid** aligned to this family.")
    elif decision == "CAUTION":
        extra.append("Run **one more mini-WFO** or refine the strategy family before full WFO.")
    else:
        extra.append("Return to **Layer 1 family / diagnosis** before expanding scope.")
    extra.append("")
    return base + "\n".join(extra)


def main(argv: list[str] | None = None) -> int:
    return run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
