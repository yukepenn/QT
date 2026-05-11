from __future__ import annotations

import numpy as np
import pandas as pd

from src.features.build_features import build_basic_features


def test_prior_multiday_lows_align_prior_sessions_only() -> None:
    """Multi-day lows on session D use only completed session lows strictly before D."""
    ny = "America/New_York"
    days = pd.bdate_range("2026-01-05", periods=6, freq="B")
    rows = []
    for d in days:
        ts_ny = pd.date_range(f"{d} 09:30", periods=5, freq="1min", tz=ny)
        ts_utc = ts_ny.tz_convert("UTC")
        for i, t in enumerate(ts_utc):
            base = 100.0 + float(d.day) * 0.1
            rows.append(
                {
                    "ts_utc": t,
                    "open": base,
                    "high": base + 0.5,
                    "low": base - 0.2 - i * 0.01,
                    "close": base + 0.1,
                    "volume": 1000.0,
                }
            )
    raw = pd.DataFrame(rows)
    out = build_basic_features(raw, copy=True)
    g = out.groupby("session_date", sort=False)["low"].min()
    dates = list(g.index)
    for sd, row in out.groupby("session_date", sort=False):
        i = dates.index(sd)
        if i < 3:
            continue
        d1, d2, d3 = dates[i - 1], dates[i - 2], dates[i - 3]
        exp3 = min(float(g.loc[d1]), float(g.loc[d2]), float(g.loc[d3]))
        assert np.allclose(row["prior_3day_low"].iloc[0], exp3, rtol=0, atol=1e-9)
