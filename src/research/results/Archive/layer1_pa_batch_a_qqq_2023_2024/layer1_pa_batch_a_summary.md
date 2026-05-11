# PA Batch A — formal Layer 1 summary (QQQ 2023–2024)

## 1. Purpose

Execute **formal Layer 1** for the four PA Batch A strategies after the shared `pa_*` feature foundation: sweeps → manifest → strict selection → signal-rate diagnosis → fast-context sanity. **No** Layer 2, mini-WFO, full WFO, or live/paper.

## 2. Window and data

| Item | Value |
|------|--------|
| Symbol | QQQ (equity) |
| Dates | 2023-01-01 → 2024-12-31 |
| Raw bars (approx.) | **194,880** rows (`read_bars`) |
| Distinct session days (from `ts_ny` date) | **502** |
| SPY | not used |

## 3. Strategies

| Strategy | Family | Focused YAML | Raw grid | Dedup rows | Capped |
|----------|--------|----------------|----------|------------|--------|
| pa_trading_range_bls_hs | pa_trading_range | `pa_trading_range_bls_hs_focused.yaml` | 108 | 18 | no (full) |
| pa_failed_range_breakout_trap | pa_range_breakout_failure | `pa_failed_range_breakout_trap_focused.yaml` | 108 | 18 | no |
| pa_tight_channel_pullback | pa_channel_pullback | `pa_tight_channel_pullback_focused.yaml` | 108 | 18 | no |
| pa_mtr_reversal | pa_major_trend_reversal | `pa_mtr_reversal_focused.yaml` | 108 | 18 | no |

`sweep.py` collapses **108** nominal combos to **18** unique parameter fingerprints per strategy (`combinations_skipped_duplicate=90`).

## 4. Sweep results

| strategy | status | result_rows | best_trades | best_total_r | best_PF | best_maxDD | notes |
|----------|--------|-------------|-------------|----------------|----------|------------|--------|
| pa_trading_range_bls_hs | ok | 18 | 409 | -6.93 | 1.095 | -37.84 | High trade count; best PF row still **negative R** vs strict `min_total_r=0`. |
| pa_failed_range_breakout_trap | ok | 18 | 331 | +2.84 | 1.135 | -47.19 | Strongest in-sample edge in this batch. |
| pa_tight_channel_pullback | ok | 18 | 14 | -3.04 | 0.943 | -5.87 | Low max trades / weak PF. |
| pa_mtr_reversal | ok | 18 | 1 | +1.98 | inf* | 0.0 | *Single-trade combo ⇒ `profit_factor=inf` in CSV; treat as **not** PF-stable. |

## 5. Signal / trade-rate diagnosis

- **Viable rate (high counts):** `pa_trading_range_bls_hs`, `pa_failed_range_breakout_trap` (see `signal_rate_diagnosis.md`).
- **Sparse:** `pa_tight_channel_pullback` (max **14** trades / combo on dedup grid).
- **Ultra-sparse:** `pa_mtr_reversal` (max **1** trade / combo).
- **Jan 2025 zero-trade warning:** **Resolved** for `pa_tight_channel_pullback` on 2023–2024 (non-zero fills exist). **`pa_mtr_reversal`** remains **structurally sparse** (not a parity failure).

## 6. Candidate selection

### Strict (primary)

See `candidate_selection_config.md`. **4** YAMLs, **all** `pa_failed_range_breakout_trap` (`PA_FAILED_RANGE_BREAKOUT_TRAP_001` … `_004` in `selected_candidates/`).

**No strict candidates:** `pa_trading_range_bls_hs` (fails `min_total_r`), `pa_tight_channel_pullback`, `pa_mtr_reversal` — listed in `no_candidate_strategies.txt`.

### Diagnostic relaxed

`diagnostic_relaxed_selection/` — **still only** `pa_failed_range_breakout_trap` passes; labeled **non-authoritative** in that folder’s `candidate_summary.md` and `summary.txt`.

## 7. Candidate sanity

- **Fast-context:** `candidate_fast_context_check.{csv,md}` — **ok** for all four strict YAMLs (Jan 2023 spot window).
- **No LOOKAHEAD in `required_features`:** unchanged from PA foundation (`preflight_check.md` / feature tests).

## 8. Interpretation (per-strategy classification)

| Strategy | Class |
|----------|--------|
| pa_trading_range_bls_hs | **SIGNAL_RATE_OK_BUT_WEAK_EDGE** (lots of trades; negative best total R under chosen grid slice). |
| pa_failed_range_breakout_trap | **PROMISING_LAYER1_CANDIDATE** (only strict exporter; PF>1.05 and total R>0 on top rows). |
| pa_tight_channel_pullback | **TOO_SPARSE_NEEDS_GRID_TUNE** |
| pa_mtr_reversal | **TOO_SPARSE_NEEDS_GRID_TUNE** (max 1 trade / combo here; tune before portfolio use). |

## 9. Decision (exactly one)

### **TUNE_PA_BATCH_A_GRIDS_FIRST**

**Rationale:**

- Strict candidates exist but **only one PA family** (`pa_range_breakout_failure`); Layer 2-style diversification is **not** supported yet.
- `pa_trading_range_bls_hs` shows **signal** but fails **`min_total_r >= 0`** on the best PF row — loosen R gate or grid/thresholds for range logic, or accept negative-R research-only configs explicitly.
- `pa_tight_channel_pullback` and `pa_mtr_reversal` need **grid / gate** relief (not implementation fixes): parity and fast-context are clean.

**Not** `PROCEED_TO_PA_BATCH_A_REDUCED_LAYER2_DESIGN` (multi-family / strength bar not met).  
**Not** `FIX_PA_BATCH_A_IMPLEMENTATION_FIRST` (no framework breakage; sweeps and parity healthy).  
**Not** `DEFER_PA_BRANCH` (failed-trap branch shows usable in-sample edge).

## 10. Explicit non-runs

- PA **Layer 2** not run.
- **mini-WFO**, **full WFO**, **live/paper** not run.

## 11. Artifacts

Curated root: `src/research/results/layer1_pa_batch_a_qqq_2023_2024/`  
Heavy sweep folders under `src/strategies/testing_parameters_results/**` are **not** committed.
