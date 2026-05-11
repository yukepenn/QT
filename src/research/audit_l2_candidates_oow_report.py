"""Curated CSV/MD outputs for Layer2 candidate OOW audit (pure pandas, research-only)."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.research.audit_l2_candidates_oow_lib import CandidateMeta, family_group, labels_table_from_wide


def write_candidate_oow_summary_md(*, out: Path, labels: pd.DataFrame) -> None:
    """Compact headline summary for candidate_oow_summary.md."""
    if labels.empty:
        return
    n = len(labels)
    vc = labels["robustness_label"].value_counts()
    pa = labels["policy_action"].value_counts()
    rp = labels.loc[labels["robustness_label"] == "ROBUST_POSITIVE", "candidate_id"].astype(str).tolist()
    io = labels.loc[labels["robustness_label"] == "INSAMPLE_ONLY", "candidate_id"].astype(str).tolist()
    lines = [
        "# Candidate-level OOW audit — compact summary",
        "",
        "## Scope",
        "",
        f"- **Candidates:** {n} (full l2_core singleton grid)",
        "- **Windows:** `early_oow`, `insample_ref`, `late_oow`",
        f"- **Runs:** {n * 3} singleton combiner replays expected (`local_runs/**` local-only)",
        "",
        "## Robustness label counts (candidate-level)",
        "",
        "| robustness_label | count |",
        "|------------------|------:|",
    ]
    for k, v in vc.items():
        lines.append(f"| {k} | {int(v)} |")
    lines += [
        "",
        "## Policy action counts",
        "",
        "| policy_action | count |",
        "|---------------|------:|",
    ]
    for k, v in pa.items():
        lines.append(f"| {k} | {int(v)} |")
    lines += ["", "## ROBUST_POSITIVE", "", "- " + "\n- ".join(sorted(rp)) if rp else "- *(none)*", "", "## INSAMPLE_ONLY", ""]
    lines.append(", ".join(sorted(io)) if io else "*(none)*")
    lines += [
        "",
        "## Artifacts",
        "",
        "- Long metrics: `candidate_oow_metrics.csv`",
        "- Wide + embedded labels: `candidate_oow_wide_metrics.csv`",
        "- Labels: `candidate_robustness_labels.csv`",
        "- Family/strategy rolls: `family_oow_summary.csv`, `strategy_oow_summary.csv`",
        "- Profile-aware join: `l2_core_failure_analysis.csv`",
        "- Manifests: `candidate_audit_run_manifest.csv`, `run_execution_manifest.csv`, `run_discovery_manifest.csv`",
    ]
    (out / "candidate_oow_summary.md").write_text("\n".join(lines), encoding="utf-8")


def _meta_row_for_id(wide: pd.DataFrame, cid: str) -> CandidateMeta:
    r = wide[wide["candidate_id"].astype(str) == cid].iloc[0]
    sc = r.get("selection_score")
    sel = float(sc) if pd.notna(sc) else None
    return CandidateMeta(
        candidate_id=str(cid),
        strategy=str(r["strategy"]),
        strategy_family=str(r["strategy_family"]),
        yaml_path=str(r["yaml_path"]),
        selection_score=sel,
        warning=str(r.get("warning") or ""),
        side=str(r.get("side") or "long"),
    )


def write_compact_highlights(*, out: Path, wide: pd.DataFrame) -> None:
    if wide.empty:
        return
    lab = labels_table_from_wide(wide)
    lab["audit_family"] = lab["candidate_id"].map(lambda cid: family_group(_meta_row_for_id(wide, str(cid))))
    rp = lab[lab["robustness_label"] == "ROBUST_POSITIVE"].copy()
    if "total_r_insample_ref" in rp.columns and not rp.empty:
        rp = rp.sort_values("total_r_insample_ref", ascending=False)
    rp.head(10).to_csv(out / "top_robust_candidates.csv", index=False)
    if {"total_r_early_oow", "total_r_late_oow"}.issubset(lab.columns):
        lab2 = lab.assign(oow_sum=lab["total_r_early_oow"].fillna(0) + lab["total_r_late_oow"].fillna(0))
        lab2.sort_values("oow_sum", ascending=True).head(10).to_csv(out / "worst_oow_candidates.csv", index=False)
        both = lab[(lab["total_r_early_oow"] > 0) & (lab["total_r_late_oow"] > 0)]
        both.to_csv(out / "positive_both_oow_candidates.csv", index=False)
    lab[lab["robustness_label"] == "INSAMPLE_ONLY"].to_csv(out / "insample_only_candidates.csv", index=False)
    lab[lab["robustness_label"] == "ANTI_PREDICTIVE_CANDIDATE"].to_csv(out / "anti_predictive_candidates.csv", index=False)


def write_full_candidate_interpretation(*, out: Path, long_df: pd.DataFrame, wide: pd.DataFrame) -> None:
    lab = labels_table_from_wide(wide) if not wide.empty else pd.DataFrame()
    summary_rows: list[dict[str, object]] = []
    if not wide.empty:
        vc = wide["robustness_label"].value_counts()
        for k, v in vc.items():
            summary_rows.append({"metric": str(k), "count": int(v)})
        if not lab.empty:
            lab2 = lab.assign(oow_sum=lab["total_r_early_oow"].fillna(0) + lab["total_r_late_oow"].fillna(0))
            for _, r in lab2.nsmallest(10, "oow_sum").iterrows():
                summary_rows.append(
                    {
                        "metric": "worst_oow_sum",
                        "count": 0,
                        "candidate_id": r["candidate_id"],
                        "oow_sum": float(r["oow_sum"]),
                        "label": r["robustness_label"],
                    }
                )
            both = lab[(lab["total_r_early_oow"] > 0) & (lab["total_r_late_oow"] > 0)]
            summary_rows.append({"metric": "positive_both_oow_count", "count": int(len(both))})
            cat = lab[(lab["total_r_insample_ref"] < 0) & (lab2["oow_sum"] > 0)]
            summary_rows.append({"metric": "insample_neg_oow_net_pos_count", "count": int(len(cat))})
            ce = lab[lab["total_r_early_oow"] < -40]
            summary_rows.append({"metric": "catastrophic_early_lt_m40_count", "count": int(len(ce))})
    pd.DataFrame(summary_rows).to_csv(out / "full_candidate_oow_interpretation.csv", index=False)
    lines = [
        "# Full candidate OOW interpretation",
        "",
        f"- **long_df rows:** {len(long_df)} (expect **198** = 66 candidates × 3 windows)",
        "",
        "## Long-grid status counts",
        "",
        "```",
        long_df["status"].value_counts().to_string(),
        "```",
        "",
        "## Candidate-level robustness_label counts",
        "",
        "```",
        wide["robustness_label"].value_counts().to_string() if not wide.empty else "(empty)",
        "```",
        "",
    ]
    if not lab.empty:
        lines += [
            "## ROBUST_POSITIVE (all)",
            "",
            "- " + "\n- ".join(sorted(lab.loc[lab["robustness_label"] == "ROBUST_POSITIVE", "candidate_id"].astype(str))),
            "",
            "## ANTI_PREDICTIVE_CANDIDATE (all)",
            "",
        ]
        anti_ids = sorted(lab.loc[lab["robustness_label"] == "ANTI_PREDICTIVE_CANDIDATE", "candidate_id"].astype(str))
        lines.append("- " + "\n- ".join(anti_ids) if anti_ids else "- *(none)*")
        lines += [
            "",
            "## Positive in both OOW windows (early and late total_r > 0)",
            "",
        ]
        both_ids = sorted(
            lab.loc[(lab["total_r_early_oow"] > 0) & (lab["total_r_late_oow"] > 0), "candidate_id"].astype(str)
        )
        lines.append("- " + "\n- ".join(both_ids) if both_ids else "- *(none)*")
        lines += ["", "## Catastrophic early_oow (total_r_early < −40)", ""]
        cata = lab[lab["total_r_early_oow"] < -40].sort_values("total_r_early_oow")
        if cata.empty:
            lines.append("- *(none)*")
        else:
            lines.append(
                "- "
                + "\n- ".join(
                    f"{r['candidate_id']} ({float(r['total_r_early_oow']):.1f} R)" for _, r in cata.iterrows()
                )
            )
        lines += ["", "## OOW_NEGATIVE", ""]
        neg = lab[lab["robustness_label"] == "OOW_NEGATIVE"]
        lines.append("- " + "\n- ".join(sorted(neg["candidate_id"].astype(str))) if len(neg) else "- *(none)*")
        lines.append("")
    (out / "full_candidate_oow_interpretation.md").write_text("\n".join(lines), encoding="utf-8")


def write_family_interpretation(*, out: Path, wide: pd.DataFrame, long_df: pd.DataFrame) -> None:
    if wide.empty:
        return
    w = wide.copy()
    fam_map = long_df.drop_duplicates("candidate_id").set_index("candidate_id")["audit_family"]
    w["audit_family"] = w["candidate_id"].astype(str).map(fam_map.to_dict())
    agg_rows = []
    for fam, g in w.groupby("audit_family"):
        vc = g["robustness_label"].value_counts()
        agg_rows.append(
            {
                "audit_family": fam,
                "candidates": int(len(g)),
                "robust_positive": int(vc.get("ROBUST_POSITIVE", 0)),
                "insample_only": int(vc.get("INSAMPLE_ONLY", 0)),
                "oow_mixed": int(vc.get("OOW_MIXED", 0)),
                "oow_negative": int(vc.get("OOW_NEGATIVE", 0)),
                "too_sparse": int(vc.get("TOO_SPARSE", 0)),
                "anti_predictive": int(vc.get("ANTI_PREDICTIVE_CANDIDATE", 0)),
                "median_r_early": float(g["total_r_early_oow"].median()),
                "median_r_insample": float(g["total_r_insample_ref"].median()),
                "median_r_late": float(g["total_r_late_oow"].median()),
                "mean_r_early": float(g["total_r_early_oow"].mean()),
                "mean_r_insample": float(g["total_r_insample_ref"].mean()),
                "mean_r_late": float(g["total_r_late_oow"].mean()),
                "sum_r_early": float(g["total_r_early_oow"].sum()),
                "sum_r_insample": float(g["total_r_insample_ref"].sum()),
                "sum_r_late": float(g["total_r_late_oow"].sum()),
            }
        )
    df = pd.DataFrame(agg_rows).sort_values("audit_family")
    df.to_csv(out / "full_family_oow_interpretation.csv", index=False)
    hdr = "| " + " | ".join(df.columns) + " |"
    sep = "| " + " | ".join(["---"] * len(df.columns)) + " |"
    body = "\n".join("| " + " | ".join(str(x) for x in row) + " |" for row in df.values.tolist())
    verdict_lines = ["## Family verdict (policy-oriented, heuristic)", ""]
    for _, row in df.iterrows():
        fam = row["audit_family"]
        rp, anti = int(row["robust_positive"]), int(row["anti_predictive"])
        if anti >= 2 and rp == 0:
            tag = "**drop_or_research** (anti-predictive cluster dominates; not a core family as-is)"
        elif anti >= 1 and rp >= 1:
            tag = "**split_family** (some robust YAMLs plus anti-predictive names — core only from robust subset)"
        elif rp >= 2 and anti == 0:
            tag = "**core_candidate** (multiple robust-positive YAMLs; still verify redundancy / YAML independence)"
        elif rp == 0 and int(row["insample_only"]) + int(row["oow_mixed"]) == int(row["candidates"]):
            tag = "**watchlist** (no robust-positive under current thresholds)"
        else:
            tag = "**mixed**"
        verdict_lines.append(f"- **{fam}:** {tag}")
    verdict_lines.append("")
    (out / "full_family_oow_interpretation.md").write_text(
        "# Family OOW interpretation\n\n" + hdr + "\n" + sep + "\n" + body + "\n\n" + "\n".join(verdict_lines),
        encoding="utf-8",
    )


def write_policy_action_summary(*, out: Path, labels: pd.DataFrame) -> None:
    if labels.empty:
        return
    overall = labels["policy_action"].value_counts().reset_index()
    overall.columns = ["policy_action", "count"]
    overall.to_csv(out / "l2_core_policy_v2_action_summary.csv", index=False)
    by_fam = labels.groupby(["audit_family", "policy_action"]).size().reset_index(name="count")
    by_fam.to_csv(out / "l2_core_policy_v2_action_summary_by_family.csv", index=False)


def robust_core_dry_run_decision(
    labels: pd.DataFrame,
    *,
    min_candidates: int = 6,
    min_families: int = 2,
    max_family_share: float = 0.55,
) -> tuple[bool, str, pd.DataFrame]:
    if labels.empty:
        return False, "empty labels", pd.DataFrame()
    keep = labels[labels["policy_action"] == "KEEP_CORE_CANDIDATE"].copy()
    if len(keep) < min_candidates:
        return False, f"KEEP_CORE count {len(keep)} < {min_candidates}", keep
    nf = keep["audit_family"].nunique()
    if nf < min_families:
        return False, f"families with KEEP_CORE {nf} < {min_families}", keep
    top_share = float(keep["audit_family"].value_counts(normalize=True).max())
    if top_share > max_family_share:
        return False, f"single-family share {top_share:.2f} > {max_family_share}", keep
    if "total_r_early_oow" in keep.columns and (keep["total_r_early_oow"] < -15).any():
        return False, "catastrophic early_oow in KEEP_CORE", keep
    if "total_r_late_oow" in keep.columns and (keep["total_r_late_oow"] < -15).any():
        return False, "catastrophic late_oow in KEEP_CORE", keep
    return True, "thresholds met", keep


def write_robust_core_dry_run(*, out: Path, labels: pd.DataFrame) -> None:
    ok, reason, keep = robust_core_dry_run_decision(labels)
    ddir = out / "robust_core_dry_run"
    not_enough = out / "robust_core_not_enough_candidates.md"
    if ok:
        if not_enough.is_file():
            not_enough.unlink()
        ddir.mkdir(parents=True, exist_ok=True)
        keep.to_csv(ddir / "selected_candidates_manifest.csv", index=False)
        fam_ct = keep["audit_family"].value_counts().to_string()
        (ddir / "robust_core_dry_run_summary.md").write_text(
            "# Robust core dry-run\n\n"
            "**Status:** PASS (research-only manifest; **not** a production candidate root)\n\n"
            f"**Gate rationale:** {reason}\n\n"
            f"**KEEP_CORE candidates:** {len(keep)}\n\n"
            "**Families represented (KEEP_CORE):**\n\n"
            f"```\n{fam_ct}\n```\n\n"
            "**Caveats:**\n\n"
            "- `GAP_ACCEPTANCE_FAILURE_001`–`004` replay with **identical** window metrics in this audit — treat as **one effective signal family** for diversity planning.\n"
            "- Dry-run uses the same singleton combiner envelope as the audit (`layer2_fixed_vwap_mtp2.yaml` default).\n",
            encoding="utf-8",
        )
    else:
        if ddir.is_dir():
            for p in ddir.glob("*"):
                p.unlink()
            try:
                ddir.rmdir()
            except OSError:
                pass
        not_enough.write_text(
            f"# Robust core dry-run — not enough candidates\n\n**Status:** FAIL\n\n**Reason:** {reason}\n\n"
            f"**KEEP_CORE count:** {int((labels['policy_action'] == 'KEEP_CORE_CANDIDATE').sum())}\n",
            encoding="utf-8",
        )


def write_side_flip_watchlist(*, out: Path, labels: pd.DataFrame) -> None:
    if labels.empty:
        return
    anti = labels[labels["robustness_label"] == "ANTI_PREDICTIVE_CANDIDATE"]
    sdir = out / "side_flip"
    sdir.mkdir(parents=True, exist_ok=True)
    anti.to_csv(sdir / "future_side_flip_watchlist.csv", index=False)
    note = (
        "\n## Anti-predictive candidates (research queue)\n\n"
        "These are **not** production shorts. Any executable side-flip diagnostic would be a **future** task.\n\n"
    )
    interp = sdir / "side_flip_interpretation.md"
    if interp.is_file():
        cur = interp.read_text(encoding="utf-8")
        if "## Anti-predictive candidates" not in cur:
            interp.write_text(cur + note, encoding="utf-8")
