"""Unit tests for ``src.backtest.strategy_runner``."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest

from src.backtest import strategy_runner as sr
from src.strategies.loader import load_strategy_config


def test_load_strategy_config_merged_default():
    cfg = sr.load_strategy_config_merged("orb_continuation", None, None)
    assert cfg.get("strategy") == "orb_continuation"


def test_grid_combos_from_nested_grid():
    combos = sr.grid_combos_from_document({"grid": {"risk.target_r": [1.0, 1.5]}})
    assert combos == [{"risk.target_r": 1.0}, {"risk.target_r": 1.5}]


def test_grid_combos_flat_dict(tmp_path: Path):
    p = tmp_path / "g.json"
    p.write_text(json.dumps({"risk.target_r": [2.0]}), encoding="utf-8")
    doc = sr.load_grid_document(p)
    assert sr.grid_combos_from_document(doc) == [{"risk.target_r": 2.0}]


def test_feature_config_fingerprint_stable():
    c1 = load_strategy_config("orb_continuation")
    c2 = load_strategy_config("orb_continuation")
    assert sr.feature_config_fingerprint(c1) == sr.feature_config_fingerprint(c2)


def test_prepare_canonical_signals_accepts_standard_frame():
    from src.strategies.strategy.base import init_standard_signal_columns

    base = init_standard_signal_columns(pd.DataFrame({"x": [1]}), strategy_name="orb_continuation", copy=True)
    out = sr.prepare_canonical_signals("orb_continuation", base)
    assert len(out) == 1


def test_validate_pipeline_metadata_only():
    cfg = load_strategy_config("pa_buy_sell_close_trend")
    rep = sr.validate_canonical_pipeline(
        strategy_name="pa_buy_sell_close_trend",
        cfg=cfg,
        asset="equity",
        symbol="",
        start="",
        end="",
        data_dir="data/raw/ibkr",
        with_data=False,
    )
    assert rep["strategy_loads"] is True
    assert not rep.get("blockers")
