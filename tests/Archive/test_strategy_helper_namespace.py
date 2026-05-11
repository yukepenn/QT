"""Strategy helper namespace: ``src.strategies.common.pa`` and compatibility shims."""

from __future__ import annotations

import src.strategies.common.pa as common_pa
from src.strategies import loader
from src.strategies.strategy import pa_batch_a_utils
from src.strategies.strategy import pa_common as pa_common_shim


def test_import_common_pa() -> None:
    assert common_pa.pa_range_window({"features": {}}) == 60
    assert callable(common_pa.finalize_long_signals_df)


def test_shim_pa_common_reexports() -> None:
    assert pa_common_shim.pa_context_windows({"features": {}}) == (60, 30, "atr_like_20")
    assert pa_common_shim.build_pa_reason("a", "b") == "a|b"


def test_shim_pa_batch_a_utils_reexports() -> None:
    assert pa_batch_a_utils.pa_range_window({"features": {}}) == 60
    assert callable(pa_batch_a_utils.finalize_long_signals_df)


def test_loader_strategy_count_unchanged() -> None:
    names = loader.available_strategies()
    assert len(names) == 35


def test_helpers_not_registered_as_strategies() -> None:
    reg = getattr(loader, "_STRATEGY_BY_NAME", {})
    assert "pa_common" not in reg
    assert "pa_batch_a_utils" not in reg
    assert "pa" not in reg
