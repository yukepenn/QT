"""Unit tests for Layer 2 persistent signal cache helpers."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.combiner.signal_cache import (
    SignalCacheKeyParts,
    build_signal_cache_key,
    clear_signal_cache_entry,
    compute_data_fingerprint,
    default_signal_cache_root,
    load_signal_cache,
    save_signal_cache,
    short_key,
    signal_cache_paths,
)


def test_build_signal_cache_key_stable() -> None:
    p1 = SignalCacheKeyParts(
        asset="equity",
        symbol="QQQ",
        start="2025-01-01",
        end="2025-01-31",
        data_fingerprint="abc",
        strategy="failed_orb",
        candidate_id="X001",
        params_hash="deadbeef",
        feature_key=(("orb_open_minutes", 15),),
        strategy_context_key=("ctx", 1),
        code_fingerprint="git123",
    )
    p2 = SignalCacheKeyParts(
        asset="equity",
        symbol="QQQ",
        start="2025-01-01",
        end="2025-01-31",
        data_fingerprint="abc",
        strategy="failed_orb",
        candidate_id="X001",
        params_hash="deadbeef",
        feature_key=(("orb_open_minutes", 15),),
        strategy_context_key=("ctx", 1),
        code_fingerprint="git123",
    )
    assert build_signal_cache_key(p1) == build_signal_cache_key(p2)


def test_key_changes_with_fields() -> None:
    base = dict(
        asset="equity",
        symbol="QQQ",
        start="2025-01-01",
        end="2025-01-31",
        data_fingerprint="dfp",
        strategy="failed_orb",
        candidate_id="A",
        params_hash="p1",
        feature_key=(("k", 1),),
        strategy_context_key=("c",),
        code_fingerprint="code",
    )
    k0 = build_signal_cache_key(SignalCacheKeyParts(**base))
    assert build_signal_cache_key(SignalCacheKeyParts(**{**base, "candidate_id": "B"})) != k0
    assert build_signal_cache_key(SignalCacheKeyParts(**{**base, "params_hash": "p2"})) != k0
    assert build_signal_cache_key(SignalCacheKeyParts(**{**base, "feature_key": (("k", 2),)})) != k0
    assert build_signal_cache_key(SignalCacheKeyParts(**{**base, "data_fingerprint": "other"})) != k0
    assert build_signal_cache_key(SignalCacheKeyParts(**{**base, "code_fingerprint": "x"})) != k0


def test_short_key() -> None:
    assert short_key("abcdef0123456789") == "abcdef012345"


def test_default_signal_cache_root() -> None:
    assert default_signal_cache_root() == Path(".cache/qt/candidate_signals")


def test_compute_data_fingerprint_deterministic() -> None:
    df = pd.DataFrame(
        {
            "ts_utc": pd.to_datetime(["2025-01-02 14:30:00+00:00", "2025-01-02 14:31:00+00:00"]),
            "symbol": ["QQQ", "QQQ"],
            "open": [100.0, 101.0],
            "high": [101.0, 102.0],
            "low": [99.0, 100.0],
            "close": [100.5, 101.5],
            "volume": [1000.0, 2000.0],
        }
    )
    assert compute_data_fingerprint(df) == compute_data_fingerprint(df)


def test_save_load_roundtrip(tmp_path: Path) -> None:
    key = "a" * 64
    n = 5
    arrays = {
        "side": np.zeros(n, dtype=np.int8),
        "valid": np.ones(n, dtype=np.bool_),
        "stop": np.full(n, 1.5, dtype=np.float64),
        "target_preview": np.zeros(n, dtype=np.float64),
        "target_mode_code": np.zeros(n, dtype=np.int8),
        "target_r": np.ones(n, dtype=np.float64),
        "risk_preview": np.zeros(n, dtype=np.float64),
    }
    meta = {
        "cache_key": key,
        "candidate_id": "test",
        "strategy": "failed_orb",
    }
    save_signal_cache(tmp_path, key, arrays, meta)
    loaded = load_signal_cache(tmp_path, key)
    assert loaded is not None
    for name in arrays:
        np.testing.assert_array_equal(loaded[name], arrays[name])
    paths = signal_cache_paths(tmp_path, key)
    assert paths["metadata"].is_file()
    raw = paths["metadata"].read_text(encoding="utf-8")
    assert "cache_key" in raw


def test_incomplete_cache_returns_none(tmp_path: Path) -> None:
    key = "b" * 64
    d = signal_cache_paths(tmp_path, key)["dir"]
    d.mkdir(parents=True)
    np.save(d / "side.npy", np.zeros(3, dtype=np.int8))
    assert load_signal_cache(tmp_path, key) is None


def test_clear_signal_cache_entry(tmp_path: Path) -> None:
    key = "c" * 64
    arrays = {
        "side": np.zeros(2, dtype=np.int8),
        "valid": np.ones(2, dtype=np.bool_),
        "stop": np.zeros(2, dtype=np.float64),
        "target_preview": np.zeros(2, dtype=np.float64),
        "target_mode_code": np.zeros(2, dtype=np.int8),
        "target_r": np.zeros(2, dtype=np.float64),
        "risk_preview": np.zeros(2, dtype=np.float64),
    }
    save_signal_cache(tmp_path, key, arrays, {"cache_key": key})
    clear_signal_cache_entry(tmp_path, key)
    assert load_signal_cache(tmp_path, key) is None
