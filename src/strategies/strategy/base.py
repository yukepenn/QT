"""Strategy plugin interface and standard signal schema."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

import pandas as pd


STANDARD_SIGNAL_COLUMNS = [
    "sig_strategy",
    "sig_side",
    "sig_entry_ref",
    "sig_stop",
    "sig_target",
    "sig_target_mode",
    "sig_target_r",
    "sig_risk_per_share",
    "sig_reason",
    "sig_valid",
]


class BaseStrategy(ABC):
    name: str
    supports_fast: bool = False
    # Sweep readiness: use prepare_signal_context + generate_signal_arrays_from_context (true fast core).
    performance_tier: str = "A_true_context_fast_core"

    @abstractmethod
    def required_features(self) -> list[str]: ...

    @abstractmethod
    def generate_signals(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> pd.DataFrame: ...

    def prepare_signal_context(self, df: pd.DataFrame, config: dict[str, Any]) -> Any:
        return df

    def context_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        return ()

    def normalized_param_key(self, config: dict[str, Any]) -> tuple[Any, ...]:
        def _freeze(obj: Any) -> Any:
            if isinstance(obj, dict):
                return tuple(sorted((k, _freeze(v)) for k, v in obj.items()))
            if isinstance(obj, list):
                return tuple(_freeze(x) for x in obj)
            return obj

        return (
            _freeze(config.get("features") or {}),
            _freeze(config.get("signal") or {}),
            _freeze(config.get("risk") or {}),
            _freeze(config.get("backtest") or {}),
        )

    def validate_config(self, config: dict[str, Any]) -> None:
        """Optional hook: raise ValueError (or NotImplementedError) if config is invalid."""
        return None

    def generate_signal_arrays_from_context(
        self, ctx: Any, config: dict[str, Any]
    ) -> dict[str, Any]:
        if isinstance(ctx, pd.DataFrame):
            return self.generate_signal_arrays(ctx, config)
        raise NotImplementedError(
            f"{self.name} does not implement generate_signal_arrays_from_context for non-DataFrame context; "
            "override prepare_signal_context + generate_signal_arrays_from_context for optimized fast path"
        )

    def generate_signal_arrays(
        self, df: pd.DataFrame, config: dict[str, Any]
    ) -> dict[str, Any]:
        raise NotImplementedError(
            f"{self.name} does not implement fast signal arrays (generate_signal_arrays)"
        )


def validate_standard_signal_columns(df: pd.DataFrame) -> None:
    missing = [c for c in STANDARD_SIGNAL_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"missing standard signal columns: {missing}")


def validate_required_features_no_lookahead(
    *, strategy_name: str, required_features: list[str]
) -> None:
    bad = [c for c in required_features if "LOOKAHEAD" in str(c)]
    if bad:
        raise ValueError(
            f"strategy {strategy_name!r} requires LOOKAHEAD feature columns (not allowed): {bad}"
        )


def init_standard_signal_columns(
    df: pd.DataFrame,
    *,
    strategy_name: str,
    copy: bool = True,
) -> pd.DataFrame:
    out = df.copy() if copy else df
    out["sig_strategy"] = strategy_name
    out["sig_side"] = 0
    out["sig_entry_ref"] = pd.NA
    out["sig_stop"] = pd.NA
    out["sig_target"] = pd.NA
    out["sig_target_mode"] = ""
    out["sig_target_r"] = pd.NA
    out["sig_risk_per_share"] = pd.NA
    out["sig_reason"] = ""
    out["sig_valid"] = False
    return out
