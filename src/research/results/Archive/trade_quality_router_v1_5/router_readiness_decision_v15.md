# Router readiness — Trade Quality Router v1.5

**Decision (exactly one):** **`NEED_MORE_TRADE_ENRICHMENT`**

## Rationale (3–6 bullets)

- **Calendar holdout:** For VWAP baseline, **train-2023 / test-2024** with the **v1** offline score, **test top80% (train threshold)** has **lower total R** than **test all** (`vwap_quality_holdout_results.csv`). That fails the v1.5 bar for “meaningful calendar holdout” before any optional combiner score adjustment.
- **Offline score v1.5:** The v1.5 VWAP holdout slice (`vwap_threshold_holdout_v15.csv`) still shows **weaker test top80** vs test all on the 2023→2024 split; the revised rules do not rescue out-of-sample separation in this diagnostic.
- **`regime_unknown`:** Decomposition CSVs show **mid-morning concentration** (`m61_120` / `m121_240` buckets carry large shares of unknown PnL for VWAP baseline — see per-system `*_unknown_by_minute_bucket.csv`). That argues against treating unknown as “early open only”; more context or longer-window labels would reduce ambiguity before router penalties.
- **Indicator mtp=2/3:** **Trade #2 is materially positive** in-sample (~+28.6R over 498 trades at mtp≥2); **trade #3** at mtp=3 adds ~+7.35R over 241 trades with **lower avg R** than trade #1. Total R rises with mtp but **avg R and PF decay** — turnover/overtrading risk is unresolved for a router prototype.
- **Target-limit-aware slip:** Overlay shows **symmetric stress** is harsh on published R, while **target-limit-adjusted** scenarios recover a large fraction of edge for both VWAP and indicator (`exit_slip_scenario_comparison.csv`). This is **research-only**; until the simulator supports exit-type slip, Global L2 gates should not assume symmetric stress is the only realistic readout.
- **No combiner/strategy/feature changes** were required for this diagnostic pass; the blocker is **evidence strength**, not engineering.

## Exact next step

- **Enrich and score additional holdout-friendly slices** (e.g. walk-forward style train/test on scored rows, or more years if available locally) **or** tighten offline score features using **only** columns observable at entry — without changing live combiner behavior — until at least one **honest** calendar split shows stable VWAP score separation **and** indicator behavior is clearer at the intended production `max_trades_per_day`.

## Explicit non-runs

- mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; large Global L2 grids; `--use-signal-cache` on unsafe OneDrive roots; strategy plugin edits; feature primitive edits; selected candidate YAML edits; hard regime filters; online combiner `regime_router`; committing raw `trades.csv`, enriched/scored row CSVs, `local_runs/`, sweeps, `top_runs/`, logs, `.cache`, parquet/npy/npz/memmap.
