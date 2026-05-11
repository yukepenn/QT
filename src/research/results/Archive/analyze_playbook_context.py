"""
Champion v0 playbook / trade-context diagnostics from curated Layer3 + panel aggregates.

Writes `context_diagnostics_v1/` plus static cycle artifacts (freeze, schema, router design, roadmaps).
Research-only; no combiner changes.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import pandas as pd


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "UNKNOWN"


def _parse_list(s: str) -> list[str]:
    return [x.strip() for x in str(s).split(",") if x.strip()]


def _write_champion_freeze(cycle: Path) -> None:
    rows = [
        {
            "profile_id": "pa_only_mtp1_meta",
            "role": "CLEAN_BASELINE",
            "candidate_ids": "PA_BUY_SELL_CLOSE_TREND_003",
            "status": "frozen",
            "reason": "simplest profile; positive all key windows; robustness anchor",
        },
        {
            "profile_id": "pa_gap_mtp2_meta",
            "role": "DEFAULT_COMBINED",
            "candidate_ids": "PA_BUY_SELL_CLOSE_TREND_003;GAP_ACCEPTANCE_FAILURE_001",
            "status": "frozen",
            "reason": "default combined; PA driver; GAP adds early/insample/full",
        },
        {
            "profile_id": "primary_mtp2_meta",
            "role": "BREADTH_REFERENCE_ONLY",
            "candidate_ids": "PA_BUY_SELL_CLOSE_TREND_003;GAP_ACCEPTANCE_FAILURE_001;CCI_EXTREME_SNAPBACK_003",
            "status": "frozen_reference",
            "reason": "highest full R; deeper DD; weaker late_oow — do not promote without new evidence",
        },
    ]
    df = pd.DataFrame(rows)
    df.to_csv(cycle / "champion_v0_freeze.csv", index=False)
    try:
        table = df.to_markdown(index=False)
    except Exception:
        table = df.to_string(index=False)
    md = "\n".join(
        [
            "# Champion v0 freeze",
            "",
            "## Scope",
            "- **Long-only** intraday sleeve on QQQ; **not** a full day-trader system.",
            "- **Not production-ready**; frozen as **benchmark / incumbent** for future router, scalp, and short research.",
            "- Future strategies must **challenge** this frozen incumbent under explicit gates.",
            "",
            "## Frozen profiles",
            "",
            table,
            "",
            "## Do not modify",
            "- Selected candidate YAML parameters for these profiles.",
            "- Signal semantics for embedded strategies.",
            "",
            "## Evidence",
            "- Layer3 complete smoke + expanded stability v1.",
            "",
        ]
    )
    (cycle / "champion_v0_freeze.md").write_text(md, encoding="utf-8")


def _write_trade_context_schema(cycle: Path) -> None:
    # Minimal schema table; full column list per user spec
    cols = [
        ("trade_id", "local trades.csv / metrics", "required", "string", "REQUIRES_LOCAL_DETAILED_REPLAY", "must align to session", "join key"),
        ("profile_id", "run metadata", "required", "string", "UNKNOWN", "from combiner run", "slice"),
        ("candidate_id", "trades.csv", "required", "string", "UNKNOWN", "from combiner", "slice"),
        ("strategy", "candidate yaml", "required", "string", "UNKNOWN", "static map", "router family"),
        ("strategy_family", "taxonomy / yaml", "required", "string", "UNKNOWN", "trade_quality_router taxonomy", "router"),
        ("setup_type", "taxonomy", "optional", "string", "UNKNOWN", "enrichment", "quality"),
        ("playbook", "metadata design", "optional", "string", "UNKNOWN", "router_metadata_v1", "router"),
        ("side", "trades", "required", "string", "long", "Champion v0 long-only", "risk"),
        ("entry_ts_utc", "trades", "required", "datetime", "REQUIRES_LOCAL_DETAILED_REPLAY", "no future timestamps", "sorting"),
        ("exit_ts_utc", "trades", "required", "datetime", "REQUIRES_LOCAL_DETAILED_REPLAY", "", ""),
        ("entry_minute_from_open", "bars", "optional", "int", "REQUIRES_LOCAL_DETAILED_REPLAY", "RTH calendar", "context"),
        ("session_date", "trades", "required", "date", "REQUIRES_LOCAL_DETAILED_REPLAY", "", "join QQQ context"),
        ("window", "run metadata", "required", "string", "UNKNOWN", "from run folder", "slice"),
        ("period_month", "derived", "required", "string", "from session_date", "", "stability"),
        ("period_quarter", "derived", "required", "string", "from session_date", "", "stability"),
        ("r_multiple", "trades", "required", "float", "REQUIRES_LOCAL_DETAILED_REPLAY", "", "PnL"),
        ("exit_reason", "trades", "required", "string", "REQUIRES_LOCAL_DETAILED_REPLAY", "", "mechanics"),
        ("bars_held", "trades", "required", "int", "REQUIRES_LOCAL_DETAILED_REPLAY", "", "management"),
        ("risk_per_share", "trades", "required", "float", "REQUIRES_LOCAL_DETAILED_REPLAY", "", "cost"),
        ("trade_number_of_day", "trades / derived", "required", "int", "REQUIRES_LOCAL_DETAILED_REPLAY", "", "priority"),
        ("prior_trade_r", "derived", "optional", "float", "REQUIRES_LOCAL_DETAILED_REPLAY", "same session sort", "quality"),
        ("prior_trade_same_family", "derived", "optional", "bool", "REQUIRES_LOCAL_DETAILED_REPLAY", "", "repeat"),
        ("same_family_repeat_flag", "derived", "optional", "bool", "REQUIRES_LOCAL_DETAILED_REPLAY", "", "repeat"),
        ("pa_regime_label_20", "FeatureStore @ entry", "optional", "string", "UNKNOWN", "merge_asof backward", "regime"),
        ("pa_regime_label_30", "FeatureStore @ entry", "optional", "string", "UNKNOWN", "", ""),
        ("pa_regime_label_60", "FeatureStore @ entry", "optional", "string", "UNKNOWN", "", ""),
        ("pa_trade_mode_20", "features", "optional", "string", "UNKNOWN", "", ""),
        ("pa_trade_mode_30", "features", "optional", "string", "UNKNOWN", "", ""),
        ("pa_always_in_side_20", "features", "optional", "string", "UNKNOWN", "", ""),
        ("pa_always_in_side_30", "features", "optional", "string", "UNKNOWN", "", ""),
        ("trend_score_20", "features", "optional", "float", "UNKNOWN", "", "context"),
        ("trend_score_30", "features", "optional", "float", "UNKNOWN", "", ""),
        ("range_efficiency_20", "features", "optional", "float", "UNKNOWN", "", ""),
        ("range_efficiency_30", "features", "optional", "float", "UNKNOWN", "", ""),
        ("vwap_cross_count_20", "features", "optional", "int", "UNKNOWN", "", ""),
        ("vwap_cross_count_30", "features", "optional", "int", "UNKNOWN", "", ""),
        ("pa_trading_range_score_20", "features", "optional", "float", "UNKNOWN", "", ""),
        ("pa_climax_score_20", "features", "optional", "float", "UNKNOWN", "", ""),
        ("pa_late_trend_score_20", "features", "optional", "float", "UNKNOWN", "", ""),
        ("pa_distance_from_vwap_atr", "features", "optional", "float", "UNKNOWN", "", ""),
        ("close_above_vwap", "features", "optional", "bool", "UNKNOWN", "", ""),
        ("close_below_vwap", "features", "optional", "bool", "UNKNOWN", "", ""),
        ("vwap_slope_20", "features", "optional", "float", "UNKNOWN", "", ""),
        ("gap_atr", "features", "optional", "float", "UNKNOWN", "", ""),
        ("orb_context", "features", "optional", "string", "UNKNOWN", "", ""),
        ("above_orb_high", "features", "optional", "bool", "UNKNOWN", "", ""),
        ("below_orb_low", "features", "optional", "bool", "UNKNOWN", "", ""),
        ("near_prior_close_atr", "features", "optional", "float", "UNKNOWN", "", ""),
        ("market_context_label", "QQQ panel join", "optional", "string", "unknown_mixed", "session→month label", "router"),
        ("context_bucket", "derived", "optional", "string", "UNKNOWN", "map router buckets", "router"),
        ("playbook_fit", "derived", "optional", "string", "UNKNOWN", "metadata rules", "router"),
        ("trade_quality_bucket", "score v2", "optional", "string", "UNKNOWN", "offline score", "filter"),
        ("cost_as_R", "derived", "optional", "float", "UNKNOWN", "slip model", "stress"),
        ("weak_period_flag", "expanded stability", "optional", "bool", "from quarter list", "2025Q1/2022Q4/2023Q3", "diag"),
        ("management_mode_hypothesis", "exit overlay design", "optional", "string", "UNKNOWN", "map setup+context", "overlay"),
    ]
    sdf = pd.DataFrame(
        cols,
        columns=["name", "source", "required_or_optional", "data_type", "fallback_if_missing", "no_lookahead_notes", "intended_analysis_use"],
    )
    sdf.to_csv(cycle / "trade_context_panel_schema.csv", index=False)
    (cycle / "trade_context_panel_schema.md").write_text(
        "\n".join(
            [
                "# trade_context_panel_schema",
                "",
                "Row-level panel is **not** committed; see `trade_context_panel_schema.csv` for column contract.",
                "",
                "## Principles",
                "- All feature joins at **entry** use **backward** `merge_asof` (no lookahead).",
                "- Champion v0 remains **long-only** in this cycle.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_router_metadata(cycle: Path) -> None:
    d = cycle / "router_metadata_v1"
    d.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "candidate_or_family": "PA_BUY_SELL_CLOSE_TREND_003",
            "current_or_future": "current",
            "strategy": "pa_buy_sell_close_trend",
            "family": "price_action",
            "setup_type": "trend_close",
            "playbook": "trend_swing_long",
            "direction": "long",
            "management_mode_hypothesis": "trend_swing",
            "preferred_contexts": "trend_long;always_in_long",
            "neutral_contexts": "unknown_mixed",
            "avoid_contexts": "late_climax;high_chop",
            "required_level_context": "VWAP / channel structure",
            "freshness_notes": "entry near signal bar",
            "risk_notes": "max_hold dependency in smoke",
            "current_evidence_status": "Champion v0 positive windows",
            "next_research_step": "trade-level regime join",
        },
        {
            "candidate_or_family": "GAP_ACCEPTANCE_FAILURE_001",
            "current_or_future": "current",
            "strategy": "gap_acceptance_failure",
            "family": "gap",
            "setup_type": "gap_failure",
            "playbook": "gap_mean_reversion_long",
            "direction": "long",
            "management_mode_hypothesis": "scalp",
            "preferred_contexts": "gap_failure;opening_drive",
            "neutral_contexts": "unknown_mixed",
            "avoid_contexts": "late_climax",
            "required_level_context": "opening range / prior close",
            "freshness_notes": "first hour bias",
            "risk_notes": "small late_oow incremental R in smoke",
            "current_evidence_status": "additive early/insample/full",
            "next_research_step": "router downweight in unknown_mixed if replay confirms",
        },
        {
            "candidate_or_family": "CCI_EXTREME_SNAPBACK_003",
            "current_or_future": "current",
            "strategy": "cci_extreme_snapback",
            "family": "indicator",
            "setup_type": "snapback",
            "playbook": "breadth_reversion_long",
            "direction": "long",
            "management_mode_hypothesis": "reversal",
            "preferred_contexts": "trading_range",
            "neutral_contexts": "trend_long",
            "avoid_contexts": "late_climax",
            "required_level_context": "extreme extension",
            "freshness_notes": "indicator reset",
            "risk_notes": "higher full DD vs PA-only",
            "current_evidence_status": "reference only in Champion v0",
            "next_research_step": "CCI vs PA overlap diagnostic on trades",
        },
    ]
    for fam in (
        "pa_range_scalp_long",
        "pa_range_scalp_short",
        "gap_up_failure_short",
        "vwap_rejection_short",
        "orb_failed_breakout_short",
        "pa_sell_close_trend_short",
        "late_climax_reversal_short",
    ):
        rows.append(
            {
                "candidate_or_family": fam,
                "current_or_future": "future",
                "strategy": "DESIGN_ONLY_NOT_IMPLEMENTED",
                "family": "DESIGN_ONLY_NOT_IMPLEMENTED",
                "setup_type": "DESIGN_ONLY_NOT_IMPLEMENTED",
                "playbook": "DESIGN_ONLY_NOT_IMPLEMENTED",
                "direction": "long_or_short",
                "management_mode_hypothesis": "scalp_or_reversal",
                "preferred_contexts": "TBD",
                "neutral_contexts": "TBD",
                "avoid_contexts": "TBD",
                "required_level_context": "TBD",
                "freshness_notes": "TBD",
                "risk_notes": "do not contaminate Champion v0",
                "current_evidence_status": "DESIGN_ONLY_NOT_IMPLEMENTED",
                "next_research_step": "Layer1 isolation after router diagnostics",
            }
        )
    df = pd.DataFrame(rows)
    df.to_csv(d / "candidate_playbook_metadata.csv", index=False)
    (d / "candidate_playbook_metadata.md").write_text(
        "# candidate_playbook_metadata\n\nSee `candidate_playbook_metadata.csv`. Future rows are **DESIGN_ONLY_NOT_IMPLEMENTED**.\n",
        encoding="utf-8",
    )


def _write_router_design(cycle: Path) -> None:
    d = cycle / "router_design_v1"
    d.mkdir(parents=True, exist_ok=True)
    rules = [
        ("R001", "trend_long", "trend_swing_long", "prefer", "PA_BUY_SELL_CLOSE_TREND_003", "PA trend-close fits trend_long", "complete smoke", "higher hit-rate hypothesis", "medium", "offline_diagnostic_v1"),
        ("R002", "gap_failure", "gap_mean_reversion_long", "prefer", "GAP_ACCEPTANCE_FAILURE_001", "gap playbook in gap context", "candidate metadata", "targeted exposure", "medium", "offline_diagnostic_v1"),
        ("R003", "unknown_mixed", "gap_mean_reversion_long", "downweight", "GAP_ACCEPTANCE_FAILURE_001", "late_oow GAP small; avoid overweight", "expanded stability", "reduce noise", "high", "offline_diagnostic_v1"),
        ("R004", "high_chop", "trend_swing_long", "downweight", "PA_BUY_SELL_CLOSE_TREND_003", "trend-chase risk in chop", "market_context_labels", "fewer false trends", "medium", "offline_diagnostic_v1"),
        ("R005", "trading_range", "scalp_long_future", "neutral", "pa_range_scalp_long", "future strategy only", "roadmap", "no live trades", "low", "future_layer1_only"),
        ("R006", "late_climax", "trend_swing_long", "block_for_diagnostic", "PA_BUY_SELL_CLOSE_TREND_003", "avoid new trend chase", "exit overlay design", "protect tail", "medium", "offline_diagnostic_v1"),
        ("R007", "unknown_mixed", "ALL", "neutral", "ALL", "default neutral not block", "router policy", "baseline", "low", "offline_diagnostic_v1"),
        ("R008", "trend_short_diagnostic", "ALL", "block_for_diagnostic", "ALL", "short not in Champion v0", "Champion freeze", "isolation", "low", "short_branch_future"),
    ]
    rdf = pd.DataFrame(
        rules,
        columns=[
            "rule_id",
            "context_bucket",
            "playbook",
            "action",
            "candidate_or_family",
            "reason",
            "evidence_source",
            "expected_effect",
            "risk_of_overfit",
            "implementation_phase",
        ],
    )
    rdf.to_csv(d / "offline_router_rule_design.csv", index=False)
    (d / "offline_router_rule_design.md").write_text(
        "# offline_router_rule_design\n\nConservative **offline** router v1 — **not** wired into combiner.\n",
        encoding="utf-8",
    )
    yaml_text = "\n".join(
        [
            "# Router v1 config draft — DESIGN ONLY",
            "enabled: false",
            "mode: offline_diagnostic",
            "version: 0.1.0",
            "notes:",
            "  - Do not import from combiner production paths.",
            "  - Context buckets are diagnostic labels only.",
            "context_buckets:",
            "  - trend_long",
            "  - trend_short_diagnostic",
            "  - trading_range",
            "  - gap_failure",
            "  - late_climax",
            "  - high_chop",
            "  - unknown_mixed",
            "default_action: neutral",
        ]
    )
    (d / "router_v1_config_draft.yaml").write_text(yaml_text + "\n", encoding="utf-8")


def _write_trade_quality_v2(cycle: Path) -> None:
    d = cycle / "trade_quality_score_v2"
    d.mkdir(parents=True, exist_ok=True)
    comp = [
        ("regime_fit_score", "alignment of trade setup to regime labels", "pa_regime_*; context_bucket", "uniform if missing", "0-1 then ×30%", "entry-time labels only", "overfit if too many bins"),
        ("level_context_score", "distance to VWAP / ORB / prior levels", "level features @ entry", "0.5 neutral", "0-1 ×20%", "backward merge", "medium"),
        ("signal_strength_score", "normalized signal strength proxy", "indicator/PA strength cols", "0.5 neutral", "0-1 ×20%", "", "high"),
        ("cost_safety_score", "spread/slip vs risk_per_share", "risk_per_share; slip model", "from cost stress tables", "0-1 ×15%", "", "medium"),
        ("freshness_score", "time since signal / bar age", "entry bar index", "0.5 if missing", "0-1 ×15%", "", "medium"),
    ]
    pd.DataFrame(
        comp,
        columns=["component", "definition", "input_columns", "fallback_if_missing", "score_range", "no_lookahead_notes", "risk_of_overfit"],
    ).to_csv(d / "trade_quality_score_design.csv", index=False)
    (d / "trade_quality_score_design.md").write_text(
        "\n".join(
            [
                "# trade_quality_score_design v2",
                "",
                "Weights: regime_fit 30%, level 20%, signal 20%, cost_safety 15%, freshness 15% → **sum = 100%**.",
                "",
                "## Buckets",
                "- **A**: composite ≥ 75",
                "- **B**: 55–75",
                "- **C**: < 55",
                "",
                "**Not implemented** in combiner in this task.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    tests = [
        ("all_trades", "row_panel", "none", "full distribution", "baseline", "reference"),
        ("ab_only", "row_panel", "bucket in {A,B}", "truncated hist", "compare to baseline", "selection bias risk"),
        ("a_only", "row_panel", "bucket==A", "strict", "max quality", "sample size risk"),
        ("avoid_removed", "row_panel", "context not in avoid list", "filtered", "improved tail?", "overfit"),
        ("prefer_only", "row_panel", "context in prefer list", "filtered", "concentrated edge?", "regime leak"),
    ]
    pd.DataFrame(
        tests,
        columns=["test_name", "input_trades", "filter_rule", "expected_output", "pass_condition", "risk"],
    ).to_csv(d / "quality_score_v2_test_plan.csv", index=False)


def _write_exit_overlay(cycle: Path) -> None:
    d = cycle / "exit_overlay_design_v1"
    d.mkdir(parents=True, exist_ok=True)
    modes = [
        ("scalp", "trading_range;gap_failure;vwap_reclaim_reject", "shorter target; shorter max_hold; NFT exit; no trail", "0.8R/1.0R/1.2R sweep", "same-bar target+stop → mark ambiguous; conservative fill worse of fill pair"),
        ("trend_swing", "trend_long;always_in_long;bull_channel", "wider target; longer max_hold; optional trail after +1R", "trail only after +1R", "regime degradation exit"),
        ("runner", "strong_trend_day;always_in_long;no_late_climax", "partial + trail VWAP/swing/ATR", "EOD flatten", "flip always-in → exit"),
        ("reversal", "late_climax;failed_breakout;trap", "tight invalidation; NFT 2–3 bars", "smaller target", "ambiguous bar → skip trail"),
    ]
    pd.DataFrame(
        modes,
        columns=["management_mode", "preferred_contexts", "behavior_summary", "future_test_axes", "conservative_intrabar_note"],
    ).to_csv(d / "exit_overlay_design.csv", index=False)
    (d / "exit_overlay_design.md").write_text(
        "# exit_overlay_design v1\n\n**Design only.** No engine changes. No global trailing stop.\n",
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            ("scalp_target_sweep", "offline replay", "target 0.8/1.0/1.2R", "PnL vs baseline", "not worse on cost stress", "overfit"),
            ("max_hold_shorten", "offline replay", "max_hold -20%", "drawdown", "DD reduction", "trade count drop"),
        ],
        columns=["test_name", "input_trades", "parameter_change", "metric", "pass_condition", "risk"],
    ).to_csv(d / "exit_overlay_test_plan.csv", index=False)


def _write_scalp_roadmap(cycle: Path) -> None:
    d = cycle / "scalp_strategy_roadmap_v1"
    d.mkdir(parents=True, exist_ok=True)
    longs = ["pa_range_scalp_long", "vwap_reclaim_scalp_long", "failed_breakdown_scalp_long", "gap_failure_scalp_long"]
    shorts = ["pa_range_scalp_short", "vwap_rejection_scalp_short", "failed_breakout_scalp_short", "gap_up_failure_scalp_short"]
    rows = []
    for x in longs:
        rows.append(
            {
                "family_id": x,
                "direction": "long",
                "status": "DESIGN_ONLY_NOT_IMPLEMENTED",
                "setup_definition": "TBD: tight range fade / VWAP scalp long",
                "preferred_market_context": "trading_range;gap_failure",
                "required_features": "pa_range; vwap; volume",
                "implementation_risk": "medium",
                "layer1_test_plan": "QQQ strict YAML small grid only",
            }
        )
    for x in shorts:
        rows.append(
            {
                "family_id": x,
                "direction": "short",
                "status": "DESIGN_ONLY_NOT_IMPLEMENTED",
                "setup_definition": "TBD: mirror long scalp with short triggers",
                "preferred_market_context": "TBD",
                "required_features": "symmetric short primitives (future)",
                "implementation_risk": "high",
                "layer1_test_plan": "isolated short branch only — not mixed with Champion v0",
            }
        )
    pd.DataFrame(rows).to_csv(d / "scalp_strategy_roadmap.csv", index=False)
    (d / "scalp_strategy_roadmap.md").write_text(
        "# scalp_strategy_roadmap v1\n\nAll rows **DESIGN_ONLY_NOT_IMPLEMENTED**. Do not add strategies in this commit.\n",
        encoding="utf-8",
    )


def _write_short_roadmap(cycle: Path) -> None:
    d = cycle / "short_strategy_roadmap_v1"
    d.mkdir(parents=True, exist_ok=True)
    fams = [
        "gap_up_failure_short",
        "vwap_rejection_short",
        "orb_failed_breakout_short",
        "pa_sell_close_trend_short",
        "range_high_failure_short",
        "late_climax_reversal_short",
    ]
    rows = []
    for f in fams:
        rows.append(
            {
                "family_id": f,
                "status": "DESIGN_ONLY_NOT_IMPLEMENTED",
                "why_not_inverse_long": "short liquidity / borrow / symmetry breaks; different failure modes",
                "preferred_context": "TBD",
                "stop_logic": "TBD",
                "target_logic": "TBD",
                "expected_trade_frequency": "lower than long sleeve",
                "expected_failure_mode": "squeeze / macro gap",
                "layer1_short_only_plan": "SPY/QQQ short-only harness (future)",
                "oow_before_mixing": "required",
            }
        )
    pd.DataFrame(rows).to_csv(d / "short_strategy_roadmap.csv", index=False)
    (d / "short_strategy_roadmap.md").write_text(
        "# short_strategy_roadmap v1\n\n**No short implementation** in this task. No side-flip research.\n",
        encoding="utf-8",
    )


def _write_next_sweep(cycle: Path) -> None:
    cycles = [
        ("Cycle_1", "Router diagnostics against Champion v0", "existing trades (local) + curated summaries", "offline router / quality / exit overlay diagnostics", "diag CSV/MD; no combiner wiring", "clear attribution + permissioning story", "no new strategies; no broad Layer2", "CONTINUE_OR_HOLD"),
        ("Cycle_2", "Router-integrated controlled Layer2", "Champion v0 candidates only", "router off/on; quality all / A+B / A; permission neutral/downweight/block-diagnostic", "small controlled L2 outputs", "improved vs baseline under same cost model", "no broad Layer2 grid", "GATE_FOR_LAYER2_INTEGRATION"),
        ("Cycle_3", "Scalp long-side additions", "roadmap long scalp families", "Layer1 only for 2–4 families; strict candidate YAMLs", "Layer1 shortlist", "OOW / smoke gates on new families only", "no short; no mix into default combined yet", "SELECT_SCALP_LONG"),
        ("Cycle_4", "Short-side branch", "short roadmap families", "short-only Layer1 + OOW", "standalone short metrics", "pass short-only gates before any mix", "no Champion v0 contamination", "ISOLATE_SHORT"),
        ("Cycle_5", "Integrated Layer2", "Champion v0 + router-approved scalp + validated short (if any)", "controlled combinations; trade-quality score", "smoke + cost stress", "gates vs frozen v0", "no broad exploration", "MERGE_CANDIDATE"),
        ("Cycle_6", "Layer3 fixed profiles", "frozen profile set post-Cycle_5", "smoke; OOW; stability", "Layer3 artifacts pack", "stability labels acceptable", "no production promotion", "BETA_READINESS"),
        ("Cycle_7", "Reduced WFO", "QQQ only; frozen candidates; small grid", "train-only selection; test-only evaluation", "WFO-lite metrics", "no leakage; stable test", "not full WFO", "WFO_LITE_DECISION"),
    ]
    pd.DataFrame(
        cycles,
        columns=["cycle_id", "purpose", "inputs", "actions", "outputs", "pass_condition", "explicit_non_goals", "expected_decision"],
    ).to_csv(cycle / "next_3layer_sweep_roadmap.csv", index=False)
    (cycle / "next_3layer_sweep_roadmap.md").write_text(
        "# next_3layer_sweep_roadmap\n\nSeven-cycle progression from **offline diagnostics** → **WFO-lite**.\n",
        encoding="utf-8",
    )


def _build_diagnostics(
    *,
    cycle: Path,
    panel: Path,
    smoke: Path,
    exp: Path,
    profiles: list[str],
    windows: list[str],
) -> None:
    diag = cycle / "context_diagnostics_v1"
    diag.mkdir(parents=True, exist_ok=True)
    win = pd.read_csv(smoke / "complete_profile_window_summary.csv")
    win = win[win["profile_id"].isin(profiles) & win["window"].isin(windows)]
    cand = pd.read_csv(smoke / "complete_candidate_contribution.csv")
    cand = cand[cand["profile_id"].isin(profiles) & cand["window"].isin(windows)]
    exr = pd.read_csv(smoke / "complete_exit_reason_summary.csv")
    exr = exr[exr["profile_id"].isin(profiles) & exr["window"].isin(windows)]
    tnum = pd.read_csv(smoke / "complete_trade_number_summary.csv")
    tnum = tnum[tnum["profile_id"].isin(profiles) & tnum["window"].isin(windows)]

    # profile summary: pivot windows
    pv = win.pivot_table(index="profile_id", columns="window", values="total_r", aggfunc="sum")
    pv.columns = [f"total_r_{c}" for c in pv.columns]
    pv = pv.reset_index()
    pv.to_csv(diag / "profile_context_summary.csv", index=False)
    try:
        md_tbl = pv.to_markdown(index=False)
    except Exception:
        md_tbl = pv.to_string(index=False)
    (diag / "profile_context_summary.md").write_text(
        "# profile_context_summary\n\nWindow-level **total_r** pivot from `complete_profile_window_summary.csv` (curated).\n\n" + md_tbl + "\n",
        encoding="utf-8",
    )

    for pid, fn in (
        ("pa_only_mtp1_meta", "pa_only_context_summary.csv"),
        ("pa_gap_mtp2_meta", "pa_gap_context_summary.csv"),
        ("primary_mtp2_meta", "primary_context_summary.csv"),
    ):
        sub = win[win["profile_id"] == pid]
        sub.to_csv(diag / fn, index=False)
        (diag / fn.replace(".csv", ".md")).write_text(f"# {fn}\n\nSee `{fn}`.\n", encoding="utf-8")

    wp = exp / "weak_period_profile_pnl.csv"
    if wp.is_file():
        pd.read_csv(wp).to_csv(diag / "weak_period_context_summary.csv", index=False)
    else:
        pd.DataFrame([{"note": "weak_period_profile_pnl.csv missing"}]).to_csv(diag / "weak_period_context_summary.csv", index=False)
    (diag / "weak_period_context_summary.md").write_text("# weak_period_context_summary\n", encoding="utf-8")

    # gap increment: pa_gap vs pa_only same window (total_r delta proxy)
    rows = []
    pa_only = win[win["profile_id"] == "pa_only_mtp1_meta"].set_index("window")["total_r"]
    pa_gap = win[win["profile_id"] == "pa_gap_mtp2_meta"].set_index("window")["total_r"]
    for w in windows:
        if w in pa_only.index and w in pa_gap.index:
            rows.append(
                {
                    "context_proxy": w,
                    "pa_only_total_r": float(pa_only.loc[w]),
                    "pa_gap_total_r": float(pa_gap.loc[w]),
                    "gap_increment_total_r": float(pa_gap.loc[w] - pa_only.loc[w]),
                    "interpretation": "window-level proxy; REQUIRES_LOCAL_DETAILED_REPLAY for true gap slice",
                }
            )
    pd.DataFrame(rows).to_csv(diag / "gap_increment_by_context.csv", index=False)

    # CCI increment: primary vs pa_gap total by window
    cci_rows = []
    prim = win[win["profile_id"] == "primary_mtp2_meta"].set_index("window")["total_r"]
    for w in windows:
        if w in prim.index and w in pa_gap.index:
            cci_rows.append(
                {
                    "context_proxy": w,
                    "pa_gap_total_r": float(pa_gap.loc[w]),
                    "primary_total_r": float(prim.loc[w]),
                    "primary_increment_vs_pa_gap": float(prim.loc[w] - pa_gap.loc[w]),
                    "note": "CCI bundled; not isolated at trade level without replay",
                }
            )
    pd.DataFrame(cci_rows).to_csv(diag / "cci_increment_by_context.csv", index=False)

    tnum.to_csv(diag / "trade_number_context_summary.csv", index=False)
    (diag / "trade_number_context_summary.md").write_text("# trade_number_context_summary\n", encoding="utf-8")
    exr.to_csv(diag / "exit_reason_context_summary.csv", index=False)
    (diag / "exit_reason_context_summary.md").write_text("# exit_reason_context_summary\n", encoding="utf-8")

    findings = [
        {
            "topic": "PA_only_best",
            "detail": "Window-level: `pa_only_mtp1_meta` total_r exceeds `pa_gap_mtp2_meta` on **late_oow** in complete smoke; `pa_gap_mtp2_meta` leads on **early_oow**, **insample_ref**, and **full_available**.",
            "evidence": "complete_profile_window_summary.csv; gap_increment_by_context.csv",
            "limitation": "REQUIRES_LOCAL_DETAILED_REPLAY for PA regime / true context buckets at trade entry",
        },
        {
            "topic": "GAP_late_oow",
            "detail": "Candidate table shows small GAP total_r in late_oow vs early — consistent with expanded stability.",
            "evidence": "complete_candidate_contribution.csv",
            "limitation": "cannot separate context without trade-level join",
        },
        {
            "topic": "CCI_reference",
            "detail": "primary adds full-span R but weaker late_oow vs PA-only in smoke recap.",
            "evidence": "complete_profile_window_summary.csv",
            "limitation": "trade-level CCI attribution REQUIRES_LOCAL_DETAILED_REPLAY",
        },
    ]
    pd.DataFrame(findings).to_csv(diag / "context_diagnostics_key_findings.csv", index=False)
    (diag / "context_diagnostics_summary.md").write_text(
        "\n".join(
            [
                "# context_diagnostics_summary",
                "",
                "Aggregated diagnostics from **curated** summaries only.",
                "",
                "## Limitations",
                "- No row-level **PA regime** or **per-trade market_context** without local replay + FeatureStore join.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def _write_decision(cycle: Path) -> None:
    text = "\n".join(
        [
            "# playbook_router_cycle_v1_decision",
            "",
            "## Decision: `RUN_LOCAL_DETAILED_TRADE_CONTEXT_REPLAY`",
            "",
            "### Rationale",
            "- Champion v0 is **frozen** and documented; strategic shift is to **context/router/quality** — not more strategies.",
            "- Trade-context **schema** and **offline router / quality / exit / roadmaps** are specified for the next cycle.",
            "- **Row-level** columns (regime at entry, true `market_context_label` per trade, `prior_trade_r`, bars_held) are **not** present in committed `complete_*` CSVs.",
            "- Aggregated diagnostics answer **window-level** PA vs PA+GAP vs primary questions only.",
            "- Next increment to reduce unknowns is a **local-only** trade tape + backward-asof feature join (not committed).",
            "",
            "### Recommended next step",
            "- Run **local-only** Layer3 Champion v0 replay enrichment (existing tooling: `fixed_profile_oow` / trade enrich patterns) to materialize a **row-level** trade-context panel on disk, then re-run offline router scoring.",
            "",
            "### Explicit non-runs",
            "- No WFO / live / SPY / broad L2 / combiner router wiring / new strategies / YAML edits / short implementation.",
            "",
        ]
    )
    (cycle / "playbook_router_cycle_v1_decision.md").write_text(text, encoding="utf-8")


def _write_bundle_and_map(cycle: Path) -> None:
    key = pd.DataFrame(
        [
            ("Champion", "pa_only_mtp1_meta", "role", "CLEAN_BASELINE", "anchor"),
            ("Champion", "pa_gap_mtp2_meta", "role", "DEFAULT_COMBINED", "default"),
            ("Champion", "primary_mtp2_meta", "role", "BREADTH_REFERENCE_ONLY", "not promoted"),
            ("Decision", "cycle_v1", "label", "RUN_LOCAL_DETAILED_TRADE_CONTEXT_REPLAY", "row-level panel blocking"),
        ],
        columns=["section", "item", "metric", "value", "interpretation"],
    )
    key.to_csv(cycle / "chatgpt_key_tables.csv", index=False)
    bundle = "\n".join(
        [
            "# CHATGPT_REVIEW_BUNDLE — Playbook Router Research Cycle v1",
            "",
            "## 1) Git / validation",
            f"- git_tip: `{_git_head()}`",
            "",
            "## 2) Why Champion v0 is frozen",
            "- See `champion_v0_freeze.md`",
            "",
            "## 3) Champion v0 roles",
            "- PA-only baseline; PA+GAP default; primary/CCI reference-only.",
            "",
            "## 4) Stop over-polishing strategies",
            "- Pivot to **context permissioning**, **trade quality**, **exit management**, and **isolated short/scalp** branches later.",
            "",
            "## 5) Trade-context panel",
            "- Schema: `trade_context_panel_schema.csv`",
            "- Aggregates: `trade_context_panel_v1/`",
            "- Missing: `trade_context_missing_inputs.csv`",
            "",
            "## 6) Context diagnostics",
            "- `context_diagnostics_v1/context_diagnostics_summary.md`",
            "",
            "## 7) Candidate playbook metadata",
            "- `router_metadata_v1/candidate_playbook_metadata.csv`",
            "",
            "## 8) Offline router design",
            "- `router_design_v1/offline_router_rule_design.csv` + `router_v1_config_draft.yaml` (`enabled: false`)",
            "",
            "## 9) Trade-quality score v2",
            "- `trade_quality_score_v2/trade_quality_score_design.md` (weights sum to 100%)",
            "",
            "## 10) Exit overlay design",
            "- `exit_overlay_design_v1/exit_overlay_design.csv`",
            "",
            "## 11) Scalp roadmap",
            "- `scalp_strategy_roadmap_v1/` — all **DESIGN_ONLY_NOT_IMPLEMENTED**",
            "",
            "## 12) Short roadmap",
            "- `short_strategy_roadmap_v1/` — **DESIGN_ONLY_NOT_IMPLEMENTED**",
            "",
            "## 13) Next 3-layer sweep",
            "- `next_3layer_sweep_roadmap.csv`",
            "",
            "## 14) Decision",
            "- **`RUN_LOCAL_DETAILED_TRADE_CONTEXT_REPLAY`**",
            "",
            "## 15) Explicit non-runs",
            "- No WFO/live/SPY/broad L2/new strategies/router implementation/YAML edits",
            "",
            "## 16) Recommended next step",
            "- Local-only row-level trade-context build + backward feature join (disk only), then offline router diagnostics.",
            "",
        ]
    )
    (cycle / "CHATGPT_REVIEW_BUNDLE.md").write_text(bundle, encoding="utf-8")
    rows = []
    for p in sorted(cycle.rglob("*")):
        if p.is_file() and p.suffix in {".csv", ".md", ".yaml"}:
            rel = "src/research/results/playbook_router_research_cycle_v1/" + str(p.relative_to(cycle)).replace("\\", "/")
            rc = 0
            if p.suffix == ".csv":
                lines = p.read_text(encoding="utf-8").splitlines()
                rc = max(0, len(lines) - 1) if lines else 0
            req = "yes" if p.name in ("CHATGPT_REVIEW_BUNDLE.md", "SOURCE_MAP.csv") else "optional"
            rows.append(
                {
                    "file_path": rel,
                    "purpose": "playbook_router_cycle_v1",
                    "required_for_review": req,
                    "row_count_if_csv": rc if p.suffix == ".csv" else "",
                    "markdown_mirror_available": "yes" if p.suffix == ".md" else "no",
                    "notes": "",
                }
            )
    pd.DataFrame(rows).to_csv(cycle / "SOURCE_MAP.csv", index=False)


def _write_baseline_inventory(cycle: Path) -> None:
    txt = "\n".join(
        [
            "# baseline_inventory",
            "",
            f"- git_tip_at_run: `{_git_head()}`",
            "- formal_decision_prior: `PROCEED_TO_PRE_WFO_STABILITY_DESIGN` (expanded stability v1)",
            "",
            "## Champion v0 (frozen)",
            "- `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`, `primary_mtp2_meta` (reference)",
            "",
            "## Files inspected",
            "- `NEXT_HANDOFF.md`, `layer3_expanded_stability_v1/**`, `layer3_fixed_profile_smoke_complete_v1/**`",
            "",
            "## This task",
            "- Freeze + schema + offline router/quality/exit designs + roadmaps + aggregated diagnostics.",
            "- **Does not** run WFO, live, SPY, broad L2, or add strategies.",
            "",
            "## Local detailed trades",
            "- **Needed** for full trade-context panel per `playbook_router_cycle_v1_decision.md`.",
            "",
        ]
    )
    (cycle / "baseline_inventory.md").write_text(txt, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Playbook router cycle v1 — diagnostics + static artifacts.")
    p.add_argument("--cycle-root", default="src/research/results/playbook_router_research_cycle_v1")
    p.add_argument("--complete-smoke-root", default="src/research/results/layer3_fixed_profile_smoke_complete_v1")
    p.add_argument("--expanded-stability-root", default="src/research/results/layer3_expanded_stability_v1")
    p.add_argument("--panel-root", default="src/research/results/playbook_router_research_cycle_v1/trade_context_panel_v1")
    p.add_argument("--profiles", default="pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta")
    p.add_argument("--windows", default="early_oow,insample_ref,late_oow,full_available")
    p.add_argument("--skip-panel-build", action="store_true")
    args = p.parse_args(argv)

    cycle = Path(args.cycle_root)
    cycle.mkdir(parents=True, exist_ok=True)
    smoke = Path(args.complete_smoke_root)
    exp = Path(args.expanded_stability_root)
    panel = Path(args.panel_root)
    profiles = _parse_list(args.profiles)
    windows = _parse_list(args.windows)

    if not args.skip_panel_build:
        panel.mkdir(parents=True, exist_ok=True)
        from src.research.build_trade_context_panel import run_build

        if (
            run_build(
                complete_smoke_root=smoke,
                expanded_stability_root=exp,
                output_root=panel,
                profiles=profiles,
                windows=windows,
                aggregate_only=True,
                allow_local_detailed_inputs="false",
            )
            != 0
        ):
            return 1

    _write_baseline_inventory(cycle)
    _write_champion_freeze(cycle)
    _write_trade_context_schema(cycle)
    _write_router_metadata(cycle)
    _write_router_design(cycle)
    _write_trade_quality_v2(cycle)
    _write_exit_overlay(cycle)
    _write_scalp_roadmap(cycle)
    _write_short_roadmap(cycle)
    _write_next_sweep(cycle)
    _build_diagnostics(cycle=cycle, panel=panel, smoke=smoke, exp=exp, profiles=profiles, windows=windows)
    _write_decision(cycle)
    _write_bundle_and_map(cycle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
