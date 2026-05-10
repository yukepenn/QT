"""Frozen feature-build specs shared by feature_key and feature modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndicatorsFeatureConfig:
    ema_windows: tuple[int, ...] = ()
    sma_windows: tuple[int, ...] = ()
    rsi_windows: tuple[int, ...] = ()
    macd_tuples: tuple[tuple[int, int, int], ...] = ()  # (fast, slow, signal)
    stochastic_tuples: tuple[tuple[int, int], ...] = ()  # (k_window, d_smooth)
    cci_windows: tuple[int, ...] = ()
    adx_windows: tuple[int, ...] = ()
    # (atr_window, mult_z) where mult_z = int(round(mult * 100)), e.g. 2.0 -> 200
    supertrend_tuples: tuple[tuple[int, int], ...] = ()


@dataclass(frozen=True)
class ChannelsFeatureConfig:
    bb_windows: tuple[int, ...] = ()
    bb_stds: tuple[float, ...] = ()
    bb_bandwidth_lookbacks: tuple[int, ...] = ()
    donchian_windows: tuple[int, ...] = ()


@dataclass(frozen=True)
class PaFeatureConfig:
    """PA feature knobs (swing windows, regime windows, bar-shape thresholds)."""

    swing_windows: tuple[int, ...] = (10, 20, 30, 60)
    regime_windows: tuple[int, ...] = (20, 30, 60)
    atr_window: int = 20
    strong_bar_body_pct: float = 0.55
    close_near_high_threshold: float = 0.70
    close_near_low_threshold: float = 0.30
    doji_body_pct: float = 0.08


@dataclass(frozen=True)
class RegimeFeatureConfig:
    windows: tuple[int, ...] = ()
