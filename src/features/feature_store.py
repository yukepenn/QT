"""FeatureStore v1: centralized raw-bar loading + in-memory feature DataFrame caching.

This is an in-memory reuse layer only (not persistent). It preserves feature behavior by
delegating to `feature_key_from_config` + `build_features_from_config`.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config, feature_key_from_config


def normalize_feature_store_key(obj: Any) -> Any:
    """Freeze nested structures to a hashable key for dict caching."""
    if isinstance(obj, dict):
        return tuple(sorted((k, normalize_feature_store_key(v)) for k, v in obj.items()))
    if isinstance(obj, list):
        return tuple(normalize_feature_store_key(x) for x in obj)
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    return obj


@dataclass
class FeatureStoreStats:
    raw_load_count: int = 0
    feature_requests: int = 0
    feature_cache_hits: int = 0
    feature_cache_misses: int = 0
    raw_rows: int | None = None
    last_symbol: str | None = None
    last_start: str | None = None
    last_end: str | None = None


class FeatureStore:
    def __init__(
        self,
        *,
        asset: str,
        symbol: str,
        start: str,
        end: str,
        data_dir: str | Path = "data/raw/ibkr",
        raw_df: pd.DataFrame | None = None,
    ) -> None:
        self.asset = str(asset)
        self.symbol = str(symbol).upper().strip()
        self.start = str(start)
        self.end = str(end)
        self.data_dir = data_dir
        self._raw: pd.DataFrame | None = raw_df
        self._cache: dict[Any, pd.DataFrame] = {}
        self.stats = FeatureStoreStats(
            raw_load_count=0,
            feature_requests=0,
            feature_cache_hits=0,
            feature_cache_misses=0,
            raw_rows=None if raw_df is None else int(len(raw_df)),
            last_symbol=self.symbol,
            last_start=self.start,
            last_end=self.end,
        )

    def get_raw(self) -> pd.DataFrame:
        if self._raw is None:
            self.stats.raw_load_count += 1
            raw = read_bars(
                asset=self.asset,
                symbol=self.symbol,
                start=self.start,
                end=self.end,
                data_dir=self.data_dir,
            )
            self._raw = raw
            self.stats.raw_rows = int(len(raw))
            self.stats.last_symbol = self.symbol
            self.stats.last_start = self.start
            self.stats.last_end = self.end
        return self._raw

    def clear(self) -> None:
        self._cache.clear()

    def has_features(self, config: dict[str, Any]) -> bool:
        fk = feature_key_from_config(config)
        k = normalize_feature_store_key(fk)
        return k in self._cache

    def get_features(self, config: dict[str, Any]) -> pd.DataFrame:
        fk = feature_key_from_config(config)
        return self.get_features_by_key(fk, config)

    def get_features_by_key(self, feature_key: Any, config: dict[str, Any]) -> pd.DataFrame:
        k = normalize_feature_store_key(feature_key)
        self.stats.feature_requests += 1
        if k in self._cache:
            self.stats.feature_cache_hits += 1
            return self._cache[k]
        self.stats.feature_cache_misses += 1
        raw = self.get_raw()
        feat = build_features_from_config(raw, config).sort_values("ts_utc", ignore_index=True)
        self._cache[k] = feat
        return feat

    def stats_dict(self) -> dict[str, Any]:
        d = asdict(self.stats)
        d["asset"] = self.asset
        d["symbol"] = self.symbol
        d["start"] = self.start
        d["end"] = self.end
        d["cache_entries"] = int(len(self._cache))
        return d

    def write_stats(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.stats_dict(), indent=2, sort_keys=True, default=str), encoding="utf-8")


def feature_store_from_bars(
    raw_df: pd.DataFrame,
    *,
    asset: str,
    symbol: str,
    start: str,
    end: str,
    data_dir: str | Path = "data/raw/ibkr",
) -> FeatureStore:
    return FeatureStore(asset=asset, symbol=symbol, start=start, end=end, data_dir=data_dir, raw_df=raw_df)

