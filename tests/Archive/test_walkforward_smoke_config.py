"""Smoke config validation tests."""

from __future__ import annotations

from pathlib import Path

import yaml


def test_repo_smoke_config_loads():
    p = Path("src/walkforward/configs/qqq_fixed_system_smoke_v1.yaml")
    assert p.is_file()
    cfg = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert cfg["symbol"] == "QQQ"
    assert len(cfg.get("systems") or []) == 3
    assert len(cfg.get("folds") or []) == 3
