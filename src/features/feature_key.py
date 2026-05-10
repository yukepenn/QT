"""Centralized feature build config and cache key."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

import pandas as pd

from src.features.build_types import ChannelsFeatureConfig, IndicatorsFeatureConfig, PaFeatureConfig, RegimeFeatureConfig
from src.features.build_features import build_basic_features


def _as_iterable(value: Any) -> Iterable[Any] | None:
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        return value
    return [value]


def normalize_int_tuple(value: Any, default: tuple[int, ...]) -> tuple[int, ...]:
    it = _as_iterable(value)
    if it is None:
        return tuple(int(x) for x in default)
    out: list[int] = []
    for x in it:
        try:
            out.append(int(x))
        except (TypeError, ValueError):
            continue
    return tuple(out) if out else tuple(int(x) for x in default)


def normalize_float_tuple(value: Any, default: tuple[float, ...]) -> tuple[float, ...]:
    it = _as_iterable(value)
    if it is None:
        return tuple(float(x) for x in default)
    out: list[float] = []
    for x in it:
        try:
            out.append(float(x))
        except (TypeError, ValueError):
            continue
    return tuple(out) if out else tuple(float(x) for x in default)


def _normalize_macd_tuples(raw: Any) -> tuple[tuple[int, int, int], ...]:
    it = _as_iterable(raw)
    if not it:
        return ()
    out: list[tuple[int, int, int]] = []
    for row in it:
        if isinstance(row, (list, tuple)) and len(row) == 3:
            try:
                out.append((int(row[0]), int(row[1]), int(row[2])))
            except (TypeError, ValueError):
                continue
    return tuple(out)


def _normalize_stoch_tuples(raw: Any) -> tuple[tuple[int, int], ...]:
    it = _as_iterable(raw)
    if not it:
        return ()
    out: list[tuple[int, int]] = []
    for row in it:
        if isinstance(row, (list, tuple)) and len(row) == 2:
            try:
                out.append((int(row[0]), int(row[1])))
            except (TypeError, ValueError):
                continue
    return tuple(out)


def _normalize_supertrend_tuples(raw: Any) -> tuple[tuple[int, int], ...]:
    it = _as_iterable(raw)
    if not it:
        return ()
    out: list[tuple[int, int]] = []
    for row in it:
        if isinstance(row, (list, tuple)) and len(row) == 2:
            try:
                atr_w = int(row[0])
                mult = float(row[1])
                mult_z = int(round(mult * 100.0))
                out.append((atr_w, mult_z))
            except (TypeError, ValueError):
                continue
    return tuple(out)


def indicators_config_from_dict(raw: dict[str, Any] | None) -> IndicatorsFeatureConfig:
    if raw is None:
        return IndicatorsFeatureConfig()
    return IndicatorsFeatureConfig(
        ema_windows=normalize_int_tuple(raw.get("ema_windows"), ()),
        sma_windows=normalize_int_tuple(raw.get("sma_windows"), ()),
        rsi_windows=normalize_int_tuple(raw.get("rsi_windows"), ()),
        macd_tuples=_normalize_macd_tuples(raw.get("macd_tuples")),
        stochastic_tuples=_normalize_stoch_tuples(raw.get("stochastic_tuples")),
        cci_windows=normalize_int_tuple(raw.get("cci_windows"), ()),
        adx_windows=normalize_int_tuple(raw.get("adx_windows"), ()),
        supertrend_tuples=_normalize_supertrend_tuples(raw.get("supertrend_tuples")),
    )


def channels_config_from_dict(raw: dict[str, Any] | None) -> ChannelsFeatureConfig:
    if raw is None:
        return ChannelsFeatureConfig()
    return ChannelsFeatureConfig(
        bb_windows=normalize_int_tuple(raw.get("bb_windows"), ()),
        bb_stds=normalize_float_tuple(raw.get("bb_stds"), ()),
        bb_bandwidth_lookbacks=normalize_int_tuple(raw.get("bb_bandwidth_lookbacks"), ()),
        donchian_windows=normalize_int_tuple(raw.get("donchian_windows"), ()),
    )


def regime_config_from_dict(raw: dict[str, Any] | None) -> RegimeFeatureConfig:
    if raw is None:
        return RegimeFeatureConfig()
    return RegimeFeatureConfig(windows=normalize_int_tuple(raw.get("windows"), ()))


def pa_config_from_dict(raw: dict[str, Any] | None) -> PaFeatureConfig:
    if raw is None or not isinstance(raw, dict):
        return PaFeatureConfig()
    return PaFeatureConfig(
        swing_windows=normalize_int_tuple(raw.get("swing_windows"), (10, 20, 30, 60)),
        regime_windows=normalize_int_tuple(raw.get("regime_windows"), (20, 30, 60)),
        atr_window=int(raw.get("atr_window", 20)),
        strong_bar_body_pct=float(raw.get("strong_bar_body_pct", 0.55)),
        close_near_high_threshold=float(raw.get("close_near_high_threshold", 0.70)),
        close_near_low_threshold=float(raw.get("close_near_low_threshold", 0.30)),
        doji_body_pct=float(raw.get("doji_body_pct", 0.08)),
    )


@dataclass(frozen=True)
class FeatureBuildConfig:
    orb_open_minutes: int = 15
    vwap_bands: tuple[float, ...] = (1.0, 2.0)
    vol_windows: tuple[int, ...] = (5, 15, 30)
    price_action_windows: tuple[int, ...] = (3, 5, 10, 20, 30, 60)
    volume_windows: tuple[int, ...] = (20, 30, 60)
    indicators: IndicatorsFeatureConfig = field(default_factory=IndicatorsFeatureConfig)
    channels: ChannelsFeatureConfig = field(default_factory=ChannelsFeatureConfig)
    regime: RegimeFeatureConfig = field(default_factory=RegimeFeatureConfig)
    pa: PaFeatureConfig = field(default_factory=PaFeatureConfig)


def feature_config_from_strategy_config(cfg: dict[str, Any]) -> FeatureBuildConfig:
    feat = cfg.get("features") or {}
    return FeatureBuildConfig(
        orb_open_minutes=int(feat.get("orb_open_minutes", 15)),
        vwap_bands=normalize_float_tuple(feat.get("vwap_bands"), (1.0, 2.0)),
        vol_windows=normalize_int_tuple(feat.get("vol_windows"), (5, 15, 30)),
        price_action_windows=normalize_int_tuple(feat.get("price_action_windows"), (3, 5, 10, 20, 30, 60)),
        volume_windows=normalize_int_tuple(feat.get("volume_windows"), (20, 30, 60)),
        indicators=indicators_config_from_dict(feat.get("indicators") if isinstance(feat.get("indicators"), dict) else None),
        channels=channels_config_from_dict(feat.get("channels") if isinstance(feat.get("channels"), dict) else None),
        regime=regime_config_from_dict(feat.get("regime") if isinstance(feat.get("regime"), dict) else None),
        pa=pa_config_from_dict(feat.get("pa") if isinstance(feat.get("pa"), dict) else None),
    )


def feature_key_from_config(cfg: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    f = feature_config_from_strategy_config(cfg)
    return (
        ("orb_open_minutes", int(f.orb_open_minutes)),
        ("vwap_bands", tuple(float(x) for x in f.vwap_bands)),
        ("vol_windows", tuple(int(x) for x in f.vol_windows)),
        ("price_action_windows", tuple(int(x) for x in f.price_action_windows)),
        ("volume_windows", tuple(int(x) for x in f.volume_windows)),
        ("indicators", f.indicators),
        ("channels", f.channels),
        ("regime", f.regime),
        ("pa", f.pa),
    )


def build_features_from_config(raw_df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    f = feature_config_from_strategy_config(cfg)
    vol_merged = tuple(sorted(set(int(x) for x in f.vol_windows) | {int(f.pa.atr_window), 20}))
    return build_basic_features(
        raw_df,
        orb_open_minutes=int(f.orb_open_minutes),
        vwap_bands=tuple(float(x) for x in f.vwap_bands),
        vol_windows=vol_merged,
        price_action_windows=tuple(int(x) for x in f.price_action_windows),
        volume_windows=tuple(int(x) for x in f.volume_windows),
        indicators=f.indicators,
        channels=f.channels,
        regime=f.regime,
        pa=f.pa,
        copy=True,
        allow_overwrite=False,
    )
