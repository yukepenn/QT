"""Mini-WFO YAML validation."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.walkforward.mini_wfo_selection import MiniWFOValidationError, layer2_raw_combo_count, validate_mini_wfo_config

CFG_PATH = Path(__file__).resolve().parents[1] / "src/walkforward/configs/qqq_mini_wfo_2023_2024_train_2025_202604_test_v1.yaml"


def test_packaged_config_validates() -> None:
    with CFG_PATH.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    validate_mini_wfo_config(cfg)


def test_grid_size_is_288() -> None:
    with CFG_PATH.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    n = layer2_raw_combo_count(cfg["layer2"]["grid"])
    assert n == 288


def test_rejects_spy_symbol() -> None:
    with CFG_PATH.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["symbol"] = "SPY"
    with pytest.raises(MiniWFOValidationError):
        validate_mini_wfo_config(cfg)


def test_rejects_train_test_overlap() -> None:
    with CFG_PATH.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["train"]["end"] = "2025-06-01"
    with pytest.raises(MiniWFOValidationError):
        validate_mini_wfo_config(cfg)


def test_rejects_live_ready() -> None:
    with CFG_PATH.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg.setdefault("experiment", {})["live_ready"] = True
    with pytest.raises(MiniWFOValidationError):
        validate_mini_wfo_config(cfg)
