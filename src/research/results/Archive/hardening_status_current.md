# Research platform hardening — current status

*Snapshot: 2026-05-05. **Authoritative HEAD:** run `git rev-parse HEAD` on `main`. Commit E landed as a small doc series ending with hash-pointer sync commits after `a37cca4` (main closeout bundle).*

## 1. Git

| Item | Value |
|------|--------|
| Branch | `main` (typical) |
| Remote | `origin` → `https://github.com/yukepenn/QT.git` |
| Latest commits (see `git log --oneline -15`) | A `6bc1c7c` · B `a049a11` · C `a1b995f` · D `75bb620` · **E** (docs) from `a37cca4` onward |
| Working tree | Should be **clean** after Commit E push (`git status --short` empty) |

## 2. Data status

- **QQQ (RTH 1-min):** Full window **2020-01-01 → 2026-04-30** is present locally for research. Representative full-window stats from archived Layer 1 summary: **~617,160** rows, **~1,588** sessions (unique NY dates), **0** duplicates dropped by `read_bars` (see `layer1_2020_summary.md`).
- **SPY:** Incomplete on typical disks — **do not use for robustness** until backfill matches QQQ coverage.
- **Raw data policy:** `data/raw/` is **gitignored**; never commit raw parquet; do not mutate raw pulls for research hygiene fixes.

## 3. Commit A (execution / combiner correctness)

- Equity / R drawdown measured from **zero** baseline (pandas + fast paths).
- **Stop-side** and **target-side** validation; finite price checks before risk sizing.
- Combiner **cooldown** resets at session boundary.
- Fast combiner emits **`daily_trade_number`**.
- **`max_open_positions != 1`** rejected (MVP).
- **Opposite-direction conflict** distinct from lower-priority rejection reason.

## 4. Commit B (features / cache)

- Full-session aggregates explicitly named **`full_session_*_LOOKAHEAD`**.
- Intraday-safe **`intraday_high_so_far`** / **`intraday_low_so_far`**.
- ORB **`*_known`** columns for gating.
- **`anchor_known`** helper where applicable.
- Centralized **`FeatureBuildConfig`** / **`feature_key`** across engine, sweep, combiner, research.
- Strategies must not list LOOKAHEAD columns in **`required_features`** (enforced in `BaseStrategy`).

## 5. Commit C (validation / cache keys)

- Optional **`BaseStrategy.validate_config`**; shared **`src/utils/config_validation.py`**.
- Validation wired into readable engine, Layer 1 sweep, combiner run/sweep/precompute, parity, `run_layer1_focused`.
- **`context_key`** / **`normalized_param_key`** audited; unsupported axes rejected.
- Long-only / single-level MVPs explicit in validation.

## 6. Commit D (combiner diagnostics)

- **`src/combiner/behavior.py`**: stable trade-sequence hash; **`behavior_unique_*`** postprocess outputs.
- **Cost-as-R** and **`profit_factor_r`** in `summarize_trades` / combiner metrics.
- **`daily_trade_number`** JSON profiles; **monthly/quarterly** `period_breakdown`.
- Postprocess **rank leaderboards**, **cost-robust** filter (research-only), optional **fixed vs sweep** comparison.
- Tests: `test_combiner_behavior`, `test_cost_as_r_metrics`, `test_daily_metrics`, `test_combiner_postprocess`.

## 7. Current caveats

- **Layer 1 / Layer 2 artifacts under pre-hardening roots are stale** for ranking (see `PRE_HARDENING_STALE.md` markers).
- **SPY** incomplete; **Layer 3** not built.
- **Cost-robust** thresholds are research filters, not live-trading approval.
- **Conservative gap-through stop fill** is not a documented guarantee in this repo; treat stop fills as implementation-defined unless explicitly specified elsewhere.
- **Behavior hash** quality depends on detailed **`trades.csv`** columns (`candidate_id`, entry/exit idx or timestamps).

## 8. Next step

1. User approval for **post-hardening rerun** (Layer 1 all-10 QQQ 2020–2026 → candidate selection → Layer 2 strict/relaxed → postprocess). See **`rerun_plan_after_hardening.md`**.
2. Only after fresh results: compare pre/post and decide if a **Layer 3 MVP** is warranted.
