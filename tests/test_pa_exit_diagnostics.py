"""Sanity checks for PA exit diagnostics helpers."""

from __future__ import annotations

from pathlib import Path

import yaml

from src.research.pa_exit_diagnostics import _cfg_from_candidate_yaml


def test_cfg_from_candidate_merges_asset_symbol(tmp_path: Path) -> None:
    p = tmp_path / "cand.yaml"
    p.write_text(
        yaml.dump(
            {
                "strategy": "pa_climax_reversal",
                "asset": "equity",
                "symbol": "QQQ",
                "config": {"strategy": "pa_climax_reversal", "signal": {"side": "long_only"}},
            }
        ),
        encoding="utf-8",
    )
    name, cfg = _cfg_from_candidate_yaml(p)
    assert name == "pa_climax_reversal"
    assert cfg.get("asset") == "equity"
    assert cfg.get("symbol") == "QQQ"
