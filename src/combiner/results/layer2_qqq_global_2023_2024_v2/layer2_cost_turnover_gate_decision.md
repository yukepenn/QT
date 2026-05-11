# Layer 2 cost / turnover gate decision (Global L2 v2 + tuned diagnostics)

**Date:** 2026-05-10  
**Window:** QQQ equity **2023-01-01 — 2024-12-31** (in-sample).  
**Candidate root:** l2_core **66** YAMLs (unchanged).

## Gates

| Gate | Preferred / strong | Observed (tuned sweeps + stress ladder) | Verdict |
|------|---------------------|-------------------------------------------|---------|
| **1 Cost robustness** | PF > 1.05 and total_r > 0 at **+0.02**; strong at **+0.03** | **+0.02:** original VWAP, lower-turnover VWAP, and **indicator_completion_core** (family / non-vwap tracks) remain **positive R** with PF > 1. **+0.03:** all top profiles still **negative total_r** (VWAP ~−20R; indicator ~−18R). | **Fail** strong 0.03; **partial** at 0.02 |
| **2 Behavior diversity** | ≥2 behavior-distinct systems not VWAP-knob variants | Lower-turnover track: **4** behavior-uniques (still VWAP-pair dominated). Family-diverse / non-vwap: **indicator** stack wins combiner rank — **multi-strategy**, but **not** a second independent economic story vs Global L1 library. | **Fail** preferred bar |
| **3 Turnover / edge** | Lower churn improves **R/trade** or **cost retention** vs original | **max_trades_per_day=1** VWAP: **294** trades, **total_r ~36.7** vs **337 / ~42.2** original; **avg R/trade** similar (~0.125 vs ~0.125). **R retention 0.01→0.02** ~0.32 for tuned VWAP vs ~0.25 original — modest, not a thick edge. Indicator track: **502** trades — **higher** churn than VWAP headline. | **Fail** preferred |
| **4 Drawdown** | Not materially worse than ~**−10.5R** | Lower-turnover VWAP: **maxDD ~−15.5R** (worse). Indicator: **~−11.8R** (similar to original multi-strategy). | **Fail** for VWAP tightening |
| **5 Monthly concentration** | No single month dominates | Not re-audited on tuned `top_runs` in this commit; original Global L2 caveat still applies. | **Open** |

## Final decision (exactly one)

**`TUNE_LAYER2_COST_TURNOVER_AGAIN`**

### Rationale

- **+0.03** slip remains **economically lethal** for headline profiles; **+0.02** is only a partial comfort.
- **Lower-turnover VWAP** cuts **total_r** and **worsens drawdown** without delivering clearly **cost-robust** or **behavior-diverse** systems.
- **Non-VWAP / family-diverse** grids surface **indicator_completion_core** at the top — **higher total_r** and slightly **better PF under 0.03** than VWAP, but still **negative R at 0.03**, **high trade count**, and **low production combiner_score** vs VWAP-centric grids.
- No evidence yet for **Layer 3 smoke**: cost and diversity gates are not cleared.

## Explicit non-runs

mini-WFO, full WFO, live/paper, SPY, new strategies/features, YAML parameter edits, committing `sweep_*` / `top_runs/` / heavy cost_stress artifacts.
