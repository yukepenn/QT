"""Bar table validation (lightweight)."""

from __future__ import annotations

import pandas as pd


def assert_sorted_unique_index(df: pd.DataFrame) -> None:
    if not df.index.is_monotonic_increasing:
        raise ValueError("bars index must be sorted ascending")
    if df.index.has_duplicates:
        raise ValueError("bars index must be unique")
