"""Tests for Playbook Router Research Cycle v1 curated artifacts (no heavy local trades)."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
CYCLE = REPO / "src/research/results/playbook_router_research_cycle_v1"


@pytest.fixture(scope="module")
def cycle_root() -> Path:
    if not CYCLE.is_dir():
        pytest.skip("playbook_router_research_cycle_v1 not generated; run analyze_playbook_context")
    return CYCLE


def test_champion_freeze_csv_profiles(cycle_root: Path) -> None:
    p = cycle_root / "champion_v0_freeze.csv"
    assert p.is_file()
    with p.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    ids = {r["profile_id"] for r in rows}
    assert ids == {"pa_only_mtp1_meta", "pa_gap_mtp2_meta", "primary_mtp2_meta"}
    assert len(rows) == 3


def test_metadata_future_rows_design_only(cycle_root: Path) -> None:
    p = cycle_root / "router_metadata_v1/candidate_playbook_metadata.csv"
    assert p.is_file()
    with p.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    future = [r for r in rows if r.get("current_or_future") == "future"]
    assert future, "expected future placeholder rows"
    for r in future:
        assert "DESIGN_ONLY_NOT_IMPLEMENTED" in (r.get("current_evidence_status") or "")


def test_router_yaml_offline_disabled(cycle_root: Path) -> None:
    yp = cycle_root / "router_design_v1/router_v1_config_draft.yaml"
    assert yp.is_file()
    cfg = yaml.safe_load(yp.read_text(encoding="utf-8"))
    assert cfg.get("enabled") is False
    assert cfg.get("mode") == "offline_diagnostic"


def test_no_future_strategy_yaml_committed() -> None:
    """Future scalp/short placeholders must not add strategy plugins in this cycle."""
    strat_dir = REPO / "src/strategies"
    forbidden = {
        "pa_range_scalp_long",
        "pa_range_scalp_short",
        "gap_up_failure_short",
        "vwap_rejection_short",
        "orb_failed_breakout_short",
        "pa_sell_close_trend_short",
        "late_climax_reversal_short",
    }
    found = [n for n in forbidden if (strat_dir / f"{n}.yaml").is_file() or (strat_dir / n).is_dir()]
    assert not found, f"unexpected strategy artifacts: {found}"


def test_trade_quality_weights_sum(cycle_root: Path) -> None:
    p = cycle_root / "trade_quality_score_v2/trade_quality_score_design.md"
    text = p.read_text(encoding="utf-8")
    assert "30%" in text and "20%" in text and "15%" in text
    assert "100%" in text or "sum = 100%" in text


def test_exit_overlay_modes(cycle_root: Path) -> None:
    p = cycle_root / "exit_overlay_design_v1/exit_overlay_design.csv"
    assert p.is_file()
    with p.open(encoding="utf-8", newline="") as f:
        modes = {r["management_mode"] for r in csv.DictReader(f)}
    assert modes == {"scalp", "trend_swing", "runner", "reversal"}


def test_next_sweep_cycles_ordered(cycle_root: Path) -> None:
    p = cycle_root / "next_3layer_sweep_roadmap.csv"
    assert p.is_file()
    with p.open(encoding="utf-8", newline="") as f:
        ids = [r["cycle_id"] for r in csv.DictReader(f)]
    assert ids == [
        "Cycle_1",
        "Cycle_2",
        "Cycle_3",
        "Cycle_4",
        "Cycle_5",
        "Cycle_6",
        "Cycle_7",
    ]


def test_source_map_includes_bundle(cycle_root: Path) -> None:
    p = cycle_root / "SOURCE_MAP.csv"
    assert p.is_file()
    with p.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    paths = {r["file_path"] for r in rows}
    assert any(r.endswith("CHATGPT_REVIEW_BUNDLE.md") for r in paths)
    bundle_rows = [r for r in rows if r["file_path"].endswith("CHATGPT_REVIEW_BUNDLE.md")]
    assert bundle_rows[0]["required_for_review"] == "yes"


def test_curated_csvs_no_absolute_paths(cycle_root: Path) -> None:
    """Curated CSV cell values should not embed Windows drive paths."""
    bad = ("D:/", "D:\\", "C:/Users", "C:\\Users", "OneDrive", ":\\")
    for csv_path in sorted(cycle_root.rglob("*.csv")):
        txt = csv_path.read_text(encoding="utf-8", errors="replace")
        for b in bad:
            assert b not in txt, f"{csv_path.relative_to(REPO)} contains {b!r}"
