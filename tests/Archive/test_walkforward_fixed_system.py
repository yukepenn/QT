"""Tests for frozen system YAML loading."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.walkforward.fixed_system import (
    build_fold_combiner_config,
    load_frozen_system,
    validate_frozen_system,
)
from src.walkforward.folds import SmokeFold


def _minimal_frozen(tmp_path: Path, live_ready: bool = False, mpos: int = 1) -> Path:
    root = tmp_path / "cand"
    root.mkdir()
    for cid in ("FAILED_ORB_001",):
        (root / f"{cid}.yaml").write_text(
            yaml.safe_dump(
                {
                    "candidate_id": cid,
                    "strategy": "failed_orb",
                    "testing_parameters": {},
                }
            ),
            encoding="utf-8",
        )
    p = tmp_path / "frozen.yaml"
    doc = {
        "system_id": "t_test",
        "research_status": "fixed_system_smoke_candidate",
        "live_ready": live_ready,
        "source": {
            "layer2_root": "src/combiner/results/layer2_qqq_2025_20260430_recent_check_v1",
        },
        "candidate_root": str(root),
        "candidate_ids": ["FAILED_ORB_001"],
        "combiner": {
            "candidate_set": "trap_family",
            "top_per_strategy": 1,
            "max_open_positions": mpos,
            "max_trades_per_day": 2,
            "daily_max_loss_r": -1.5,
            "cooldown_after_loss_minutes": 0,
            "priority_policy": "metadata_priority",
            "no_new_after_minute": 360,
        },
        "cost": {"commission_per_trade": 0.0, "slippage_per_share": 0.01},
    }
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


def test_frozen_load_ok(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fp = _minimal_frozen(tmp_path)
    fs = load_frozen_system(fp)
    validate_frozen_system(fs, symbol="QQQ")


def test_missing_candidate_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fp = _minimal_frozen(tmp_path)
    txt = fp.read_text(encoding="utf-8")
    data = yaml.safe_load(txt)
    data["candidate_ids"] = ["MISSING_ID"]
    fp.write_text(yaml.safe_dump(data), encoding="utf-8")
    fs = load_frozen_system(fp)
    with pytest.raises(FileNotFoundError):
        validate_frozen_system(fs, symbol="QQQ")


def test_live_ready_true_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fp = _minimal_frozen(tmp_path, live_ready=True)
    fs = load_frozen_system(fp)
    with pytest.raises(ValueError, match="live_ready"):
        validate_frozen_system(fs, symbol="QQQ")


def test_max_open_positions_bad(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fp = _minimal_frozen(tmp_path, mpos=2)
    fs = load_frozen_system(fp)
    with pytest.raises(ValueError, match="max_open_positions"):
        validate_frozen_system(fs, symbol="QQQ")


def test_build_fold_config(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    fp = _minimal_frozen(tmp_path)
    fs = load_frozen_system(fp)
    fold = SmokeFold(
        fold_id="t",
        label="",
        test_start="2024-01-01",
        test_end="2024-02-01",
    )
    cfg = build_fold_combiner_config(fs, fold, {})
    assert "candidate_sets" in cfg
    assert cfg["candidate_root"]
