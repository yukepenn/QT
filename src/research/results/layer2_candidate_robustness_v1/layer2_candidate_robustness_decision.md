# Layer2 candidate robustness — decision (v1)

## Decision label (exactly one)

**`RUN_MORE_CANDIDATE_OOW_AUDIT`**

## Rationale (3–6 bullets)

- This pack audited **27 / 66** l2_core YAMLs (**vwap** + **indicator** only); **39** YAMLs in **opening_trap**, **pa**, **afternoon**, and **other** groups were **not** replayed here.
- Among audited names, only **2** met **`ROBUST_POSITIVE`** (both **`cci_extreme_snapback`**), far below any reasonable multi-family dry-run threshold.
- **VWAP** singletons are **unanimously** non-robust-positive under the heuristic; fixed-profile VWAP OOW failure aligns with **per-candidate** weakness, not only combination weighting.
- **Side-flip:** only a **non-executable sign proxy** on fixed-profile aggregates was produced; it does **not** justify contrarian production shorts or `INVESTIGATE_SIDE_FLIP_SHORT_RESEARCH` as a primary branch.
- Policy **`REVISIT_LAYER1_SELECTION_CRITERIA`** is **deferred** until the **extended** audit still shows pervasive failure; current evidence is **partial** by construction.

## Recommended next step (exactly one)

Run **`opening_trap` + `pa` + `afternoon` + `other`** singleton audits on the same three windows, then refresh CSV/MD aggregates (still **no** parameter tuning on OOW).

## Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; broad Global L2 grid; new strategies; new feature primitives; edits to selected candidate YAMLs; combiner `regime_router`; hard regime filters; production short routing; OOW parameter optimization; `--use-signal-cache` on unsafe OneDrive roots; committing `local_runs/` or raw `trades.csv` / heavy artifacts; `git add .`
