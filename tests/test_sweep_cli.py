"""CLI behavior for ``src.backtest.sweep``."""

from __future__ import annotations

import pytest

import src.backtest.sweep as sweep


def test_default_missing_args_nonzero():
    assert sweep.main([]) != 0


def test_data_root_incomplete_returns_3():
    assert sweep.main(["--data-root", "C:/fake"]) == 3


def test_validate_pipeline_metadata_zero():
    assert sweep.main(["--validate-pipeline", "--strategy", "pa_buy_sell_close_trend"]) == 0


def test_pipeline_help_returns_zero():
    assert sweep.main(["--pipeline-help"]) == 0
