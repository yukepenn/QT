"""Layer 2 candidate signal matrix precompute (feature/context caches, profiling)."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.backtest.fast import prepare_backtest_arrays
from src.combiner.candidate import Candidate, merged_strategy_config
from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config, feature_key_from_config
from src.strategies.loader import load_strategy


def normalize_for_context_cache_key(obj: Any) -> Any:
    """Freeze nested structures for hashable context cache keys (Layer 1–aligned semantics)."""
    if isinstance(obj, dict):
        return tuple(sorted((k, normalize_for_context_cache_key(v)) for k, v in obj.items()))
    if isinstance(obj, list):
        return tuple(normalize_for_context_cache_key(x) for x in obj)
    if isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    return obj


def build_context_cache_key(strategy_name: str, feature_key: Any, strategy_context_key: Any) -> tuple[Any, ...]:
    """Context cache key: (strategy, feature_key_tuple, normalized context_key(cfg)).

    Layer 1 sweep uses ``(fk, strat.context_key(cfg))`` with ``fk = feature_key_from_config(cfg)``.
    Layer 2 prepends ``strategy`` so distinct strategies never share a context bucket.
    """
    ck = strategy_context_key
    if ck is None:
        norm: tuple[Any, ...] = ()
    elif isinstance(ck, tuple):
        norm = tuple(normalize_for_context_cache_key(x) for x in ck)
    else:
        norm = (normalize_for_context_cache_key(ck),)
    return (str(strategy_name), feature_key, norm)


def _strategy_context_key_short(norm: tuple[Any, ...]) -> str:
    blob = json.dumps(norm, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


def _feature_key_short(feature_key: Any) -> str:
    blob = json.dumps(feature_key, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:12]


@dataclass
class CandidateSignalMatrix:
    candidates: list[Candidate]
    candidate_ids: list[str]
    backtest_arrays: dict[str, Any]
    side: np.ndarray
    valid: np.ndarray
    stop: np.ndarray
    target_preview: np.ndarray
    target_mode_code: np.ndarray
    target_r: np.ndarray
    risk_preview: np.ndarray
    meta_arrays: dict[str, np.ndarray]
    raw_bars_rows: int

    @property
    def n_candidates(self) -> int:
        return len(self.candidates)

    @property
    def n_bars(self) -> int:
        return int(self.backtest_arrays["n"])


PROFILE_FIELDNAMES = [
    "candidate_id",
    "strategy",
    "candidate_rank",
    "warning",
    "params_hash_short",
    "feature_key_short",
    "strategy_context_key_short",
    "feature_cache_hit",
    "context_cache_hit",
    "feature_sec",
    "context_sec",
    "signal_sec",
    "total_sec",
    "n_signals",
    "n_long_signals",
    "n_short_signals",
    "error",
]


def write_precompute_profile_summary(profile_csv_path: Path) -> None:
    """Write aggregated `candidate_precompute_profile_summary.csv` (+ `.md`) beside the per-candidate profile."""
    profile_csv_path = Path(profile_csv_path)
    if not profile_csv_path.is_file():
        return
    df = pd.read_csv(profile_csv_path)
    if df.empty:
        return
    if "candidate_id" not in df.columns:
        df = df.copy()
        df["candidate_id"] = [f"__row{i}" for i in range(len(df))]

    def _bhit(col: str) -> pd.Series:
        if col not in df.columns:
            return pd.Series(0, index=df.index)
        ser = df[col]
        return ser.astype(str).str.lower().eq("true") | ser.eq(True)

    df["_fhit"] = _bhit("feature_cache_hit").astype(int)
    df["_fmiss"] = 1 - df["_fhit"]
    df["_chit"] = _bhit("context_cache_hit").astype(int)
    df["_cmiss"] = 1 - df["_chit"]

    for c in ("total_sec", "feature_sec", "context_sec", "signal_sec", "n_signals", "n_long_signals", "n_short_signals"):
        if c not in df.columns:
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")

    gcols = ["strategy", "feature_key_short", "strategy_context_key_short"]
    for gc in gcols:
        if gc not in df.columns:
            df[gc] = ""

    def _sum_min1(s: pd.Series) -> float:
        return float(s.sum(min_count=1)) if s.notna().any() else float("nan")

    out = (
        df.groupby(gcols, dropna=False)
        .agg(
            candidate_count=("candidate_id", "count"),
            n_feature_cache_hits=("_fhit", "sum"),
            n_feature_cache_misses=("_fmiss", "sum"),
            n_context_cache_hits=("_chit", "sum"),
            n_context_cache_misses=("_cmiss", "sum"),
            sum_total_sec=("total_sec", "sum"),
            mean_total_sec=("total_sec", "mean"),
            max_total_sec=("total_sec", "max"),
            sum_feature_sec=("feature_sec", _sum_min1),
            sum_context_sec=("context_sec", _sum_min1),
            sum_signal_sec=("signal_sec", _sum_min1),
            total_signals=("n_signals", "sum"),
            total_long_signals=("n_long_signals", "sum"),
            total_short_signals=("n_short_signals", "sum"),
        )
        .reset_index()
    )
    out_path = profile_csv_path.parent / "candidate_precompute_profile_summary.csv"
    out.to_csv(out_path, index=False)

    md_path = profile_csv_path.parent / "candidate_precompute_profile_summary.md"
    lines = [
        "# Candidate precompute profile summary",
        "",
        f"Source: `{profile_csv_path.name}`",
        "",
        "```",
        out.head(50).to_string(index=False),
        "```",
        "",
    ]
    md_path.write_text("\n".join(lines), encoding="utf-8")


def precompute_candidate_signal_matrices(
    *,
    candidates: list[Candidate],
    asset: str,
    symbol: str,
    start: str,
    end: str,
    data_dir: str | Path = "data/raw/ibkr",
    profile_csv_path: Path | None = None,
    progress_prefix: str = "[precompute]",
) -> CandidateSignalMatrix:
    """Read bars once; build features per feature_key; stack signal arrays (n_c × n_bars).

    Context cache key matches Layer 1: (strategy, feature_key, normalized context_key(cfg)),
    not full params_hash. Optional ``profile_csv_path`` writes per-candidate timings and cache hits.
    """
    if not candidates:
        raise ValueError("no candidates")
    sym = symbol.upper().strip()
    raw = read_bars(asset=asset, symbol=sym, start=start, end=end, data_dir=data_dir)
    if raw.empty:
        raise ValueError(f"empty bars for {sym}")

    n_c = len(candidates)
    canonical_ts: pd.Series | None = None
    backtest_arrays: dict[str, Any] | None = None
    meta_arrays: dict[str, np.ndarray] | None = None
    side = np.zeros((n_c, 0), dtype=np.int8)
    valid = np.zeros((n_c, 0), dtype=np.bool_)
    stop = np.zeros((n_c, 0), dtype=np.float64)
    tgt_preview = np.zeros((n_c, 0), dtype=np.float64)
    tgt_mode = np.zeros((n_c, 0), dtype=np.int8)
    tgt_r = np.zeros((n_c, 0), dtype=np.float64)
    risk_preview = np.zeros((n_c, 0), dtype=np.float64)
    cids: list[str] = []

    feat_cache: dict[str, pd.DataFrame] = {}
    ctx_cache: dict[tuple[Any, ...], Any] = {}
    strategy_cache: dict[str, Any] = {}
    profile_rows: list[dict[str, Any]] = []

    for ci, spec in enumerate(candidates):
        t_row0 = time.perf_counter()
        feature_cache_hit = False
        context_cache_hit = False
        feature_sec = 0.0
        context_sec = 0.0
        signal_sec = 0.0
        err = ""
        n_sig = n_long = n_short = 0
        fk_short = ""
        params_hash_short = str(spec.params_hash or "")[:12]
        strategy_context_key_short = ""

        exc: BaseException | None = None
        print(
            f"{progress_prefix} {ci + 1}/{n_c} candidate_id={spec.candidate_id} strategy={spec.strategy} start",
            flush=True,
        )
        try:
            if spec.strategy not in strategy_cache:
                strategy_cache[spec.strategy] = load_strategy(spec.strategy)
            strat = strategy_cache[spec.strategy]
            if not strat.supports_fast:
                raise ValueError(f"{spec.strategy} does not support fast path")
            cfg = merged_strategy_config(spec)
            strat.validate_config(cfg)
            fk = feature_key_from_config(cfg)
            fk_short = _feature_key_short(fk)

            t_feat0 = time.perf_counter()
            if fk in feat_cache:
                feat_df = feat_cache[fk]
                feature_cache_hit = True
            else:
                feat_df = build_features_from_config(raw, cfg).sort_values("ts_utc", ignore_index=True)
                feat_cache[fk] = feat_df
            feature_sec = time.perf_counter() - t_feat0

            ts = feat_df["ts_utc"]
            if canonical_ts is None:
                canonical_ts = ts.reset_index(drop=True)
                backtest_arrays = prepare_backtest_arrays(feat_df)
                meta_arrays = {
                    "session_date": feat_df["session_date"].to_numpy(copy=False),
                    "minute_from_open": feat_df["minute_from_open"].to_numpy(dtype=np.int32, copy=False),
                    "ts_utc": feat_df["ts_utc"].to_numpy(copy=False),
                    "ts_ny": feat_df["ts_ny"].to_numpy(copy=False) if "ts_ny" in feat_df.columns else np.array([]),
                }
            else:
                if len(feat_df) != len(canonical_ts):
                    raise ValueError(
                        f"length mismatch candidate={spec.candidate_id} n={len(feat_df)} expected={len(canonical_ts)}"
                    )
                if not ts.reset_index(drop=True).equals(canonical_ts):
                    raise ValueError(f"ts_utc mismatch for candidate={spec.candidate_id}")

            miss = [c for c in strat.required_features() if c not in feat_df.columns]
            if miss:
                raise ValueError(f"{spec.candidate_id} missing features {miss}")

            raw_ck = strat.context_key(cfg)
            ctx_key = build_context_cache_key(spec.strategy, fk, raw_ck)
            strategy_context_key_short = _strategy_context_key_short(ctx_key[2])

            t_ctx0 = time.perf_counter()
            if ctx_key in ctx_cache:
                ctx = ctx_cache[ctx_key]
                context_cache_hit = True
            else:
                ctx = strat.prepare_signal_context(feat_df, cfg)
                ctx_cache[ctx_key] = ctx
            context_sec = time.perf_counter() - t_ctx0

            t_sig0 = time.perf_counter()
            sig = strat.generate_signal_arrays_from_context(ctx, cfg)
            signal_sec = time.perf_counter() - t_sig0
            cids.append(spec.candidate_id)

            if side.shape[1] == 0:
                n = len(feat_df)
                side = np.zeros((n_c, n), dtype=np.int8)
                valid = np.zeros((n_c, n), dtype=np.bool_)
                stop = np.zeros((n_c, n), dtype=np.float64)
                tgt_preview = np.zeros((n_c, n), dtype=np.float64)
                tgt_mode = np.zeros((n_c, n), dtype=np.int8)
                tgt_r = np.zeros((n_c, n), dtype=np.float64)
                risk_preview = np.zeros((n_c, n), dtype=np.float64)

            side[ci] = sig["side"].astype(np.int8)
            valid[ci] = sig["valid"].astype(np.bool_)
            stop[ci] = sig["stop"].astype(np.float64)
            tgt_preview[ci] = sig["target_preview"].astype(np.float64)
            tgt_mode[ci] = sig["target_mode_code"].astype(np.int8)
            tgt_r[ci] = sig["target_r"].astype(np.float64)
            risk_preview[ci] = sig.get("risk_preview", np.zeros(len(feat_df), dtype=np.float64)).astype(
                np.float64
            )

            vrow = valid[ci] & (side[ci] != 0)
            n_sig = int(np.sum(vrow))
            n_long = int(np.sum(vrow & (side[ci] == 1)))
            n_short = int(np.sum(vrow & (side[ci] == -1)))
        except Exception as e:
            err = str(e)
            exc = e

        total_sec = time.perf_counter() - t_row0
        fch = "hit" if feature_cache_hit else "miss"
        cch = "hit" if context_cache_hit else "miss"
        print(
            f"{progress_prefix} {ci + 1}/{n_c} done total_sec={total_sec:.2f} signals={n_sig} "
            f"feature_cache={fch} context_cache={cch}",
            flush=True,
        )
        row = {
            "candidate_id": spec.candidate_id,
            "strategy": spec.strategy,
            "candidate_rank": spec.candidate_rank,
            "warning": spec.warning or "",
            "params_hash_short": params_hash_short,
            "feature_key_short": fk_short,
            "strategy_context_key_short": strategy_context_key_short,
            "feature_cache_hit": feature_cache_hit,
            "context_cache_hit": context_cache_hit,
            "feature_sec": round(feature_sec, 4),
            "context_sec": round(context_sec, 4),
            "signal_sec": round(signal_sec, 4),
            "total_sec": round(total_sec, 4),
            "n_signals": n_sig,
            "n_long_signals": n_long,
            "n_short_signals": n_short,
            "error": err,
        }
        profile_rows.append({k: row.get(k, "") for k in PROFILE_FIELDNAMES})
        if err:
            if profile_csv_path is not None and profile_rows:
                _pp = Path(profile_csv_path)
                _pp.parent.mkdir(parents=True, exist_ok=True)
                with _pp.open("w", newline="", encoding="utf-8") as pf:
                    w = csv.DictWriter(pf, fieldnames=PROFILE_FIELDNAMES)
                    w.writeheader()
                    w.writerows(profile_rows)
            assert exc is not None
            raise exc

    assert backtest_arrays is not None and meta_arrays is not None

    if profile_csv_path is not None:
        profile_csv_path = Path(profile_csv_path)
        profile_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with profile_csv_path.open("w", newline="", encoding="utf-8") as pf:
            w = csv.DictWriter(pf, fieldnames=PROFILE_FIELDNAMES)
            w.writeheader()
            w.writerows(profile_rows)
        write_precompute_profile_summary(profile_csv_path)

    return CandidateSignalMatrix(
        candidates=candidates,
        candidate_ids=cids,
        backtest_arrays=backtest_arrays,
        side=side,
        valid=valid,
        stop=stop,
        target_preview=tgt_preview,
        target_mode_code=tgt_mode,
        target_r=tgt_r,
        risk_preview=risk_preview,
        meta_arrays=meta_arrays,
        raw_bars_rows=len(raw),
    )


def build_candidate_signal_arrays(
    candidates: list[Candidate],
    *,
    asset: str,
    symbol: str,
    start: str,
    end: str,
    data_dir: str | Path = "data/raw/ibkr",
) -> tuple[dict[str, Any], dict[str, np.ndarray], pd.DataFrame, dict[str, np.ndarray]]:
    """Backward-compatible alias returning legacy tuple + candidates_used table."""
    csm = precompute_candidate_signal_matrices(
        candidates=candidates, asset=asset, symbol=symbol, start=start, end=end, data_dir=data_dir
    )
    mats = {
        "side": csm.side,
        "valid": csm.valid,
        "stop": csm.stop,
        "target_preview": csm.target_preview,
        "target_mode_code": csm.target_mode_code,
        "target_r": csm.target_r,
        "risk_preview": csm.risk_preview,
    }
    rows = [
        {
            "candidate_idx": i,
            "candidate_id": c.candidate_id,
            "strategy": c.strategy,
            "strategy_family": c.family,
            "priority": c.default_priority,
            "active_start_minute": c.default_active_start_minute,
            "active_end_minute": c.default_active_end_minute,
        }
        for i, c in enumerate(csm.candidates)
    ]
    return csm.backtest_arrays, mats, pd.DataFrame(rows), csm.meta_arrays
