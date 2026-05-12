# CHATGPT_REVIEW_BUNDLE — execution-backed hardening

## 1. Git / validation

- Branch: **`main`**
- **`python -m compileall -q src`:** OK
- **`python -m pytest -q`:** **149** passed
- **`python -m src.research.validate_research_artifacts --root .../execution_backed_hardening --csv-only`:** OK → **`execution_backed_hardening_artifact_validation.csv`** (**17** curated CSVs scanned)
- Loader / backtest smoke / validate-pipeline / combiner help / parity help / exit-overlay help: OK (see `baseline_validation.csv`)

## 2. Why hardening was needed

Before controlled Layer1/2/3 rebuild, execution-backed Layer2 needed **correct session entry**, **session-safe cooldown**, **shared min-risk enforcement**, and **correct scale-out sizing** so research does not inherit subtle lookahead / calendar bugs or duplicate risk rules outside `src/execution/`.

## 3. Session-boundary guard

`adapter.simulate_combiner_canonical` skips signals where `session_date[cursor+1] != session_date[cursor]`. See `session_boundary_guard.md`.

## 4. Cooldown session reset

`CombinerState.reset_day` clears **`cooldown_until_bar`** and **`open_positions`**. See `cooldown_session_reset.md`.

## 5. Min-risk execution policy

`ExecutionPolicy.min_risk_per_share` + **`materialize_trade_levels`** reject **`risk_too_small`**. Policy populated via **`execution_policy_from_combiner_cfg`** using **`max(cfg, per-candidate floor)`**. See `min_risk_policy.md`.

## 6. Scale-out fraction semantics

**Remaining-qty** semantics implemented in `_maybe_scale_out`. See `scaleout_fraction_semantics.md`.

## 7. Tiny smoke result

`run_combiner_adapter_parity --try-real-smoke --engine execution_backed` (Jan 2024 QQQ, PA+GAP) → **23** trades, **4.412R** total (see `smoke/hardening_smoke_summary.csv`).

## 8. Docs sync

`docs_sync_summary.md` / `.csv` lists touched docs + handoff files.

## 9. Fast-path / Numba plan

`fast_path_acceleration_plan.md` — **no Numba implementation** in this task.

## 10. Decision

**`DESIGN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`** — see `execution_backed_hardening_decision.md`.

## 11. Explicit non-runs

No WFO, broad sweeps, router, production exit-management, new strategies, legacy delete, second PnL engine, raw trade rows.

## 12. Recommended next step

**`DESIGN_CONTROLLED_LAYER1_EXECUTION_BACKED_REBUILD`**
