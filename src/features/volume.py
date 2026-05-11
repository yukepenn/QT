"""Session-scoped volume ratios (shifted MA denominators; no lookahead)."""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.feature_config import FEATURE_COLUMNS
from src.features.utils import add_or_overwrite_columns, ensure_columns, safe_copy


def add_volume_features(
    df: pd.DataFrame,
    *,
    windows: tuple[int, ...] = (20, 30, 60),
    copy: bool = True,
    allow_overwrite: bool = False,
) -> pd.DataFrame:
    module_name = "volume"
    cols = FEATURE_COLUMNS[module_name]
    add_or_overwrite_columns(df, cols, module_name=module_name, allow_overwrite=allow_overwrite)

    ensure_columns(df, ["session_date", "volume"], context="volume")

    out = safe_copy(df, copy)
    vol = out["volume"].astype(float)
    g = out.groupby("session_date", sort=False)
    new_cols: dict[str, pd.Series] = {}
    for n in windows:
        vma = g["volume"].transform(
            lambda s, w=n: s.rolling(w, min_periods=1).mean().shift(1)
        )
        col_ma = f"volume_ma_{n}_prior"
        new_cols[col_ma] = vma
        ratio = vol / vma.replace(0.0, np.nan)
        new_cols[f"volume_ratio_{n}"] = ratio

    return pd.concat([out, pd.DataFrame(new_cols)], axis=1)
