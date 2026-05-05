# Research platform hardening — closeout report (2026-05-05)

## 1. Executive summary

- **Commits A–D** (execution, features/cache, validation, combiner diagnostics) are **implemented, tested, and pushed** on `main`.
- The repository is **ready for a deliberate post-hardening rerun** of Layer 1 and Layer 2 (see `rerun_plan_after_hardening.md`). **Layer 3 is not started** and remains out of scope until rerun outputs exist.
- **No live trading** claims; all results remain **research-only**.

## 2. Why hardening was necessary

Pre-hardening saved CSVs and candidate libraries could reflect:

- **Drawdown** computed from a non-zero baseline (fixed in A).
- **Execution** paths without consistent stop/target/finite-price checks (A).
- **Features** that mixed full-session lookahead aggregates with signal logic without explicit naming or ORB gating (B).
- **Stale or wrong context caches** if `context_key` / `normalized_param_key` omitted parameters (C).
- **Config-only dedupe** without trade-sequence or cost-aware metrics (D).

Therefore **old Layer 1 / Layer 2 roots are marked stale**; see `PRE_HARDENING_STALE.md` in those directories.

## 3. Commit A — changes and tests

- Drawdown from **zero**; execution validation; combiner cooldown/session fixes; **`daily_trade_number`**; rejection reason hygiene.
- Tests: execution / drawdown / combiner (see `tests/` — e.g. execution and drawdown modules from hardening phase).

## 4. Commit B — changes and tests

- **`full_session_*_LOOKAHEAD`**, intraday so-far columns, ORB **`*_known`**, centralized **`feature_key`** / **`FeatureBuildConfig`**.
- Tests: `test_feature_no_lookahead.py`, `test_feature_key.py`.

## 5. Commit C — changes and tests

- **`validate_config`**, **`src/utils/config_validation.py`**, wiring across engine/sweep/combiner/research; context key audit; fake axes removed.
- Tests: `test_strategy_config_validation.py`, `test_strategy_context_keys.py`.

## 6. Commit D — changes and tests

- **`behavior.py`**, behavior-unique postprocess, cost-as-R, **`profit_factor_r`**, daily/period breakdowns, leaderboards.
- Tests: `test_combiner_behavior.py`, `test_cost_as_r_metrics.py`, `test_daily_metrics.py`, `test_combiner_postprocess.py`.

## 7. Validation (Commit E)

See **`hardening_validation_20260505.md`**: pytest **64** passed, compileall, loader, read_bars, build_features, parity, combiner smoke, boundary greps.

## 8. Stale artifacts (retained, not deleted)

| Root | Why stale |
|------|-----------|
| `src/research/results/layer1_all10_qqq_2020_20260430_v1/` | Layer 1 sweeps + selection **before** A–D fully on `main` |
| `src/combiner/results/layer2_qqq_2020_20260430_v2_relaxed/` | Layer 2 v2 relaxed **before** trustworthy post-hardening Layer 1 + metrics/dedupe stack |

Historical reference only; **`PRE_HARDENING_STALE.md`** in each root.

## 9. Data caveats

- **QQQ** 2020–2026 RTH window is the **primary complete** research symbol on a typical full backfill.
- **SPY** remains **incomplete** on many setups — **not** used for robustness until parity with QQQ coverage.

## 10. Remaining technical caveats

- **Gap-through stop** behavior: treat as **implementation-defined** unless explicitly documented; conservative gap modeling is a **future** enhancement if not already specified in engine docs.
- **Behavior hash** strength requires **detailed trade columns**; weak hashes are flagged in postprocess markdown.
- **Cost-robust filters** are **research screens**, not approval for live trading.

## 11. Recommended next step

1. Obtain explicit **user approval** to run **`rerun_plan_after_hardening.md`** (Layer 1 post-hardening root → `select_candidates` strict/relaxed → new Layer 2 strict/relaxed configs and sweeps → postprocess with behavior + cost flags).
2. Author **`posthardening_vs_prehardening_comparison.md`** from **actual** new outputs (no fabricated numbers).
3. **Only then** decide whether a **Layer 3 MVP** (simple walk-forward smoke) is justified.

## 12. Explicit non-goals

- No **live trading** productization in this phase.
- No **Layer 3** build in Commit E.
- No **new strategies** or signal-logic expansion tied to this closeout.
- No **SPY robustness** claims until SPY data is complete.
