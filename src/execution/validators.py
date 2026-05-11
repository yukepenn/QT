from __future__ import annotations

import math
import numpy as np
import pandas as pd

from src.execution.types import ExecutionPolicy, Side, TradeIntent


def is_finite_price(x: float) -> bool:
    try:
        return x is not None and math.isfinite(float(x))
    except (TypeError, ValueError):
        return False


def validate_bars(df: pd.DataFrame, *, required: tuple[str, ...]) -> tuple[bool, str]:
    miss = [c for c in required if c not in df.columns]
    if miss:
        return False, f"missing_columns:{miss}"
    if df.index.has_duplicates:
        return False, "duplicate_index"
    return True, "ok"


def validate_execution_policy(p: ExecutionPolicy) -> tuple[bool, str]:
    if p.semantics_version != "1.0":
        return False, "unsupported_semantics_version"
    if not is_finite_price(p.slippage_per_share) or p.slippage_per_share < 0:
        return False, "bad_slippage"
    if not is_finite_price(p.commission_per_trade) or p.commission_per_trade < 0:
        return False, "bad_commission"
    return True, "ok"


def validate_trade_intent(
    intent: TradeIntent, policy: ExecutionPolicy, bars_len: int
) -> tuple[bool, str]:
    if intent.side not in (Side.LONG, Side.SHORT):
        return False, "invalid_side"
    if intent.side == Side.SHORT and not policy.allow_short:
        return False, "short_disabled"
    if intent.entry_idx < 0 or intent.entry_idx >= bars_len:
        return False, "bad_entry_idx"
    if not is_finite_price(intent.stop_price):
        return False, "bad_stop"
    if not is_finite_price(intent.target_price) and intent.target_mode == "fixed_price":
        return False, "bad_target"
    if not is_finite_price(intent.risk_per_share) or intent.risk_per_share <= 0:
        return False, "bad_risk"
    if intent.qty <= 0:
        return False, "bad_qty"
    return True, "ok"


def bars_to_arrays(df: pd.DataFrame) -> dict[str, np.ndarray]:
    return {
        "open": df["open"].to_numpy(dtype=np.float64, copy=False),
        "high": df["high"].to_numpy(dtype=np.float64, copy=False),
        "low": df["low"].to_numpy(dtype=np.float64, copy=False),
        "close": df["close"].to_numpy(dtype=np.float64, copy=False),
        "minute": df["minute_from_open"].to_numpy(dtype=np.int32, copy=False)
        if "minute_from_open" in df.columns
        else np.zeros(len(df), dtype=np.int32),
    }
