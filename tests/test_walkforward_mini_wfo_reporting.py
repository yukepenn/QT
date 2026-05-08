"""Mini-WFO summary and frozen-system reporting."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.walkforward.mini_wfo_selection import (
    mini_wfo_summary_expected_sections,
    render_mini_wfo_summary_md,
    validate_frozen_system_yaml,
)


def test_expected_summary_sections_present() -> None:
    md = render_mini_wfo_summary_md(
        decision="PASS",
        train_window=("2023-01-01", "2024-12-31"),
        test_window=("2025-01-01", "2026-04-30"),
    )
    for title in mini_wfo_summary_expected_sections():
        assert title in md


def test_validate_frozen_system_yaml_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "selected_frozen_system.yaml"
    doc = {
        "system_id": "x",
        "source": {"train_start": "a", "train_end": "b", "selected_from": "t", "selected_rank": 1},
        "candidate_root": "/tmp",
        "candidate_ids": ["A"],
        "combiner": {},
        "cost": {},
        "selection_reason": "r",
        "selection_metrics_train": {},
        "live_ready": False,
        "research_status": "mini_wfo_selected_train_only",
    }
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    validate_frozen_system_yaml(p)


def test_validate_rejects_live_ready_true(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    doc = {
        "system_id": "x",
        "source": {"train_start": "a", "train_end": "b", "selected_from": "t", "selected_rank": 1},
        "candidate_root": "/tmp",
        "candidate_ids": [],
        "combiner": {},
        "cost": {},
        "selection_reason": "r",
        "selection_metrics_train": {},
        "live_ready": True,
        "research_status": "x",
    }
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    with pytest.raises(ValueError):
        validate_frozen_system_yaml(p)


def test_missing_yaml_raises() -> None:
    with pytest.raises(FileNotFoundError):
        validate_frozen_system_yaml(Path("/nonexistent/selected_frozen_system.yaml"))
