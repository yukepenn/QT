from __future__ import annotations

from pathlib import Path

import yaml

from src.walkforward.mini_wfo import load_mini_wfo_config


def test_v3_style_testing_configs_mapping_parses(tmp_path: Path) -> None:
    cfg = {
        "experiment": {"name": "x", "live_ready": False},
        "asset": "equity",
        "symbol": "QQQ",
        "train": {"start": "2023-01-01", "end": "2024-12-31"},
        "test": {"start": "2025-01-01", "end": "2026-04-30"},
        "paths": {"output_root": "x", "train_layer1_root": "x", "train_layer2_root": "x", "frozen_system_dir": "x", "test_root": "x"},
        "layer1": {
            "strategies": ["gap_acceptance_failure", "failed_orb"],
            "testing_configs": {
                "gap_acceptance_failure": "src/strategies/testing_parameters/gap_acceptance_failure_refined_v1.yaml",
                "failed_orb": "src/strategies/testing_parameters/failed_orb_refined_v1.yaml",
            },
        },
        "layer2": {"candidate_sets": {}, "grid": {}},
        "execution": {"max_open_positions": 1},
    }
    p = tmp_path / "cfg.yaml"
    p.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
    doc = load_mini_wfo_config(p)
    assert isinstance(doc.get("layer1", {}).get("testing_configs"), dict)

