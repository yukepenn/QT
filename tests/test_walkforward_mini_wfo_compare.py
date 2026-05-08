from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from src.walkforward.mini_wfo_compare import (
    _extract_selected_candidate_set_from_decision,
    _infer_candidate_set_from_ids,
    summarize_root,
    validate_selected_system_consistency,
)


def _write(p: Path, s: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")


def test_extract_selected_candidate_set_from_decision(tmp_path: Path) -> None:
    p = tmp_path / "selection_decision.md"
    _write(p, "- Selected candidate_set: **failed_gap**\n")
    assert _extract_selected_candidate_set_from_decision(p) == "failed_gap"


def test_infer_candidate_set_from_ids() -> None:
    assert _infer_candidate_set_from_ids(["MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]) == "gap_only"
    assert _infer_candidate_set_from_ids(["MINIWFO_FAILED_ORB_001"]) == "failed_only"
    assert _infer_candidate_set_from_ids(["MINIWFO_FAILED_ORB_001", "MINIWFO_GAP_ACCEPTANCE_FAILURE_001"]) == "failed_gap"


def test_validate_selected_system_consistency_flags_mismatch() -> None:
    w = validate_selected_system_consistency(
        candidate_set="gap_only",
        candidate_ids=["MINIWFO_FAILED_ORB_001", "MINIWFO_GAP_ACCEPTANCE_FAILURE_001"],
    )
    assert "mismatch" in w


def test_summarize_root_prefers_selection_decision_set(tmp_path: Path) -> None:
    root = tmp_path / "run_root"

    _write(
        root / "frozen_system" / "selected_frozen_system.yaml",
        "\n".join(
            [
                "system_id: x",
                "source:",
                "  train_start: '2020-01-01'",
                "  train_end: '2024-12-31'",
                "candidate_ids:",
                "  - MINIWFO_FAILED_ORB_001",
                "  - MINIWFO_GAP_ACCEPTANCE_FAILURE_001",
                "selection_metrics_train:",
                "  total_r: 10.0",
                "  profit_factor_r: 1.1",
                "  max_drawdown_r: -5.0",
                "",
            ]
        ),
    )
    _write(root / "frozen_system" / "selection_decision.md", "- Selected candidate_set: **failed_gap**\n")

    (root / "selection_audit.json").write_text(
        json.dumps(
            {
                "strategy_universe_layer1": ["failed_orb", "gap_acceptance_failure"],
                "optional_diagnostics_layer1": [],
                "selected_candidate_set": "gap_only",
            }
        ),
        encoding="utf-8",
    )

    (root / "train_layer2_behavior_unique.csv").parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([{"candidate_set": "gap_only"}]).to_csv(root / "train_layer2_behavior_unique.csv", index=False)

    _write(
        root / "test" / "metrics.json",
        json.dumps({"trades": 2, "total_r": 1.0, "profit_factor": 1.0, "profit_factor_r": 1.0, "max_drawdown_r": -1.0}),
    )
    pd.DataFrame(
        [
            {"slippage_per_share": 0.01, "total_r": 1.0},
            {"slippage_per_share": 0.02, "total_r": 0.5},
            {"slippage_per_share": 0.03, "total_r": 0.2},
        ]
    ).to_csv(root / "test" / "cost_stress.csv", index=False)

    pd.DataFrame([{"period": "2025-12", "trades": 2, "total_r": -1.0}]).to_csv(
        root / "test" / "monthly_breakdown.csv", index=False
    )
    _write(root / "mini_wfo_summary.md", "**FAIL**\n")

    row = summarize_root(root)
    assert row["selected_candidate_set"] == "failed_gap"
    assert row["selected_candidate_ids"] == "MINIWFO_FAILED_ORB_001,MINIWFO_GAP_ACCEPTANCE_FAILURE_001"
    assert "top_behavior_set=gap_only" in (row.get("warnings") or "")

