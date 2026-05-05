"""Lightweight registry for raw vs feature column names and documentation."""

from __future__ import annotations

RAW_COLUMNS = [
    "ts_utc",
    "ts_ny",
    "asset",
    "symbol",
    "root",
    "contract",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "average",
    "barCount",
    "source",
    "useRTH",
    "bar_size",
]

RAW_COLUMN_DESCRIPTIONS = {
    "ts_utc": "Timezone-aware UTC bar timestamp; primary time key.",
    "ts_ny": "Timezone-aware America/New_York bar timestamp for session logic.",
    "asset": "Asset type, e.g. equity or futures.",
    "symbol": "Equity/ETF symbol, e.g. SPY or QQQ.",
    "root": "Futures root, e.g. NQ or ES; null for equities.",
    "contract": "Explicit futures contract, e.g. NQM6; null for equities.",
    "open": "1-minute open price.",
    "high": "1-minute high price.",
    "low": "1-minute low price.",
    "close": "1-minute close price.",
    "volume": "1-minute volume.",
    "average": "IBKR average/WAP-like bar field if available.",
    "barCount": "IBKR barCount field if available.",
    "source": "Data source, currently ibkr.",
    "useRTH": "Whether the downloader requested regular trading hours only.",
    "bar_size": "Bar size string, e.g. 1 min.",
}

FEATURE_COLUMNS = {
    "time_features": [
        "session_date",
        "time_ny",
        "minute_of_day",
        "minute_from_open",
        "minutes_to_close",
        "is_rth_calc",
        "is_opening_30m",
        "is_closing_30m",
        "day_of_week",
        "date_id",
    ],
    "vwap": [
        "vwap",
        "vwap_dist",
        "vwap_dist_pct",
        "vwap_side",
        "vwap_slope_5",
        "vwap_slope_15",
        "vwap_slope_20",
        "vwap_slope_30",
        "vwap_slope_60",
        "vwap_std",
        "vwap_z",
        "close_above_vwap",
        "close_below_vwap",
        "vwap_persistence_above_10",
        "vwap_persistence_above_20",
        "vwap_persistence_above_30",
        "vwap_persistence_above_60",
        "vwap_persistence_below_10",
        "vwap_persistence_below_20",
        "vwap_persistence_below_30",
        "vwap_persistence_below_60",
        "vwap_upper_1.0",
        "vwap_lower_1.0",
        "vwap_upper_2.0",
        "vwap_lower_2.0",
    ],
    "orb": [
        "orb_open_minutes",
        "orb_high",
        "orb_low",
        "orb_mid",
        "orb_width",
        "orb_width_pct",
        "after_orb",
        "above_orb_high",
        "below_orb_low",
        "in_orb_range",
        "orb_breakout_dir",
        "orb_high_dist",
        "orb_low_dist",
    ],
    "levels": [
        "session_open",
        "session_high",
        "session_low",
        "session_close",
        "prior_day_open",
        "prior_day_high",
        "prior_day_low",
        "prior_day_close",
        "prior_day_range",
        "gap_from_prior_close",
        "gap_pct_from_prior_close",
        "gap_prior_range_norm",
    ],
    "price_action": [
        "bar_range",
        "body",
        "body_abs",
        "upper_wick",
        "lower_wick",
        "close_location",
        "is_green",
        "is_red",
        "prev_high_by_session",
        "prev_low_by_session",
        "prev_close_by_session",
        "rolling_high_3_prior",
        "rolling_low_3_prior",
        "rolling_range_3_prior",
        "range_width_3",
        "rolling_high_5_prior",
        "rolling_low_5_prior",
        "rolling_range_5_prior",
        "range_width_5",
        "rolling_high_10_prior",
        "rolling_low_10_prior",
        "rolling_range_10_prior",
        "range_width_10",
        "rolling_high_20_prior",
        "rolling_low_20_prior",
        "rolling_range_20_prior",
        "range_width_20",
        "rolling_high_30_prior",
        "rolling_low_30_prior",
        "rolling_range_30_prior",
        "range_width_30",
        "rolling_high_60_prior",
        "rolling_low_60_prior",
        "rolling_range_60_prior",
        "range_width_60",
    ],
    "volume": [
        "volume_ma_20_prior",
        "volume_ratio_20",
        "volume_ma_30_prior",
        "volume_ratio_30",
        "volume_ma_60_prior",
        "volume_ratio_60",
    ],
    "volatility": [
        "ret_1m",
        "tr",
        "ret_std_5",
        "range_5",
        "range_pct_5",
        "atr_like_5",
        "ret_std_15",
        "range_15",
        "range_pct_15",
        "atr_like_15",
        "ret_std_30",
        "range_30",
        "range_pct_30",
        "atr_like_30",
    ],
}

