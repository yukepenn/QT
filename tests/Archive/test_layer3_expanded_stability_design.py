"""Design-only tests for Layer3 expanded stability v1 artifacts (no combiner runs)."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
DESIGN = _ROOT / "src/research/results/layer3_expanded_stability_design_v1"
ALLOWED_DECISIONS = frozenset(
    {
        "RUN_LAYER3_EXPANDED_STABILITY",
        "NEED_MORE_EXPANDED_STABILITY_DESIGN",
        "REFINE_LAYER3_PROFILE_SET",
        "HOLD_BEFORE_STABILITY",
        "DEFER_GLOBAL_SYSTEM",
    }
)
GATE_LABELS = frozenset(
    {
        "EXPANDED_STABILITY_READY",
        "EXPANDED_STABILITY_READY_WITH_WARNINGS",
        "NEED_WEAK_PERIOD_DIAGNOSTICS",
        "REFINE_COMBINATION_RULES",
        "FAIL_EXPANDED_STABILITY",
        "HOLD_BEFORE_STABILITY",
        "future_optional",
    }
)


def _read_csv(name: str) -> list[dict[str, str]]:
    path = DESIGN / name
    assert path.is_file(), f"missing {path}"
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _read_text(name: str) -> str:
    return (DESIGN / name).read_text(encoding="utf-8")


def test_profile_selection_parses_and_required_profiles():
    rows = _read_csv("expanded_stability_profile_selection.csv")
    by_id = {r["profile_id"]: r for r in rows}
    assert set(by_id) == {
        "pa_only_mtp1_meta",
        "pa_gap_mtp2_meta",
        "primary_mtp2_meta",
        "pa_gap_mtp1_meta",
        "pa_only_mtp2_meta",
    }
    assert by_id["pa_only_mtp1_meta"]["include_in_expanded_stability"] == "YES"
    assert by_id["pa_gap_mtp2_meta"]["include_in_expanded_stability"] == "YES"
    assert by_id["pa_only_mtp1_meta"]["include_as_default_candidate"] == "YES"
    assert by_id["pa_gap_mtp2_meta"]["include_as_default_candidate"] == "YES"
    assert by_id["primary_mtp2_meta"]["include_as_reference_only"] == "YES"


def test_weak_period_docs_reference_anchor_quarters():
    md = _read_text("weak_period_diagnostic_design.md")
    assert "2025Q1" in md
    assert "2022Q4" in md


def test_market_context_labels_not_calendar_hardcoded():
    rows = _read_csv("market_context_label_design.csv")
    names = {r["label_name"] for r in rows}
    assert "2025Q1" not in names
    assert "2022Q4" not in names
    assert "uptrend_low_vol" in names
    assert "unknown_mixed" in names


def test_gate_csv_failure_actions_use_allowed_vocab():
    rows = _read_csv("expanded_stability_gate_design.csv")
    actions = {r["failure_action"] for r in rows}
    assert actions <= GATE_LABELS


def test_expected_outputs_lists_bundle_and_source_map():
    rows = _read_csv("expanded_stability_expected_outputs.csv")
    outs = {r["output_file"] for r in rows}
    assert "CHATGPT_REVIEW_BUNDLE.md" in outs
    assert "SOURCE_MAP.csv" in outs


def test_curated_csvs_no_absolute_path_tokens():
    abs_tokens = ("D:/", "C:/", "OneDrive", "\\OneDrive")
    for p in sorted(DESIGN.glob("*.csv")):
        txt = p.read_text(encoding="utf-8")
        for tok in abs_tokens:
            assert tok not in txt, f"{p.name} contains {tok!r}"


def test_decision_label_valid():
    dec = _read_text("layer3_expanded_stability_design_decision.md")
    matched = {d for d in ALLOWED_DECISIONS if f"**`{d}`**" in dec}
    assert matched == {"RUN_LAYER3_EXPANDED_STABILITY"}


def test_source_map_paths_repo_relative():
    rows = _read_csv("SOURCE_MAP.csv")
    for r in rows:
        fp = r["file_path"]
        assert not fp.startswith("D:/")
        assert "OneDrive" not in fp
        assert fp.startswith("src/research/results/layer3_expanded_stability_design_v1/")
