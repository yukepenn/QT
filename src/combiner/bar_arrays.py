"""Bar columns → contiguous NumPy arrays for combiner signal-matrix prep."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def prepare_backtest_arrays(df: pd.DataFrame) -> dict[str, Any]:
    need = [
        "ts_utc",
        "ts_ny",
        "session_date",
        "minute_from_open",
        "open",
        "high",
        "low",
        "close",
    ]
    miss = [c for c in need if c not in df.columns]
    if miss:
        raise ValueError(f"prepare_backtest_arrays missing: {miss}")
    work = df.sort_values("ts_utc").reset_index(drop=True)
    sid_codes, uniques = pd.factorize(work["session_date"], sort=False)
    return {
        "open": work["open"].to_numpy(dtype=np.float64, copy=False),
        "high": work["high"].to_numpy(dtype=np.float64, copy=False),
        "low": work["low"].to_numpy(dtype=np.float64, copy=False),
        "close": work["close"].to_numpy(dtype=np.float64, copy=False),
        "minute": work["minute_from_open"].to_numpy(dtype=np.int32, copy=False),
        "session_id": sid_codes.astype(np.int32),
        "session_dates": uniques,
        "n": len(work),
    }
