"""Canonical Layer 1 parameter sweep — **not implemented** on the reference engine.

This module is the **mainline** entry for sweep-related CLI and thin
compatibility hooks. Historical Numba grid sweeps live in
``src.backtest.legacy.sweep_legacy`` and use **legacy** accounting
(``engine=legacy_numba_fast``). Do not compare their R/PnL to
``src.execution.path.simulate_trade_path`` without a parity study.

Usage:

- Default / no ``--legacy``: print guidance and exit (no silent legacy sweep).
- ``--legacy ...``: forward remaining arguments to ``legacy.sweep_legacy.main``.
"""

from __future__ import annotations

import argparse
import sys
from typing import Any


def run_canonical_sweep_placeholder(*_args: Any, **_kwargs: Any) -> None:
    """Reserved for future reference-engine sweep (not implemented)."""
    raise NotImplementedError(
        "Canonical sweep (features → signals → run_strategy_backtest → execution) "
        "is not implemented yet. See docs/CANONICAL_SWEEP_DESIGN.md. "
        "For reference-only Numba sweeps use: python -m src.backtest.sweep --legacy ..."
    )


def _print_canonical_notice() -> None:
    print(
        "Canonical parameter sweep is not implemented yet.\n"
        "The reference accounting path is src.execution.path.simulate_trade_path.\n"
        "To run the legacy Numba fast grid (reference accounting only), use:\n"
        "  python -m src.backtest.sweep --legacy [same arguments as before]\n"
        "This prints engine=legacy_numba_fast and writes under strategy testing_parameters_results/.\n"
        "See docs/CANONICAL_SWEEP_DESIGN.md and docs/LAYER_FLOW.md.\n",
        file=sys.stderr,
    )


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    if argv and argv[0] == "--legacy":
        print("engine=legacy_numba_fast", flush=True)
        from src.backtest.legacy.sweep_legacy import main as legacy_main

        return int(legacy_main(argv[1:]))

    p = argparse.ArgumentParser(
        description=(
            "Layer 1 sweep CLI: canonical sweep is not implemented; "
            "use --legacy to run the Numba reference grid (legacy accounting)."
        )
    )
    p.add_argument(
        "--legacy",
        action="store_true",
        help="Must be first argument: run legacy Numba sweep (see legacy.sweep_legacy).",
    )
    p.add_argument(
        "--canonical-help",
        action="store_true",
        help="Describe the future canonical sweep pipeline.",
    )
    args, unknown = p.parse_known_args(argv)

    if args.canonical_help:
        print(
            "Future canonical sweep: load bars → build features → load strategy → "
            "generate signals → map to standard signal contract → run_strategy_backtest → "
            "execution (simulate_trade_path) → metrics. Optional Numba acceleration only "
            "via src.execution.fast_path after parity tests vs the reference engine."
        )
        return 0

    if unknown:
        print(
            f"ERROR unexpected arguments {unknown!r}. "
            "Legacy Numba sweep requires --legacy as the first token, e.g.\n"
            "  python -m src.backtest.sweep --legacy --strategy ... --start ... --end ...\n",
            file=sys.stderr,
        )
        _print_canonical_notice()
        return 2

    if args.legacy:
        print("engine=legacy_numba_fast", flush=True)
        from src.backtest.legacy.sweep_legacy import main as legacy_main

        return int(legacy_main([]))

    _print_canonical_notice()
    p.print_help(sys.stderr)
    return 1


def validate_testing_grid_for_strategy(strategy: str, testing: dict[str, Any]) -> None:
    from src.backtest.legacy import sweep_legacy as sl

    return sl.validate_testing_grid_for_strategy(strategy, testing)


def _finalize_combo_config(cfg: dict[str, Any]) -> None:
    from src.backtest.legacy import sweep_legacy as sl

    return sl._finalize_combo_config(cfg)


def _load_testing_yaml(path: Any, *, expected_strategy: str) -> dict[str, Any]:
    from src.backtest.legacy import sweep_legacy as sl

    return sl._load_testing_yaml(path, expected_strategy=expected_strategy)


def _metrics_row(**kwargs: Any) -> dict[str, Any]:
    from src.backtest.legacy import sweep_legacy as sl

    return sl._metrics_row(**kwargs)


if __name__ == "__main__":
    raise SystemExit(main())
