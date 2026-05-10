"""PA magnet level column names (kept separate from levels.py to avoid import cycles)."""

from __future__ import annotations


def pa_magnet_level_column_names(swing_windows: tuple[int, ...]) -> list[str]:
    cols = [
        "near_orb_high_known_atr",
        "near_orb_low_known_atr",
        "near_vwap_upper_1_atr",
        "near_vwap_lower_1_atr",
        "near_vwap_upper_2_atr",
        "near_vwap_lower_2_atr",
    ]
    for n in swing_windows:
        nn = int(n)
        cols.extend(
            [
                f"pa_mm_range_up_{nn}",
                f"pa_mm_range_down_{nn}",
                f"near_pa_mm_range_up_atr_{nn}",
                f"near_pa_mm_range_down_atr_{nn}",
            ]
        )
    return cols
