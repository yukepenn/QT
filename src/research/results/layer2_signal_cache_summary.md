# Layer 2 persistent candidate signal cache — summary

## 1. Purpose

Speed up repeated Layer 2 precompute (diagnostics, fixed runs, sweeps, postprocess cost stress) by persisting **per-candidate** fast-path signal arrays for a deterministic key: asset/symbol/window, **data fingerprint** (cheap bar digest), **code fingerprint** (git HEAD + dirty flag, or source hash fallback), strategy, candidate id, params hash, feature key, and strategy `context_key`. **Not** a FeatureStore; **not** committed to git.

## 2. Files changed

| Item | Path |
|------|------|
| New | `src/combiner/signal_cache.py` |
| Wired | `src/combiner/precompute.py`, `run.py`, `sweep.py`, `postprocess.py` (`cost_stress`) |
| Ignore | `.gitignore` — `.cache/`, `data/cache/`, `*.npy`, `*.npz`, `*.memmap`, `PROJECT_STRUCTURE_AND_SCRIPTS.txt` |
| Tests | `tests/test_combiner_signal_cache.py`, `tests/test_combiner_precompute_signal_cache.py` |
| Docs | `README.md`, `PROGRESS.md`, `CHANGES.md`, this file |

## 3. Cache key components

`SignalCacheKeyParts` → `build_signal_cache_key` (SHA-256 hex): `asset`, `symbol`, `start`, `end`, `data_fingerprint`, `strategy`, `candidate_id`, `params_hash`, `feature_key`, `strategy_context_key`, `code_fingerprint`.

## 4. Cache storage layout

Default root: `.cache/qt/candidate_signals` (override with `--signal-cache-root` or YAML `precompute.signal_cache_root`).

Per entry: `.cache/qt/candidate_signals/<key[:2]>/<key>/` — `side.npy`, `valid.npy`, `stop.npy`, `target_preview.npy`, `target_mode_code.npy`, `target_r.npy`, `risk_preview.npy`, `metadata.json`. Writes use a staging dir then rename.

**Invalidation:** change bars, dates, strategy/plugin code (fingerprints), candidate YAML, or feature/context-driving config → new key. Deleting `.cache/qt/...` is always safe.

## 5. CLI / YAML options

**CLI** (`run.py`, `sweep.py`, `postprocess.py` for cost stress):

- `--use-signal-cache`
- `--signal-cache-root <path>`
- `--refresh-signal-cache`

**YAML** (optional, under base combiner config):

```yaml
precompute:
  use_signal_cache: true
  signal_cache_root: ".cache/qt/candidate_signals"
  refresh_signal_cache: false
```

CLI `--use-signal-cache` / `--refresh-signal-cache` / `--signal-cache-root` override YAML when passed (same rules as `resolve_precompute_signal_cache_settings`).

Startup log: `[precompute-cache] use_signal_cache=... root=... refresh=...`

## 6. Cache-off vs cache-on behavior

- **Off:** Same as pre-cache behavior; profile columns `signal_cache_enabled=False`, `signal_cache_hit=False`.
- **On, cold:** Builds features/context/signals; writes disk cache; `signal_cache_hit=False`, `signal_cache_write_sec` populated.
- **On, warm:** Loads arrays when key matches; skips context + signal generation; may **bootstrap** features once per run if needed for shared `backtest_arrays` / `meta_arrays` (first row all cache hits). Profile: `signal_cache_hit=True`, `signal_cache_load_sec` populated.

In-memory **feature/context** caches remain; disk cache is an additional layer.

## 7. Tests

- `pytest -q` — includes `test_combiner_signal_cache.py` (key stability, save/load, incomplete cache, clear) and `test_combiner_precompute_signal_cache.py` (off vs cold vs warm matrix equality for `FAILED_ORB_001`, Jan 2025).

## 8. Smoke results (QQQ Jan 2025, `trap_family` top 1)

- **No cache / cold / warm:** `candidate_signal_summary.csv` **signals** per candidate identical (e.g. 15 / 4 / 3).
- **Warm:** console shows `signal_cache=hit` for all three candidates; precompute wall time lower than cold.

## 9. Equivalence (QQQ 2025-01-01 → 2026-04-30, `trap_family` top 1)

| Mode | trades | total_r | PF | max_drawdown_r |
|------|--------|---------|-----|----------------|
| No cache | 329 | 66.3293679139934 | 1.479397596602119 | -14.102637612790438 |
| Cache cold (`--refresh-signal-cache`) | 329 | 66.3293679139934 | 1.479397596602119 | -14.102637612790438 |
| Cache warm | 329 | 66.3293679139934 | 1.479397596602119 | -14.102637612790438 |

## 10. Cleanup note

Smoke folders under `src/combiner/results/_smoke_signal_cache_*` and `_equiv_signal_cache_*` are **not** committed. Local caches `.cache/qt/test_candidate_signals` and `.cache/qt/equiv_candidate_signals` used for validation only.

## 11. Next recommended phase

1. FeatureStore-style feature reuse (separate from signal arrays).
2. FeatureStore base + ORB overlay patterns.
3. Active/archive config and results layout.
4. Small Layer 3 smoke after the above.
