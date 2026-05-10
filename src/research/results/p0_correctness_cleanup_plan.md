# P0 correctness cleanup — initial plan

## Scope overview

This phase improves **format/maintainability**, fixes **P0 correctness** (session boundaries, sweep dedupe keys, combiner validation parity, structural target semantics documentation), and adds **PA diagnostics** (gate counts, exit summaries) **without** running Layer 1/2/WFO or changing strategy counts.

## A. Formatting scope

- **Root/docs:** `.gitignore` (section headers only; preserve ignore rules), `README.md`, `PROJECT_STATUS.md` (light readability pass where needed).
- **Core Python:** `loader.py`, `base.py`, `build_features.py`, `feature_key.py`, `feature_config.py`, `build_types.py`, `price_action.py`, `pa_swings.py`, `regime.py`, `levels.py`, `execution.py`, `fast.py`, `sweep.py`, `simulator.py`, `mini_wfo.py`, `select_candidates.py`.
- **PA strategies:** all `src/strategies/strategy/pa_*.py`.
- **Tooling:** `black` for Python where applicable; **no logic edits** in the format commit.

## B. Correctness fixes

1. **`pa_swings.py`:** Replace cross-session `shift(1)` leakage with **session-scoped** `groupby("session_date").shift(1)` for prior-bar state vs range highs/lows and related PA swing flags.
2. **`normalized_param_key`:** Audit all ten PA strategies; ensure every config field that affects **final signal arrays** (including stops/targets/thinning) is keyed; document in `pa_normalized_param_key_audit.md`.
3. **`combiner/simulator.py`:** Route detailed-path trade validation through `validate_trade_setup` from `backtest/execution.py` for parity with fast path.
4. **Structural targets:** Prefer **Option A** (document + tests locking current R-equivalent behavior) unless tests prove engine-ready **Option B** (`*_fixed_px` modes without changing legacy modes).

## C. PA target semantics decision

- **Default:** Option A — document “structural → fixed-R equivalent at signal bar” where applicable; add explicit tests.
- **Optional:** Add `*_fixed_px` modes only if `TM_FIXED_PX` wiring is clean and legacy YAML unchanged.

## D. Diagnostics scripts

- `src/research/pa_gate_diagnostics.py` — gate pass counts per PA strategy/config/window.
- `src/research/pa_exit_diagnostics.py` — exit reason / hold / R / cost summaries from compact outputs (no committed `trades.csv`).

## E. Explicit non-runs

- No Layer 1 sweeps or tuning reruns.
- No Layer 2 combiner runs.
- No mini-WFO / full WFO.
- No live/paper.
- No new strategies; no global shorts; no trailing stops.

## F. Artifact policy

- Commit: source, tests, curated diagnostic **CSV/MD** under `src/research/results/`, docs/index updates.
- Do **not** commit: `testing_parameters_results/**`, `top_runs/`, `run_*`, `sweep_*`, `fixed_runs/`, `trades.csv`, `equity.csv`, signal logs, caches, raw data, numpy/memmap/parquet blobs.

## G. Commits (three-way split)

1. **Format-only:** `Format core research modules for maintainability`
2. **Correctness:** pa_swings + normalized_param_key + combiner validation + structural target tests/docs
3. **Diagnostics + documentation:** gate/exit scripts, curated outputs, `RESULTS_INDEX`, `GRID_INDEX`, `ARTIFACT_POLICY`, summary MD

---

_Baseline Phase 0 (2026-05-10): pytest 242 passed, compileall OK, loader lists 35 strategies, parity checks OK, boundary greps OK, no `.py` under combiner/research/walkforward results roots, no tracked heavy artifact paths._
