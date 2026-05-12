"""Legacy vs canonical boundaries (imports and messaging)."""

import inspect

import src.execution.path as path_mod


def test_sweep_module_documents_legacy_engine():
    import src.backtest.sweep as sweep

    doc = (sweep.__doc__ or "").lower()
    assert "legacy" in doc or "not canonical" in doc


def test_importing_execution_does_not_pull_legacy_fast():
    """Canonical ``src.execution`` must not import Numba fast legacy."""
    import src.execution as ex

    assert not hasattr(ex, "prepare_backtest_arrays")
    src = inspect.getsource(path_mod)
    assert "fast_legacy" not in src
    assert "legacy.fast" not in src
