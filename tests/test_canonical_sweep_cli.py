"""CLI behavior for ``src.backtest.sweep``."""

from __future__ import annotations

from unittest import mock

import pytest

import src.backtest.sweep as sweep


def test_default_missing_args_nonzero():
    assert sweep.main([]) != 0


def test_data_root_incomplete_returns_3():
    assert sweep.main(["--data-root", "C:/fake"]) == 3


def test_validate_pipeline_metadata_zero():
    assert sweep.main(["--validate-pipeline", "--strategy", "pa_buy_sell_close_trend"]) == 0


def test_legacy_first_token_delegates():
    with mock.patch("src.backtest.legacy.sweep_legacy.main", return_value=0) as m:
        rc = sweep.main(["--legacy", "--help"])
    assert rc == 0
    m.assert_called_once_with(["--help"])
