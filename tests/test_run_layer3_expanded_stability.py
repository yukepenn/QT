from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

import src.research.run_layer3_expanded_stability as mod

REPO = Path(__file__).resolve().parents[1]
SMOKE = REPO / "src/research/results/layer3_fixed_profile_smoke_complete_v1"
OUT = REPO / "src/research/results/layer3_expanded_stability_v1"


def test_complete_smoke_summaries_parse() -> None:
    smoke = mod._read_smoke_root(SMOKE)
    assert not smoke["complete_monthly_summary"].empty
    assert not smoke["complete_quarterly_summary"].empty
    assert set(smoke["complete_profile_window_summary"]["profile_id"].unique()) >= {
        "pa_only_mtp1_meta",
        "pa_gap_mtp2_meta",
    }


def test_market_context_labels_no_calendar_as_metric_names() -> None:
    p = OUT / "market_context_labels.csv"
    assert p.is_file()
    df = pd.read_csv(p)
    cols = {c.lower() for c in df.columns}
    assert "2025q1" not in cols
    assert "2022q4" not in cols


def test_weak_period_list_in_interpretation() -> None:
    p = OUT / "weak_period_interpretation.md"
    text = p.read_text(encoding="utf-8")
    assert "2025Q1" in text
    assert "2022Q4" in text


def test_gate_status_vocabulary() -> None:
    g = pd.read_csv(OUT / "expanded_stability_gate_results.csv")
    allowed = {"PASS", "FAIL", "WARNING", "NOT_EVALUATED"}
    assert set(g["status"].unique()) <= allowed


def test_decision_label_allowed() -> None:
    dec = (OUT / "layer3_expanded_stability_decision.md").read_text(encoding="utf-8")
    allowed = {
        "PROCEED_TO_PRE_WFO_STABILITY_DESIGN",
        "RUN_LOCAL_DETAILED_WEAK_PERIOD_REPLAY",
        "REFINE_LAYER3_COMBINATION_RULES",
        "HOLD_BEFORE_WFO",
        "DEFER_GLOBAL_SYSTEM",
    }
    m = re.search(r"## Decision: `([^`]+)`", dec)
    assert m, "decision header missing"
    assert m.group(1) in allowed


def test_no_absolute_paths_in_curated_csvs() -> None:
    toks = ("D:/", "C:/", "OneDrive")
    for p in OUT.glob("*.csv"):
        s = p.read_text(encoding="utf-8")
        for t in toks:
            assert t not in s, p.name


def test_source_map_lists_bundle() -> None:
    sm = pd.read_csv(OUT / "SOURCE_MAP.csv")
    paths = set(sm["file_path"].astype(str))
    assert any("CHATGPT_REVIEW_BUNDLE.md" in x for x in paths)


def test_manifest_no_trading_rerun() -> None:
    m = pd.read_csv(OUT / "run_execution_manifest.csv")
    assert (m["requires_new_trading_run"].astype(str) == "no").all()


def test_required_profiles_in_weak_period_pnl() -> None:
    df = pd.read_csv(OUT / "weak_period_profile_pnl.csv")
    for wp in ("2025Q1", "2022Q4"):
        sub = df[df["weak_period"] == wp]
        pids = set(sub["profile_id"].astype(str))
        assert "pa_only_mtp1_meta" in pids
        assert "pa_gap_mtp2_meta" in pids
