"""Backward-compatible shim for PA config/reason helpers.

.. deprecated::
    Import from ``src.strategies.common.pa`` in new code.
"""

from __future__ import annotations

from src.strategies.common.pa import (
    build_pa_reason,
    pa_context_windows,
    pa_family_from_strategy_name,
    safe_bool_array,
    safe_float_array,
)

__all__ = [
    "build_pa_reason",
    "pa_context_windows",
    "pa_family_from_strategy_name",
    "safe_bool_array",
    "safe_float_array",
]
