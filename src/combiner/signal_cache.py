"""Persistent on-disk cache for per-candidate Layer 2 signal arrays (research only)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]

SIGNAL_ARRAY_NAMES = (
    "side",
    "valid",
    "stop",
    "target_preview",
    "target_mode_code",
    "target_r",
    "risk_preview",
)

_CODE_FINGERPRINT_FILES = (
    Path("src/combiner/precompute.py"),
    Path("src/combiner/signal_cache.py"),
    Path("src/features/feature_key.py"),
    Path("src/features/build_features.py"),
    Path("src/strategies/strategy/base.py"),
)


@dataclass
class SignalCacheKeyParts:
    asset: str
    symbol: str
    start: str
    end: str
    data_fingerprint: str
    strategy: str
    candidate_id: str
    params_hash: str
    feature_key: Any
    strategy_context_key: Any
    code_fingerprint: str


def default_signal_cache_root() -> Path:
    return Path(".cache/qt/candidate_signals")


def short_key(key: str) -> str:
    return key[:12] if len(key) >= 12 else key


def compute_data_fingerprint(raw_df: pd.DataFrame) -> str:
    """Cheap deterministic digest of bar coverage (not full file hash)."""
    n = int(len(raw_df))
    if n == 0:
        return hashlib.sha256(b"empty").hexdigest()
    ts = raw_df["ts_utc"]
    sym = ""
    if "symbol" in raw_df.columns and len(raw_df):
        sym = str(raw_df["symbol"].iloc[0])
    head_ts = [str(x) for x in ts.head(min(3, n)).tolist()]
    tail_ts = [str(x) for x in ts.tail(min(3, n)).tolist()]
    blob: dict[str, Any] = {
        "n": n,
        "min_ts": str(ts.min()),
        "max_ts": str(ts.max()),
        "symbol": sym,
        "head_ts": head_ts,
        "tail_ts": tail_ts,
    }
    for col in ("open", "high", "low", "close", "volume"):
        if col in raw_df.columns:
            a = raw_df[col].to_numpy(dtype=np.float64, copy=False)
            blob[f"{col}_checksum"] = float(np.nansum(a))
    payload = json.dumps(blob, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _hash_file_contents(paths: list[Path], root: Path) -> str:
    h = hashlib.sha256()
    for rel in paths:
        p = root / rel
        if not p.is_file():
            continue
        h.update(rel.as_posix().encode())
        h.update(p.read_bytes())
    return h.hexdigest()


def compute_code_fingerprint() -> str:
    """Prefer git HEAD (+ dirty suffix); else hash of key source files."""
    try:
        head = (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                cwd=_REPO_ROOT,
                stderr=subprocess.DEVNULL,
                timeout=8,
            )
            .decode()
            .strip()
        )
        st = subprocess.check_output(
            ["git", "status", "--porcelain"],
            cwd=_REPO_ROOT,
            stderr=subprocess.DEVNULL,
            timeout=8,
        ).decode()
        dirty = bool(st.strip())
        return f"{head}-dirty" if dirty else head
    except (subprocess.CalledProcessError, FileNotFoundError, OSError, subprocess.TimeoutExpired):
        pass
    return _hash_file_contents(list(_CODE_FINGERPRINT_FILES), _REPO_ROOT)


def build_signal_cache_key(parts: SignalCacheKeyParts) -> str:
    payload = json.dumps(asdict(parts), sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def signal_cache_paths(cache_root: Path, key: str) -> dict[str, Path]:
    d = Path(cache_root) / key[:2] / key
    out: dict[str, Path] = {"dir": d, "metadata": d / "metadata.json"}
    for name in SIGNAL_ARRAY_NAMES:
        out[name] = d / f"{name}.npy"
    return out


def load_signal_cache(cache_root: Path, key: str) -> dict[str, np.ndarray] | None:
    paths = signal_cache_paths(cache_root, key)
    if not paths["metadata"].is_file():
        return None
    for name in SIGNAL_ARRAY_NAMES:
        if not paths[name].is_file():
            return None
    try:
        meta = json.loads(paths["metadata"].read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    arrays: dict[str, np.ndarray] = {}
    for name in SIGNAL_ARRAY_NAMES:
        try:
            arrays[name] = np.load(paths[name], allow_pickle=False)
        except (OSError, ValueError):
            return None
        spec = (meta.get("arrays") or {}).get(name)
        if not isinstance(spec, dict):
            return None
        exp_shape = tuple(spec.get("shape") or ())
        exp_dtype = str(spec.get("dtype") or "")
        if tuple(arrays[name].shape) != exp_shape or str(arrays[name].dtype) != exp_dtype:
            return None
    return arrays


def save_signal_cache(
    cache_root: Path,
    key: str,
    arrays: dict[str, np.ndarray],
    metadata: dict[str, Any],
) -> None:
    paths = signal_cache_paths(cache_root, key)
    final_dir = paths["dir"]
    parent = final_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = parent / f"{key}.staging_{os.getpid()}"
    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)
    staging.mkdir(parents=True)

    array_meta: dict[str, Any] = {}
    for name in SIGNAL_ARRAY_NAMES:
        if name not in arrays:
            raise KeyError(name)
        arr = arrays[name]
        array_meta[name] = {"shape": list(arr.shape), "dtype": str(arr.dtype)}
        np.save(staging / f"{name}.npy", arr, allow_pickle=False)

    meta_out = dict(metadata)
    meta_out["arrays"] = array_meta
    (staging / "metadata.json").write_text(json.dumps(meta_out, indent=2, sort_keys=True, default=str), encoding="utf-8")

    if final_dir.exists():
        shutil.rmtree(final_dir, ignore_errors=True)
    staging.rename(final_dir)


def clear_signal_cache_entry(cache_root: Path, key: str) -> None:
    d = signal_cache_paths(cache_root, key)["dir"]
    if d.exists():
        shutil.rmtree(d, ignore_errors=True)
