"""Light tests for PA diagnostics scripts (no large bar downloads)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.research.pa_exit_diagnostics import _cfg_from_candidate_yaml


def test_cfg_from_candidate_yaml_requires_config_block(tmp_path: Path) -> None:
    p = tmp_path / "bad.yaml"
    p.write_text(yaml.dump({"strategy": "pa_climax_reversal"}), encoding="utf-8")
    with pytest.raises(ValueError):
        _cfg_from_candidate_yaml(p)


def test_pa_gate_diagnostics_importable():
    import src.research.pa_gate_diagnostics as g

    assert callable(g.main)
