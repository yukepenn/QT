"""Emit Layer 2 base + sweep YAML for Global QQQ 2023–2024 v2 from an l2_core candidate root."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

OPENING_TRAP = {
    "failed_orb",
    "gap_acceptance_failure",
    "prior_day_level_trap",
    "orb_retest_continuation",
    "orb_continuation",
}
VWAP_CORE = {"vwap_reversal", "vwap_reclaim_reject", "vwap_trend_pullback"}
INDICATOR_CORE = {
    "stochastic_oversold_cross",
    "cci_extreme_snapback",
    "macd_momentum_turn",
    "supertrend_atr_flip",
    "rsi_failure_swing",
    "bollinger_squeeze_breakout",
    "bollinger_band_fade_chop",
    "consecutive_bar_exhaustion",
}


def _strategies_from_l2_csv(csv_path: Path) -> set[str]:
    df = pd.read_csv(csv_path)
    return {str(s).strip() for s in df["strategy"].astype(str)}


def _short_mixed_ids(csv_path: Path, diversity_csv: Path | None) -> tuple[bool, list[str]]:
    """Return (include_long_short_mixed, candidate_ids for that bucket)."""
    df = pd.read_csv(csv_path)
    cids: list[str] = []
    if diversity_csv is not None and diversity_csv.is_file():
        div = pd.read_csv(diversity_csv)
        if "candidate_id" in div.columns and "n_short_signals" in div.columns:
            div = div.set_index("candidate_id")
            for _, r in df.iterrows():
                cid = str(r["candidate_id"])
                if cid in div.index and int(div.loc[cid, "n_short_signals"] or 0) > 0:
                    cids.append(cid)
    if cids:
        return True, sorted(set(cids))
    # Fallback: inspect YAML signal.side
    root = csv_path.parent / "selected_candidates"
    if root.is_dir():
        for yp in sorted(root.glob("*.yaml")):
            doc = yaml.safe_load(yp.read_text(encoding="utf-8"))
            sig = (doc or {}).get("signal") or {}
            side = str(sig.get("side", "")).lower().replace(" ", "_")
            if side in ("both", "short_only", "short"):
                cids.append(str(doc.get("candidate_id", "")))
    cids = [c for c in cids if c]
    return bool(cids), sorted(set(cids))


def _low_turnover_ids(csv_path: Path, max_trades: int = 250) -> list[str]:
    df = pd.read_csv(csv_path)
    if "trades" not in df.columns:
        return []
    t = pd.to_numeric(df["trades"], errors="coerce").fillna(1e9)
    return sorted(df.loc[t <= max_trades, "candidate_id"].astype(str).tolist())


def build_candidate_sets(st: set[str]) -> dict[str, dict]:
    def pack(names: set[str]) -> dict | None:
        hit = sorted(names & st)
        if not hit:
            return None
        return {"include_warnings": False, "max_per_strategy": 4, "strategies": hit}

    sets_cfg: dict[str, dict] = {}
    p = pack(OPENING_TRAP)
    if p:
        sets_cfg["opening_trap_core"] = p
    p = pack(VWAP_CORE)
    if p:
        sets_cfg["vwap_core"] = p
    p = pack(INDICATOR_CORE)
    if p:
        sets_cfg["indicator_completion_core"] = p
    pa = sorted(s for s in st if s.startswith("pa_"))
    if pa:
        sets_cfg["pa_core"] = {"include_warnings": False, "max_per_strategy": 4, "strategies": pa}
    sets_cfg["all_strict_l2_core"] = {"include_warnings": False, "max_per_strategy": 80}
    sets_cfg["all_behavior_diverse"] = {"include_warnings": False, "max_per_strategy": 1}
    return sets_cfg


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--l2-core-csv", type=Path, required=True, help="selected_candidates.csv under l2_core")
    ap.add_argument(
        "--diversity-csv",
        type=Path,
        default=None,
        help="candidate_signal_diversity.csv for short/both detection",
    )
    ap.add_argument("--base-out", type=Path, required=True)
    ap.add_argument("--sweep-out", type=Path, required=True)
    args = ap.parse_args(argv)

    csv_path = args.l2_core_csv
    if not csv_path.is_absolute():
        csv_path = Path.cwd() / csv_path
    st = _strategies_from_l2_csv(csv_path)
    if not st:
        print("ERROR no strategies in l2 csv", file=sys.stderr)
        return 2

    sets_cfg = build_candidate_sets(st)
    low_ids = _low_turnover_ids(csv_path)
    if low_ids:
        sets_cfg["all_low_turnover"] = {
            "include_warnings": False,
            "max_per_strategy": 4,
            "candidate_ids": low_ids,
        }
    mix_ok, mix_ids = _short_mixed_ids(csv_path, args.diversity_csv)
    if mix_ok and mix_ids:
        sets_cfg["long_short_mixed"] = {
            "include_warnings": False,
            "max_per_strategy": 4,
            "candidate_ids": mix_ids,
        }

    rel_root = "src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates"
    base = {
        "name": "layer2_qqq_global_2023_2024_v2",
        "candidate_root": rel_root,
        "execution": {
            "commission_per_trade": 0.0,
            "slippage_per_share": 0.01,
            "eod_exit_minute": 389,
            "no_new_after_minute": 360,
            "recompute_target_from_entry": True,
            "min_risk_per_share": 0.03,
        },
        "system": {
            "max_open_positions": 1,
            "max_trades_per_day": 2,
            "daily_max_loss_r": -2.0,
            "cooldown_after_loss_minutes": 15,
            "cooldown_scope": "session",
        },
        "conflict": {
            "priority_policy": "metadata_priority",
            "same_bar_policy": "priority",
            "tie_breakers": ["candidate_score", "candidate_rank", "candidate_index"],
            "opposite_direction_policy": "",
        },
        "candidate_sets": sets_cfg,
    }

    nonempty_sets: list[str] = []
    for name, prof in sets_cfg.items():
        if name in ("all_strict_l2_core", "all_behavior_diverse"):
            nonempty_sets.append(name)
            continue
        if name == "all_low_turnover" and prof.get("candidate_ids"):
            nonempty_sets.append(name)
            continue
        if name == "long_short_mixed" and prof.get("candidate_ids"):
            nonempty_sets.append(name)
            continue
        if prof.get("strategies"):
            nonempty_sets.append(name)
    nonempty_sets = sorted(set(nonempty_sets))
    if not nonempty_sets:
        print("ERROR no non-empty candidate_set", file=sys.stderr)
        return 2

    sweep = {
        "name": "layer2_sweep_qqq_global_2023_2024_v2",
        "base_config": "src/combiner/configs/layer2_qqq_global_2023_2024_v2.yaml",
        "grid": {
            "candidate_set": nonempty_sets,
            "top_per_strategy": [1, 2],
            "system.max_trades_per_day": [1, 2],
            "system.daily_max_loss_r": [-1.5, -2.0, -3.0],
            "system.cooldown_after_loss_minutes": [0, 15],
            "conflict.priority_policy": ["metadata_priority", "score_adjusted_priority"],
        },
        "fixed": {
            "execution.commission_per_trade": 0.0,
            "execution.slippage_per_share": 0.01,
            "execution.eod_exit_minute": 389,
            "execution.no_new_after_minute": 360,
            "execution.recompute_target_from_entry": True,
            "execution.min_risk_per_share": 0.03,
            "system.max_open_positions": 1,
            "system.cooldown_scope": "session",
        },
    }

    base_out = args.base_out
    sweep_out = args.sweep_out
    if not base_out.is_absolute():
        base_out = Path.cwd() / base_out
    if not sweep_out.is_absolute():
        sweep_out = Path.cwd() / sweep_out
    base_out.parent.mkdir(parents=True, exist_ok=True)
    sweep_out.parent.mkdir(parents=True, exist_ok=True)
    base_out.write_text(yaml.safe_dump(base, sort_keys=False), encoding="utf-8")
    sweep_out.write_text(yaml.safe_dump(sweep, sort_keys=False), encoding="utf-8")
    print(f"Wrote {base_out}", flush=True)
    print(f"Wrote {sweep_out}", flush=True)
    print(f"candidate_sets in grid: {sweep['grid']['candidate_set']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
