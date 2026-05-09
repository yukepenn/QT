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


@dataclass(frozen=True)
class ChannelsFeatureConfig:
    bb_windows: tuple[int, ...] = ()
    bb_stds: tuple[float, ...] = ()
    bb_bandwidth_lookbacks: tuple[int, ...] = ()
    donchian_windows: tuple[int, ...] = ()


@dataclass(frozen=True)
class RegimeFeatureConfig:
    windows: tuple[int, ...] = ()
