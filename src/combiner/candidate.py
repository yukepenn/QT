"""Layer 1 candidate YAMLs, signal precompute, and candidate-set selection."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import time
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.backtest.fast import prepare_backtest_arrays
from src.data.read_bars import read_bars
from src.features.feature_key import build_features_from_config, feature_key_from_config
from src.strategies.loader import deep_update, load_strategy, load_strategy_config


def _finalize_entry_start(cfg: dict[str, Any]) -> None:
    sig = cfg.setdefault("signal", {})
    if sig.get("entry_start_minute") is None:
        orb_m = int((cfg.get("features") or {}).get("orb_open_minutes", 15))
        sig["entry_start_minute"] = orb_m


def merged_strategy_config(spec: Candidate) -> dict[str, Any]:
    base = load_strategy_config(spec.strategy)
    cfg = deep_update(base, spec.config)
    _finalize_entry_start(cfg)
    return cfg


def _rank_from_candidate_id(cid: str) -> int:
    m = re.search(r"_(\d+)$", cid.strip())
    return int(m.group(1)) if m else 999


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    strategy: str
    asset: str
    symbol: str
    candidate_rank: int
    source_sweep_path: str
    source_results_csv: str
    params_hash: str
    config: dict[str, Any]
    metrics: dict[str, Any]
    metadata: dict[str, Any]
    selection: dict[str, Any]
    family: str
    conflict_group: str
    default_priority: int
    default_active_start_minute: int
    default_active_end_minute: int
    warning: str

    @property
    def strategy_family(self) -> str:
        return self.family

    @property
    def priority(self) -> int:
        return self.default_priority

    @property
    def active_start_minute(self) -> int:
        return self.default_active_start_minute

    @property
    def active_end_minute(self) -> int:
        return self.default_active_end_minute

    @property
    def source(self) -> dict[str, Any]:
        return {
            "results_csv": self.source_results_csv,
            "sweep_folder": self.source_sweep_path,
        }


CandidateSpec = Candidate


def load_candidate_yaml(path: Path) -> Candidate:
    with path.open(encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"invalid candidate yaml {path}")
    cid = str(raw["candidate_id"])
    meta = dict(raw.get("metadata") or {})
    sel = dict(raw.get("selection") or {})
    src = dict(raw.get("source") or {})
    cfg = dict(raw.get("config") or {})
    ph = ""
    blob = json.dumps(cfg, sort_keys=True, default=str).encode("utf-8")
    ph = hashlib.sha256(blob).hexdigest()[:12]
    family = str(meta.get("family", raw.get("strategy_family", "unknown")))
    return Candidate(
        candidate_id=cid,
        strategy=str(raw["strategy"]),
        asset=str(raw.get("asset", "equity")),
        symbol=str(raw["symbol"]),
        candidate_rank=int(raw.get("candidate_rank", _rank_from_candidate_id(cid))),
        source_sweep_path=str(src.get("sweep_folder", "")),
        source_results_csv=str(src.get("results_csv", "")),
        params_hash=ph,
        config=cfg,
        metrics=dict(raw.get("metrics") or {}),
        metadata=meta,
        selection=sel,
        family=family,
        conflict_group=str(meta.get("conflict_group", raw.get("conflict_group", "QQQ_directional"))),
        default_priority=int(meta.get("default_priority", raw.get("default_priority", 50))),
        default_active_start_minute=int(
            meta.get("default_active_start_minute", raw.get("default_active_start_minute", 0))
        ),
        default_active_end_minute=int(
            meta.get("default_active_end_minute", raw.get("default_active_end_minute", 389))
        ),
        warning=str(sel.get("warning", "") or ""),
    )


def load_candidates(candidate_root: Path) -> list[Candidate]:
    paths = sorted(candidate_root.glob("*.yaml"))
    return [load_candidate_yaml(p) for p in paths]


def select_candidate_set(
    candidates: list[Candidate],
    profile: dict[str, Any],
    *,
    top_per_strategy: int,
) -> list[Candidate]:
    """Filter candidates using a named profile dict from Layer 2 YAML."""
    out = list(candidates)
    if profile.get("include_strategies"):
        st = set(str(x) for x in profile["include_strategies"])
        out = [c for c in out if c.strategy in st]
    if profile.get("strategies"):
        st = set(str(x) for x in profile["strategies"])
        out = [c for c in out if c.strategy in st]
    if profile.get("exclude_strategies"):
        ex = set(str(x) for x in profile["exclude_strategies"])
        out = [c for c in out if c.strategy not in ex]
    if profile.get("include_families"):
        fs = set(str(x) for x in profile["include_families"])
        out = [c for c in out if c.family in fs]
    if profile.get("exclude_families"):
        ex = set(str(x) for x in profile["exclude_families"])
        out = [c for c in out if c.family not in ex]
    strict_only = bool(profile.get("strict_only", False))
    if strict_only:
        out = [c for c in out if not str(c.warning or "").strip()]
    if not bool(profile.get("include_warnings", True)):
        out = [c for c in out if not str(c.warning or "").strip()]
    if profile.get("candidate_ids"):
        want = set(str(x) for x in profile["candidate_ids"])
        out = [c for c in out if c.candidate_id in want]
    max_total = profile.get("max_total_candidates")
    yaml_cap = profile.get("max_per_strategy")
    if yaml_cap is not None:
        mps = min(int(yaml_cap), int(top_per_strategy))
    else:
        mps = int(top_per_strategy)
    by_s: dict[str, list[Candidate]] = {}
    for c in out:
        by_s.setdefault(c.strategy, []).append(c)
    trimmed: list[Candidate] = []
    for s in sorted(by_s.keys()):
        rows = sorted(by_s[s], key=lambda x: (x.candidate_rank, x.candidate_id))
        trimmed.extend(rows[:mps])
    out = trimmed
    if max_total is not None and int(max_total) > 0:
        out = sorted(out, key=lambda x: (-x.default_priority, x.candidate_rank))[: int(max_total)]
    return sorted(out, key=lambda x: x.candidate_id)


def resolve_candidate_universe_for_grid(
    raw_eligible: list[Candidate],
    base_cfg: dict[str, Any],
    combo_rows: list[dict[str, Any]],
    *,
    reserved_keys: frozenset[str] | None = None,
) -> list[Candidate]:
    """Union of candidates that any sweep grid row can select (generic).

    For each combo, resolves ``candidate_set`` + ``top_per_strategy`` against
    ``base_cfg["candidate_sets"]`` using the same rules as :func:`select_candidate_set`.
    If no names resolve (e.g. missing grid), returns ``raw_eligible`` unchanged.
    """
    _ = reserved_keys  # reserved for future grid keys that affect selection
    sets_cfg = base_cfg.get("candidate_sets") or {}
    want_ids: set[str] = set()
    for combo in combo_rows:
        cs_name = str(combo.get("candidate_set", "") or "")
        if cs_name not in sets_cfg:
            continue
        tps = int(combo.get("top_per_strategy", 1))
        profile = dict(sets_cfg[cs_name])
        selected = select_candidate_set(raw_eligible, profile, top_per_strategy=tps)
        for c in selected:
            want_ids.add(c.candidate_id)
    if not want_ids:
        return list(raw_eligible)
    order = {c.candidate_id: i for i, c in enumerate(raw_eligible)}
    out = [c for c in raw_eligible if c.candidate_id in want_ids]
    out.sort(key=lambda c: order.get(c.candidate_id, 10**9))
    return out


def build_enabled_mask(universe: list[Candidate], selected: list[Candidate]) -> np.ndarray:
    """Align with precomputed matrices: 1 = candidate included in this combiner run/sweep row."""
    sel = {c.candidate_id for c in selected}
    return np.array([1 if c.candidate_id in sel else 0 for c in universe], dtype=np.int8)


def write_candidates_used(candidates: list[Candidate], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "candidate_id": c.candidate_id,
            "strategy": c.strategy,
            "symbol": c.symbol,
            "candidate_rank": c.candidate_rank,
            "priority": c.default_priority,
            "family": c.family,
            "warning": c.warning,
        }
        for c in candidates
    ]
    pd.DataFrame(rows).to_csv(path, index=False)


def encode_candidate_metadata(candidates: list[Candidate]) -> tuple[
    dict[str, int],
    dict[str, int],
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    """Integer codes + aligned float/int arrays for Numba."""
    strategies = sorted({c.strategy for c in candidates})
    families = sorted({c.family for c in candidates})
    st_map = {s: i for i, s in enumerate(strategies)}
    fa_map = {f: i for i, f in enumerate(families)}
    n = len(candidates)
    pri = np.zeros(n, dtype=np.float64)
    score = np.zeros(n, dtype=np.float64)
    rank = np.zeros(n, dtype=np.int32)
    ast = np.zeros(n, dtype=np.int32)
    aen = np.zeros(n, dtype=np.int32)
    sc = np.zeros(n, dtype=np.int32)
    fc = np.zeros(n, dtype=np.int32)
    warn = np.zeros(n, dtype=np.bool_)
    for i, c in enumerate(candidates):
        sel = c.selection or {}
        pri[i] = float(c.default_priority)
        score[i] = float(sel.get("score", 0.0) or 0.0)
        rank[i] = int(c.candidate_rank)
        ast[i] = int(c.default_active_start_minute)
        aen[i] = int(c.default_active_end_minute)
        sc[i] = int(st_map[c.strategy])
        fc[i] = int(fa_map[c.family])
        warn[i] = bool(str(c.warning or "").strip())
    return st_map, fa_map, pri, score, rank, ast, aen, sc, fc, warn


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

    Optional ``profile_csv_path`` writes per-candidate timings, signal counts, and cache hits.
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
    ctx_cache: dict[tuple[str, str], Any] = {}
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
        ctx_short = str(spec.params_hash or "")[:12]

        exc: BaseException | None = None
        print(
            f"{progress_prefix} {ci + 1}/{n_c} candidate_id={spec.candidate_id} strategy={spec.strategy} start",
            flush=True,
        )
        try:
            strat = load_strategy(spec.strategy)
            if not strat.supports_fast:
                raise ValueError(f"{spec.strategy} does not support fast path")
            cfg = merged_strategy_config(spec)
            strat.validate_config(cfg)
            fk = feature_key_from_config(cfg)
            fk_short = fk[:24] if len(fk) > 24 else fk

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

            ctx_key = (fk, str(spec.params_hash))
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
        profile_rows.append(
            {
                "candidate_id": spec.candidate_id,
                "strategy": spec.strategy,
                "candidate_rank": spec.candidate_rank,
                "warning": spec.warning or "",
                "feature_key_short": fk_short,
                "context_key_short": ctx_short,
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
        )
        if err:
            if profile_csv_path is not None and profile_rows:
                _pp = Path(profile_csv_path)
                _pp.parent.mkdir(parents=True, exist_ok=True)
                with _pp.open("w", newline="", encoding="utf-8") as pf:
                    w = csv.DictWriter(pf, fieldnames=list(profile_rows[0].keys()))
                    w.writeheader()
                    w.writerows(profile_rows)
            assert exc is not None
            raise exc

    assert backtest_arrays is not None and meta_arrays is not None

    if profile_csv_path is not None:
        profile_csv_path = Path(profile_csv_path)
        profile_csv_path.parent.mkdir(parents=True, exist_ok=True)
        with profile_csv_path.open("w", newline="", encoding="utf-8") as pf:
            w = csv.DictWriter(pf, fieldnames=list(profile_rows[0].keys()))
            w.writeheader()
            w.writerows(profile_rows)

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


def apply_combiner_rules(spec: Candidate, strategy_rules: dict[str, Any]) -> Candidate:
    rules = strategy_rules.get(spec.strategy) or {}
    if not rules:
        return spec
    meta = dict(spec.metadata)
    if "priority" in rules:
        meta["default_priority"] = int(rules["priority"])
    kw: dict[str, Any] = {"metadata": meta}
    if "priority" in rules:
        kw["default_priority"] = int(rules["priority"])
    if "active_start_minute" in rules:
        kw["default_active_start_minute"] = int(rules["active_start_minute"])
    if "active_end_minute" in rules:
        kw["default_active_end_minute"] = int(rules["active_end_minute"])
    return replace(spec, **kw) if kw else spec


def filter_candidates(
    candidates: list[Candidate],
    *,
    strategies: list[str] | None = None,
    candidate_ids: list[str] | None = None,
    top_per_strategy: int | None = None,
) -> list[Candidate]:
    out = list(candidates)
    if candidate_ids:
        want = set(candidate_ids)
        out = [c for c in out if c.candidate_id in want]
    if strategies:
        st = set(strategies)
        out = [c for c in out if c.strategy in st]
    out.sort(key=lambda c: c.candidate_id)
    if top_per_strategy is not None and top_per_strategy > 0:
        by_s: dict[str, list[Candidate]] = {}
        for c in out:
            by_s.setdefault(c.strategy, []).append(c)
        trimmed: list[Candidate] = []
        for s in sorted(by_s.keys()):
            trimmed.extend(sorted(by_s[s], key=lambda x: (x.candidate_rank, x.candidate_id))[:top_per_strategy])
        out = sorted(trimmed, key=lambda x: x.candidate_id)
    return out


def _min_abs_diff_two_sorted_minutes(m1: np.ndarray, m2: np.ndarray) -> float:
    """Minimum |a - b| for minute-of-day integers; O(n log n + m log m + n + m)."""
    if m1.size == 0 or m2.size == 0:
        return float("nan")
    a = np.sort(m1.astype(np.int64, copy=False).ravel())
    b = np.sort(m2.astype(np.int64, copy=False).ravel())
    i = j = 0
    best = abs(int(a[0]) - int(b[0]))
    while i < len(a) and j < len(b):
        best = min(best, abs(int(a[i]) - int(b[j])))
        if best == 0:
            return 0.0
        if a[i] < b[j]:
            i += 1
        else:
            j += 1
    return float(best)


def write_candidate_diagnostics(
    csm: CandidateSignalMatrix,
    out_dir: Path,
    *,
    enabled_mask: np.ndarray | None = None,
) -> None:
    """Write overlap / conflict CSVs (fast; vectorized)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    nc, n = csm.side.shape
    mask = np.ones(nc, dtype=np.bool_) if enabled_mask is None else enabled_mask.astype(np.bool_)
    minute = csm.meta_arrays["minute_from_open"].astype(np.int64)
    ts = csm.meta_arrays["ts_utc"]

    t0 = time.perf_counter()
    print(f"[diagnostics] writing candidate_signal_summary.csv... C={nc} N={n}", flush=True)
    rows_sig = []
    med_by_ci = np.full(nc, np.nan, dtype=np.float64)
    for ci in range(nc):
        if not mask[ci]:
            continue
        c = csm.candidates[ci]
        v = csm.valid[ci] & (csm.side[ci] != 0)
        sig_n = int(np.sum(v))
        long_n = int(np.sum(v & (csm.side[ci] == 1)))
        short_n = int(np.sum(v & (csm.side[ci] == -1)))
        ix = np.flatnonzero(v)
        first_ts = ""
        last_ts = ""
        if sig_n:
            first_ts = str(pd.Timestamp(ts[ix[0]]))
            last_ts = str(pd.Timestamp(ts[ix[-1]]))
        avg_m = float(np.mean(minute[ix])) if sig_n else np.nan
        med_m = float(np.median(minute[ix])) if sig_n else np.nan
        med_by_ci[ci] = med_m
        rows_sig.append(
            {
                "candidate_id": c.candidate_id,
                "strategy": c.strategy,
                "family": c.family,
                "warning": c.warning,
                "candidate_rank": c.candidate_rank,
                "priority": c.default_priority,
                "score": float(c.selection.get("score", 0) or 0),
                "signals": sig_n,
                "long_signals": long_n,
                "short_signals": short_n,
                "first_signal_ts": first_ts,
                "last_signal_ts": last_ts,
                "avg_signal_minute": avg_m,
                "median_signal_minute": med_m,
                "active_start": c.default_active_start_minute,
                "active_end": c.default_active_end_minute,
            }
        )
    pd.DataFrame(rows_sig).to_csv(out_dir / "candidate_signal_summary.csv", index=False)

    print("[diagnostics] building overlap matrices...", flush=True)
    vmask = (csm.valid & (csm.side != 0) & mask.reshape(-1, 1)).astype(np.int8, copy=False)
    lmask = (csm.valid & (csm.side == 1) & mask.reshape(-1, 1)).astype(np.int8, copy=False)
    smask = (csm.valid & (csm.side == -1) & mask.reshape(-1, 1)).astype(np.int8, copy=False)

    v_i32 = vmask.astype(np.int32, copy=False)
    l_i32 = lmask.astype(np.int32, copy=False)
    s_i32 = smask.astype(np.int32, copy=False)

    same_bar_overlap = v_i32 @ v_i32.T
    same_direction_same_bar = (l_i32 @ l_i32.T) + (s_i32 @ s_i32.T)
    opposite_side_same_bar = (l_i32 @ s_i32.T) + (s_i32 @ l_i32.T)

    # Same-day overlap: candidate has any signal in session.
    session_id = np.asarray(csm.meta_arrays["session_date"])
    _, inv = np.unique(session_id, return_inverse=True)
    s_cnt = int(inv.max() + 1) if inv.size else 0
    print(f"[diagnostics] building session overlap... S={s_cnt}", flush=True)
    session_mat = np.zeros((nc, s_cnt), dtype=np.int8)
    for ci in range(nc):
        if not mask[ci]:
            continue
        ix = np.flatnonzero(vmask[ci].astype(np.bool_, copy=False))
        if ix.size == 0:
            continue
        np.maximum.at(session_mat[ci], inv[ix], 1)
    session_i32 = session_mat.astype(np.int32, copy=False)
    same_day_overlap = session_i32 @ session_i32.T

    print("[diagnostics] writing candidate_overlap_matrix.csv...", flush=True)
    ids = [csm.candidates[i].candidate_id for i in range(nc)]
    pd.DataFrame(same_bar_overlap.astype(np.int32), index=ids, columns=ids).to_csv(out_dir / "candidate_overlap_matrix.csv")

    print("[diagnostics] writing candidate_conflict_summary.csv...", flush=True)
    pairs: list[dict[str, Any]] = []
    for ci in range(nc):
        if not mask[ci]:
            continue
        a = csm.candidates[ci]
        for cj in range(ci + 1, nc):
            if not mask[cj]:
                continue
            b = csm.candidates[cj]
            approx_md = float(abs(med_by_ci[ci] - med_by_ci[cj])) if np.isfinite(med_by_ci[ci]) and np.isfinite(med_by_ci[cj]) else float("nan")
            pairs.append(
                {
                    "candidate_a": a.candidate_id,
                    "candidate_b": b.candidate_id,
                    "strategy_a": a.strategy,
                    "strategy_b": b.strategy,
                    "family_a": a.family,
                    "family_b": b.family,
                    "same_bar_overlap": int(same_bar_overlap[ci, cj]),
                    "same_day_overlap": int(same_day_overlap[ci, cj]),
                    "opposite_side_same_bar": int(opposite_side_same_bar[ci, cj]),
                    "same_direction_same_bar": int(same_direction_same_bar[ci, cj]),
                    "approx_abs_median_signal_minute_diff": approx_md,
                }
            )
    pd.DataFrame(pairs).to_csv(out_dir / "candidate_conflict_summary.csv", index=False)
    print(f"[diagnostics] done in {time.perf_counter() - t0:.2f}s", flush=True)
