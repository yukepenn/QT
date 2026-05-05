"""Centralized feature build config and cache key.

Goal: every place that builds `build_basic_features` should derive both:
- a stable cache key (hashable, deterministic), and
- a normalized FeatureBuildConfig carrying all knobs that affect feature columns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

import pandas as pd

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


@dataclass(frozen=True)
class FeatureBuildConfig:
    orb_open_minutes: int = 15
    vwap_bands: tuple[float, ...] = (1.0, 2.0)
    vol_windows: tuple[int, ...] = (5, 15, 30)
    price_action_windows: tuple[int, ...] = (3, 5, 10, 20, 30, 60)
    volume_windows: tuple[int, ...] = (20, 30, 60)


def feature_config_from_strategy_config(cfg: dict[str, Any]) -> FeatureBuildConfig:
    feat = cfg.get("features") or {}
    return FeatureBuildConfig(
        orb_open_minutes=int(feat.get("orb_open_minutes", 15)),
        vwap_bands=normalize_float_tuple(feat.get("vwap_bands"), (1.0, 2.0)),
        vol_windows=normalize_int_tuple(feat.get("vol_windows"), (5, 15, 30)),
        price_action_windows=normalize_int_tuple(feat.get("price_action_windows"), (3, 5, 10, 20, 30, 60)),
        volume_windows=normalize_int_tuple(feat.get("volume_windows"), (20, 30, 60)),
    )


def feature_key_from_config(cfg: dict[str, Any]) -> tuple[tuple[str, Any], ...]:
    f = feature_config_from_strategy_config(cfg)
    return (
        ("orb_open_minutes", int(f.orb_open_minutes)),
        ("vwap_bands", tuple(float(x) for x in f.vwap_bands)),
        ("vol_windows", tuple(int(x) for x in f.vol_windows)),
        ("price_action_windows", tuple(int(x) for x in f.price_action_windows)),
        ("volume_windows", tuple(int(x) for x in f.volume_windows)),
    )


def build_features_from_config(raw_df: pd.DataFrame, cfg: dict[str, Any]) -> pd.DataFrame:
    f = feature_config_from_strategy_config(cfg)
    return build_basic_features(
        raw_df,
        orb_open_minutes=int(f.orb_open_minutes),
        vwap_bands=tuple(float(x) for x in f.vwap_bands),
        vol_windows=tuple(int(x) for x in f.vol_windows),
        price_action_windows=tuple(int(x) for x in f.price_action_windows),
        volume_windows=tuple(int(x) for x in f.volume_windows),
        copy=True,
        allow_overwrite=False,
    )

