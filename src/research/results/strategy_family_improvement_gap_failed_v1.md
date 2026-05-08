# Strategy Family Improvement — Gap / Failed ORB v1

## 1. Why we are here

- mini-WFO v1 and v2A (QQQ; train 2023–2024, test 2025–2026) both ended **CAUTION**.
- mini-WFO v2B (train 2020–2024, test 2025–2026) ended **FAIL**.
- Full rolling WFO is **not justified** and remains **blocked**.

## 2. Current evidence

### 2.1 Mini-WFO comparison

See `src/walkforward/results/mini_wfo_comparison_v1_v2.md`.

- v1: selected `gap_only` (`MINIWFO_GAP_ACCEPTANCE_FAILURE_001`), test total_r ≈ 1.31, PF_R ≈ 1.03, **0.02 slippage negative**.
- v2A: broader family universe, but still selected `gap_only` and matched v1.
- v2B: selected `failed_gap` (failed_orb + gap_acceptance_failure), test total_r ≈ -5.92, PF_R ≈ 0.94, **fails cost stress**.

### 2.2 Dec 2025 loss cluster (test window)

Diagnostics are under `src/research/results/gap_failed_family_diagnostics_v1/`.

Key takeaways from `dec2025_loss_cluster_summary.md`:

- **v1 / v2A Dec-2025**: 8 trades each, total_r ≈ **-8.07** (PF_R 0.0). All losses are essentially stop-like \(~ -1R\) outcomes.
- **v2B Dec-2025**: 10 trades, total_r ≈ **-6.27** (PF_R ≈ 0.17).
- **Dominant driver**: `gap_acceptance_failure` contributes the majority of Dec-2025 loss R.
- **Exit reason**: overwhelmingly **stop**.
- **Timing**: losses are concentrated in **early entries** (dominant bucket **0–15 minutes** after the open, as computed from `entry_ts_utc`).

Interpretation: Dec-2025 weakness looks like a “small count of mostly ~-1R stops” regime, not a slow bleed. That is consistent with the family being **thin-edge and slippage-fragile**.

## 3. Gap family findings (gap_acceptance_failure)

From `gap_acceptance_diagnostic.csv` (train/test windows, grouped by exit_reason / entry_minute_bucket / risk_bucket):

- **Train (2023–2024)**:
  - targets are profitable; stops are large negative.
  - performance is sensitive to which trades avoid the stop bucket.
- **Test (2025–2026)**:
  - still has profitable targets, but the stop bucket dominates enough to make edge thin.
  - Dec-2025 is an extreme case where essentially everything goes to stop.

What we **cannot** see yet (missing columns):
- gap direction (up/down), gap size in ATR, acceptance vs failure mode, VWAP context at entry.

## 4. Failed ORB findings (failed_orb)

From `failed_orb_diagnostic.csv`:

- In v2B train, `failed_orb` can contribute positive R, but it also has a substantial stop bucket.
- In v2B test, `failed_orb` is not the primary Dec-2025 driver (gap is), but it does not “save” the combined system OOS.

Interpretation: `failed_orb` looks like it may be **regime-dependent** and/or needs **confirmation filters** to avoid stop-heavy conditions.

## 5. Candidate improvements (ranked)

### P1 (highest priority): narrow the gap family to reduce stop-heavy regimes

- **Split `gap_acceptance_failure` into explicit subtypes** (diagnostic axes first, then variants):
  - `gap_up_acceptance_long`
  - `gap_down_failure_long` (only if supported by evidence)
- **Add coarse filters that directly target the Dec-2025 failure signature**:
  - avoid early open entries (or require stronger confirmation for 0–15 minutes)
  - optional “do-not-trade” if risk-per-share is too small relative to costs (cost fragility)
- **Cost robustness**:
  - treat “survives 0.02 slippage” as a hard gate for family readiness
  - review whether `min_risk_per_share` should be higher for the gap family (parameter / config-level; not logic)

### P2: failed_orb confirmation and time-window tightening

- **VWAP-confirmed failed ORB** (or other lightweight confirmation that is non-lookahead).
- **Tighten windows** (fast vs late failed ORB variants).
- **Stop/target variants** focused on reducing ~-1R stop frequency (prefer fewer trades over marginal edge).

### P3: only after evidence

- prior_day trap integration only with clear filters.
- ORB continuation/retest only if a regime filter is evidenced (do not add random breadth).

## 6. What NOT to do yet

- Full rolling WFO.
- Live / paper trading.
- Broad new strategy explosion.
- SPY robustness research.
- More random Layer 2 variants without strategy-family improvements.

## 7. Next proposed implementation (keep it small)

Implement **1–2** refined variants only (then re-evaluate):

1. `gap_acceptance_refined_v1`:
   - add subtype labeling + diagnostic columns (direction, size bucket, mode) if possible without altering decisions
   - add one conservative filter targeting the stop-heavy early-open regime

2. `failed_orb_refined_v1`:
   - add confirmation option (VWAP context) and/or tighter time window

## 8. Next validation after implementation

- Layer 1 focused sweep on the refined variants (QQQ only).
- mini-WFO v3:
  - Train 2023–2024
  - Test 2025–2026
  - Require survival at 0.02 slippage to advance.
- Compare to v1/v2A/v2B (same table; same audit/oracle outputs).

