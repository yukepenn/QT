"""Layer 1 candidate YAMLs, selection rules, and metadata for Layer 2."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import yaml

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.strategies.loader import deep_update, load_strategy_config


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


_REEXPORT_PRECOMPUTE = frozenset({
    "CandidateSignalMatrix",
    "build_candidate_signal_arrays",
    "build_context_cache_key",
    "normalize_for_context_cache_key",
    "precompute_candidate_signal_matrices",
    "write_precompute_profile_summary",
})


def __getattr__(name: str) -> Any:
    """Lazy re-exports so `candidate` never imports `precompute` at import time (avoids cycles)."""
    if name in _REEXPORT_PRECOMPUTE:
        from src.combiner import precompute as _pre

        return getattr(_pre, name)
    if name == "write_candidate_diagnostics":
        from src.combiner import diagnostics as _diag

        return _diag.write_candidate_diagnostics
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