FEATURE_DEPENDENCIES = {
    "time_features": ["ts_utc", "ts_ny"],
    "vwap": ["session_date", "open", "high", "low", "close", "volume"],
    "orb": ["session_date", "minute_from_open", "high", "low", "close"],
    "levels": ["session_date", "open", "high", "low", "close"],
    "price_action": ["session_date", "open", "high", "low", "close"],
    "volume": ["session_date", "volume"],
    "volatility": ["session_date", "high", "low", "close"],
}

FEATURE_COLUMN_DESCRIPTIONS = {
    "session_date": "NY session date derived from ts_ny.",
    "time_ny": "HH:MM string in New York time.",
    "minute_of_day": "Minutes since midnight New York time.",
    "minute_from_open": "Minutes since configured RTH open, default 09:30.",
    "minutes_to_close": "Minutes until configured RTH close, default 16:00.",
    "is_rth_calc": "Whether bar time is inside configured RTH window. Distinct from raw useRTH.",
    "is_opening_30m": "True in first 30 minutes after session open.",
    "is_closing_30m": "True in last 30 minutes before session close.",
    "day_of_week": "Weekday index (Monday=0).",
    "date_id": "Sortable integer id from session_date.",
    "vwap": "Intraday VWAP reset by session_date.",
    "vwap_dist": "close - vwap.",
    "vwap_dist_pct": "close / vwap - 1.",
    "vwap_side": "1 if close > vwap, -1 if close < vwap, else 0.",
    "vwap_std": "Expanding intraday std of close-vwap deviation.",
    "vwap_z": "(close - vwap) / vwap_std.",
    "orb_high": "Opening range high for configured open_minutes.",
    "orb_low": "Opening range low for configured open_minutes.",
    "orb_mid": "Opening range midpoint.",
    "orb_width": "Opening range width.",
    "orb_width_pct": "orb_width / orb_mid.",
    "after_orb": "True after opening range window is complete.",
    "above_orb_high": "close > orb_high.",
    "below_orb_low": "close < orb_low.",
    "in_orb_range": "close between orb_low and orb_high.",
    "orb_breakout_dir": "1 above OR high after ORB, -1 below OR low after ORB, else 0.",
    "orb_high_dist": "close - orb_high.",
    "orb_low_dist": "close - orb_low.",
    "prior_day_open": "Previous session open.",
    "prior_day_high": "Previous session high.",
    "prior_day_low": "Previous session low.",
    "prior_day_close": "Previous session close.",
    "prior_day_range": "prior_day_high - prior_day_low.",
    "session_open": "First open of session.",
    "session_high": "Session high.",
    "session_low": "Session low.",
    "session_close": "Last close of session.",
    "gap_from_prior_close": "Current session open minus prior session close.",
    "gap_pct_from_prior_close": "gap / prior_day_close.",
    "ret_1m": "1-minute percent return within session.",
    "tr": "True range approximation within session.",
}


def all_declared_feature_columns() -> list[str]:
    out: list[str] = []
    for cols in FEATURE_COLUMNS.values():
        out.extend(cols)
    return out


def describe_column(name: str) -> str:
    if name in RAW_COLUMN_DESCRIPTIONS:
        return RAW_COLUMN_DESCRIPTIONS[name]
    if name in FEATURE_COLUMN_DESCRIPTIONS:
        return FEATURE_COLUMN_DESCRIPTIONS[name]
    return f"(no description for {name!r})"


def feature_columns_for(module_name: str) -> list[str]:
    if module_name not in FEATURE_COLUMNS:
        raise KeyError(f"Unknown feature module: {module_name!r}")
    return list(FEATURE_COLUMNS[module_name])


def validate_no_registry_duplicates() -> None:
    if len(RAW_COLUMNS) != len(set(RAW_COLUMNS)):
        raise ValueError(f"Duplicate entries in RAW_COLUMNS: {RAW_COLUMNS}")

    seen: set[str] = set()
    for mod, cols in FEATURE_COLUMNS.items():
        for c in cols:
            if c in seen:
                raise ValueError(f"Feature column {c!r} declared in more than one module (duplicate registry)")
            seen.add(c)

    overlap = seen.intersection(set(RAW_COLUMNS))
    if overlap:
        raise ValueError(f"Feature column(s) collide with RAW_COLUMNS: {sorted(overlap)}")
