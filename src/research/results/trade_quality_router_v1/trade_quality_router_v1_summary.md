# Trade quality router v1 — summary

## 1. Purpose

Offline **trade-level regime/context enrichment**, **attribution**, **setup taxonomy**, and **prototype quality score** for existing Global L2 systems — **no** strategy or combiner logic changes.

## 2. Current Global L2 context

- Baseline VWAP pair: **~42.2R**, **337** trades @ 0.01 slip (`layer2_cost_turnover_tuned_comparison.csv`).
- Lower-turnover VWAP: **~36.7R**, **294** trades; deeper drawdown.
- Indicator five-pack @ **mtp=1**: **~43.5R**, **502** trades (matches tuned comparison row).

## 3. Systems selected

See `selected_systems_for_diagnostics.{md,csv}` — three systems only.

## 4. Trade file / manifest inventory

`manifest_inventory_phase0.md` + comparison CSV in `src/combiner/results/layer2_qqq_global_2023_2024_v2/`. Raw `trades.csv` regenerated **locally** only; **not committed**.

## 5. Feature and trade schema

`trade_output_and_feature_schema_inventory.md`.

## 6. Enrichment method and timestamp policy

`merge_asof` **backward** on `entry_ts_utc` vs feature `ts_utc`; `RegimeFeatureConfig.windows=(20,)` for generic regime metrics; PA regime labels use default `PaFeatureConfig.regime_windows` including **20**.

## 7. PnL by regime/context

Per-system CSV/MD under `analysis/<system>/entry_regime_label_summary.*`.

**Headline:** No single regime bucket owns all edge; **`late_trend_climax`** is frequent; **`trading_range`** and **`regime_unknown`** remain important **positive** contributors in these replays.

## 8. PnL by trade number / repeated family / prior outcome

- **VWAP baseline (mtp=2):** trade **#2** bucket **+5.5R** (43 trades) — not “toxic” in aggregate.
- **Indicator @ mtp=1:** only trade **#1** exists — **no** trade #2/#3 readout for this profile.
- **Same-family repeat / prior loss:** small second-trade cohorts — interpret cautiously (`prior_loss_bucket_summary.csv`).

## 9. Cost sensitivity (realistic model)

- Baseline **0.01**/share, stress **0.02**, extreme **0.03** — see Global L2 cost docs.
- Attribution uses a **symmetric marginal R proxy** per +0.01 slip/leg (`-0.02 / risk_per_share`) in `analyze_trade_quality.py`; **target** exits still use uniform slip in the engine — limitation called out in `trade_quality_analysis_summary.md`.

## 10. Setup taxonomy

`setup_taxonomy_v1.{csv,md}` — ≤10 `setup_type` values; maps VWAP, opening traps, indicator, PA.

## 11. Offline trade_quality_score

- **VWAP baseline:** **top 80%** by score → **higher** total R (~45.2 vs 42.2) and **shallower** max-DD proxy (`threshold_simulation_vwap_baseline_global_l2.csv`); **`score_ge_60`** retains only **49** trades — high cutoff is **brittle**.
- **Indicator:** higher score subsets **do not** beat “all trades”; deciles **collapsed** when scores tie.
- **Rules:** mix of **evidence tables** (regime summary) + **small hypothesis bonuses** — see `score_rules_resolved_*.json`.

## 12. Evidence for/against 2–3 vs 5+ trades/day

- **For mtp>1 (VWAP):** second trade bucket **positive** in aggregate — weak evidence that **mtp=2** is not inherently harmful for this pair **in-sample**.
- **For mtp 5+:** **no** direct evidence here; indicator replay at **mtp=1** was required to match economics — **do not** extrapolate to 5 without new runs.

## 13. Evidence for/against future regime router

- **Infrastructure:** `build_basic_features` already exposes enough **session-safe** columns for a **first prototype** (regime labels, ORB/VWAP distances, chop proxies).
- **Product readiness:** **insufficient** — indicator score fails; **`regime_unknown`** too large; need **more enrichment / decomposition** before optional **`regime_router`**.

## 14. Decision

**`NEED_MORE_TRADE_ENRICHMENT`** (see `regime_router_design_from_evidence_v1.md`).

## 15. Explicit non-runs

mini-WFO; full WFO; live/paper; SPY; Global L1 rerun; large L2 grids; strategy/feature primitive changes; candidate YAML edits; hard regime filter; combiner router implementation; committing `local_runs/`, raw `trades.csv`, enriched row-level CSVs, sweep/top_runs.

## 16. Recommended next step

**Exactly one:** expand trade enrichment (decompose `regime_unknown`, calendar holdout, optional **mtp=2** replay for indicator five-pack, refine exit/slip attribution assumptions) **before** implementing `regime_router`.

---

### Positioning questions (required)

| Question | Answer |
|----------|--------|
| Closer to static Layer 2 or human-like router? | Still **closer to static Layer 2**; router remains **research-only**. |
| Is `features/regime.py` + PA/VWAP/ORB sufficient for first prototype? | **Yes** for a **diagnostic** prototype; **not** sufficient alone for production routing without more validation. |
| Best router prototype candidate? | **VWAP pair** shows **more** score separation than indicator in this pass; indicator economics need **paired mtp** studies first. |
| Support `max_trades_per_day` 3 or 5? | **No** evidence yet; **mtp=2** VWAP second trade is **positive** in-sample only. |
| Implement optional router next? | **No** — **`NEED_MORE_TRADE_ENRICHMENT`**. |
