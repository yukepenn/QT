# Regime router design from evidence (v1 — design only)

**Status:** No combiner changes. No hard regime filter. This document proposes future module boundaries if diagnostics mature.

## 1. Why not a hard regime filter

Hard blocking throws away marginal edge and amplifies **regime misclassification** risk. The research direction is **trade-quality** and **score adjustment** with **default-off** behavior and explicit unknown-policy.

## 2. What current Layer 2 already does

`src/combiner/run.py` + `simulator.py`: single open position, priority/tie-breakers, `max_trades_per_day`, daily loss cap, cooldown — **static** rules, not PA/regime-aware beyond what strategies embed in signals.

## 3. What trade enrichment found (QQQ 2023–2024, in-sample)

- **VWAP pair (`vwap_core`, mtp=2):** PnL is **not** concentrated in a single `entry_regime_label`; `regime_unknown`, `late_trend_climax`, and `trading_range` all contribute meaningfully (`analysis/vwap_baseline_global_l2/entry_regime_label_summary.csv`). **Second trade of day** remains **net positive** in aggregate (`entry_trade_number_of_day_summary.csv`: bucket `2` → **+5.5R** over 43 trades).
- **Lower-turnover VWAP (mtp=1):** no second-trade bucket; regime mix shifts slightly toward `trading_range` in contribution ranking (`trade_quality_key_findings.csv`).
- **Indicator five-pack (`indicator_completion_core`, mtp=1):** same coarse regime columns; **`late_trend_climax`** dominates trade count (~64%) but is not the only contributor; `regime_unknown` has the **largest** share of total R in this replay.
- **Exit attribution (VWAP baseline):** almost all **losses** sit in **`stop`** exits; **`target`** exits carry most positive R (`exit_reason_summary.csv`) — cost sensitivity should not assume uniform adverse slip on targets (combiner still uses one slip constant; see limitations).
- **Offline `trade_quality_score`:** **VWAP** — top 80% by score improves **total R** and **max-DD proxy** vs all trades (`quality_score/threshold_simulation_vwap_baseline_global_l2.csv`). **Indicator** — rank-based subsets **do not** improve total R in this prototype (`threshold_simulation_indicator_completion_mtp1.csv`); deciles **degenerate** when scores tie (`pnl_by_quality_decile_*.csv`).

## 4. Which regime/setup combinations have evidence

| Context | Finding |
|---------|---------|
| `late_trend_climax` | Large **share of trades** for both VWAP and indicator; still **positive total R** in these replays — not a simple “avoid” bucket without further splitting. |
| `trading_range` | **Positive** total R in VWAP + indicator summaries — aligns with **hypothesis** affinity for mean-reversion / completion setups; sample overlap with other regimes. |
| `regime_unknown` | **High total R contribution** — likely **state bucket** / score tie mix; needs feature diagnostics before router penalties. |
| Second daily trade (VWAP, mtp=2) | **Positive** aggregate R — argues **against** treating trade #2 as toxic by default. |
| Prior loss → next trade | **Small N** on trade #2 cohort; mixed — do not hard-block. |

## 5. Bonus / penalty ideas (future, default off)

- **Hypothesis-only (low weight):** small affinity bonus when `trading_range` + VWAP family (documented in `score_trade_quality_offline.py`).
- **Evidence-derived (when N≥15 per bucket):** regime table from `entry_regime_label_summary.csv` feeding ± adjustments (already prototyped in `score_rules_resolved_*.json`).
- **Chop proxy:** high `entry_vwap_cross_count` penalty **only** if bucket attribution shows persistent negative expectancy (not proven globally in v1).

## 6. Genericity and default-disabled

- All routing lives behind **`regime_router.enabled: false`**.
- **Unknown policy:** `neutral` until calibrated.
- **No YAML signal edits** in v1; optional future metadata table in registry.

## 7. Proposed module boundaries (future)

| Module | Role |
|--------|------|
| `src/combiner/regime_router.py` | Optional score adjustment hooks (not implemented). |
| `src/combiner/trade_quality.py` | Shared helpers for trade-level context if ever moved online. |
| `src/research/enrich_combiner_trades.py` | Offline enrichment (current). |
| `src/research/analyze_trade_quality.py` | Offline attribution (current). |
| `src/research/score_trade_quality_offline.py` | Offline scoring experiments (current). |

## 8. Proposed config block (future)

```yaml
regime_router:
  enabled: false
  mode: score_adjustment
  unknown_policy: neutral
  use_trade_quality_score: true
  min_quality_to_trade: null
  score_adjustment:
    affinity_bonus: 5
    mismatch_penalty: 10
    strong_mismatch_penalty: 25
    same_family_repeat_penalty: 10
    prior_loss_same_family_penalty: 15
    high_chop_penalty: 10
```

## 9. Proposed sweep axes (later)

- `enabled`: false / true  
- `min_quality_to_trade`: null / 50 / 60  
- `max_trades_per_day`: 2 / 3 / 5  
- `same_family_repeat_penalty`: 0 / 10 / 20  
- `regime_affinity_bonus`: 0 / 5 / 10  

## 10. Strict non-goals

No hard block in v1; no new strategies; no short forcing; no live/paper; no Layer 3 until evidence improves; no committing raw sweep/trades.

---

## Decision label (exactly one)

### **NEED_MORE_TRADE_ENRICHMENT**

**Rationale (3–6 bullets):**

- Indicator stack: offline score **does not** separate good/bad trades under the current rule set; **VWAP** shows **some** rank separation but not enough to ship a router alone.
- **`regime_unknown`** is a large positive contributor — router penalties would be mis-calibrated until that bucket is explained / decomposed.
- **ExitReason × slippage** is still a single constant in the combiner; trade-quality conclusions about “cost-sensitive contexts” are **partial**.
- **mtp=1** indicator replay **cannot** answer trade #2/#3 for that system; need paired replays (mtp=2/3) **before** arguing `max_trades_per_day`.
- Keep building **enrichment + attribution** (optional calendar splits, stronger magnet semantics) before any online **`regime_router`**.
