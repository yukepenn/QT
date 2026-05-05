# Post-hardening rerun plan (not executed)

**Do not run these commands until explicitly approved.** This document is a checklist only. Commit E does **not** create the new YAML configs listed below unless you add them in a later change; copy from existing `layer2_qqq_2020_20260430_v2_relaxed` / strict templates when implementing the rerun.

## 1. Purpose

Regenerate **trustworthy** Layer 1 and Layer 2 research artifacts after **Commits A–D**, using **new output roots** so pre-hardening folders stay historical.

## 2. Preconditions

- **QQQ** Parquet covers **2020-01-01 → 2026-04-30** RTH (verify with `read_bars` / coverage tools).
- **SPY** not used for this rerun.
- `git status` **clean**; **`python -m pytest -q`** passes.
- Pre-hardening roots have **`PRE_HARDENING_STALE.md`**; treat old rankings as **non-authoritative**.

## 3. New result roots (do not overwrite old)

| Artifact | New path |
|----------|----------|
| Layer 1 bundle | `src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/` |
| Layer 1 tag | `layer1_qqq_2020_20260430_posthardening_v1` |
| Layer 2 strict | `src/combiner/results/layer2_qqq_2020_20260430_posthardening_strict_v1/` |
| Layer 2 relaxed | `src/combiner/results/layer2_qqq_2020_20260430_posthardening_relaxed_v1/` |
| New strict configs (to be authored) | `src/combiner/configs/layer2_qqq_2020_20260430_posthardening_strict.yaml`, `layer2_sweep_qqq_2020_20260430_posthardening_strict.yaml` |
| New relaxed configs (to be authored) | `src/combiner/configs/layer2_qqq_2020_20260430_posthardening_relaxed.yaml`, `layer2_sweep_qqq_2020_20260430_posthardening_relaxed.yaml` |

## 4. Step 1 — Layer 1 all-10 sweep

```bash
python src/research/run_layer1_focused.py ^
  --asset equity ^
  --symbols QQQ ^
  --start 2020-01-01 ^
  --end 2026-04-30 ^
  --strategies all ^
  --tag layer1_qqq_2020_20260430_posthardening_v1 ^
  --output-root src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1 ^
  --top 100 ^
  --min-trades 80 ^
  --progress-every 100 ^
  --resume
```

*(On Unix shells, replace `^` with `\`.)*  
Note: `--resume` is a **boolean flag** (no numeric argument).

## 5. Step 2 — Candidate selection

Use **`src/research/select_candidates.py`**. Inspect current flags with:

```bash
python src/research/select_candidates.py --help
```

**Strict manifest pass (example thresholds — adjust after inspecting manifest columns):**

```bash
python src/research/select_candidates.py ^
  --manifest src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/sweep_manifest.csv ^
  --output-root src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1 ^
  --top-per-strategy 5 ^
  --min-trades 150 ^
  --min-profit-factor 1.05 ^
  --min-total-r 0 ^
  --max-drawdown-r -80 ^
  --max-avg-bars-held 90 ^
  --max-eod-count 0 ^
  --max-end-of-data-count 0 ^
  --allow-relaxed-fallback ^
  --relaxed-min-trades 80 ^
  --relaxed-min-profit-factor 1.0 ^
  --relaxed-min-total-r -10 ^
  --relaxed-max-drawdown-r -100
```

Relaxed rows should be **tagged** in selector output as relaxed when fallback applies (see script output / `candidate_summary.md`).

## 6. Step 3 — Layer 2 strict (config design)

Before running, **author** strict YAML + sweep YAML under **§3** paths. Intended knobs:

- `include_warnings`: **false**
- Candidate sets: e.g. `trap_family`, `opening_family`, `core5_no_vwap`, `strict_core`, `all_strict` (must match `candidate_sets` you define)
- Grid: `max_trades_per_day` ∈ `[1, 2, 3, 5]`; `daily_max_loss_r` ∈ `[-1.5, -2.0, -3.0]`; `cooldown_after_loss_minutes` ∈ `[0, 15, 30]`; `priority_policy` ∈ `metadata_priority`, `score_adjusted_priority`
- Execution: `slippage_per_share: 0.01`, `min_risk_per_share: 0.03` (or as in your template), `max_open_positions: 1`

## 7. Step 4 — Layer 2 relaxed (config design)

- `include_warnings`: **true**
- Candidate sets: e.g. `vwap_control_family`, `all_with_relaxed`, plus strict sets if desired
- Broader grid: `max_trades_per_day` add **10**; `daily_max_loss_r` add **-5.0**; same cooldown/priority ideas as v2 relaxed unless you tighten

## 8. Step 5 — Diagnostics and fixed runs

```bash
python src/combiner/run.py --candidate-root src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/selected_candidates --config src/combiner/configs/layer2_qqq_2020_20260430_posthardening_relaxed.yaml --asset equity --symbol QQQ --start 2020-01-01 --end 2026-04-30 --diagnostics-only --candidate-set trap_family --top-per-strategy 1 --output-root src/combiner/results/layer2_qqq_2020_20260430_posthardening_relaxed_v1
```

Fixed `run.py` examples (repeat with different `--candidate-set` / `--top-per-strategy`):

- `trap_family` top 1 and top 5  
- `opening_family` top 5  
- `core5_no_vwap` top 5  
- `strict_core` top 5  
- `all_strict` top 5  
- `all_with_relaxed` top 5 (relaxed config)

Use `--detailed` where you need logs; set `--output-root` under the new strict or relaxed results root.

## 9. Step 6 — Full Layer 2 sweeps

**Strict** (after configs exist):

```bash
python src/combiner/sweep.py ^
  --candidate-root src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/selected_candidates ^
  --config src/combiner/configs/layer2_sweep_qqq_2020_20260430_posthardening_strict.yaml ^
  --asset equity --symbol QQQ --start 2020-01-01 --end 2026-04-30 ^
  --output-root src/combiner/results/layer2_qqq_2020_20260430_posthardening_strict_v1 ^
  --top 50 --detail-top 20 --progress-every 50 ^
  --tag sweep_posthardening_strict_v1
```

**Relaxed:**

```bash
python src/combiner/sweep.py ^
  --candidate-root src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/selected_candidates ^
  --config src/combiner/configs/layer2_sweep_qqq_2020_20260430_posthardening_relaxed.yaml ^
  --asset equity --symbol QQQ --start 2020-01-01 --end 2026-04-30 ^
  --output-root src/combiner/results/layer2_qqq_2020_20260430_posthardening_relaxed_v1 ^
  --top 50 --detail-top 20 --progress-every 50 ^
  --tag sweep_posthardening_relaxed_v1
```

Adjust `--top` / `--detail-top` / dates to match machine time and disk budget.

## 10. Step 7 — Postprocess

Example (replace `SWEEP_DIR` with actual `sweep_*` folder under the new results root):

```bash
python src/combiner/postprocess.py ^
  --sweep-dir SWEEP_DIR ^
  --output-root src/combiner/results/layer2_qqq_2020_20260430_posthardening_relaxed_v1 ^
  --dedupe-top 100 ^
  --cost-stress-top 10 ^
  --write-behavior-unique ^
  --behavior-dedupe-top 100 ^
  --write-period-breakdowns ^
  --candidate-root src/research/results/layer1_all10_qqq_2020_20260430_posthardening_v1/selected_candidates ^
  --config src/combiner/configs/layer2_qqq_2020_20260430_posthardening_relaxed.yaml ^
  --asset equity --symbol QQQ --start 2020-01-01 --end 2026-04-30 ^
  --cost-robust-min-trades 300 ^
  --cost-robust-slip 0.02 ^
  --cost-robust-min-total-r 0 ^
  --cost-robust-min-pf 1.0 ^
  --cost-robust-max-dd-r -100 ^
  --cost-robust-max-median-cost-r 0.50
```

Add `--compare-fixed-runs path\to\fixed_run_summary.csv` if you collected fixed runs under the same root.

## 11. Step 8 — Compare pre vs post

After rerun, author **`posthardening_vs_prehardening_comparison.md`** (or similar) using **measured** outputs:

- Selected candidate counts / IDs  
- Best **behavior-unique** systems vs old `top_unique`  
- **Cost-robust** sets at 0.02 slippage  
- **total_r**, **profit_factor**, **profit_factor_r**, **max_drawdown_r**, **median_cost_r**  
- Strategy/family frequency in winners  

**Do not invent numbers** in that doc.

## 12. Step 9 — Decision gate before Layer 3

Consider Layer 3 **smoke** only if post-hardening outputs show at least one **behavior-unique** system that roughly satisfies (tune as a team):

- `total_r > 0` at **0.02** slippage in cost stress  
- `profit_factor_r > 1.0` (or consistent with your bar count)  
- `max_drawdown_r` not catastrophic **for your risk budget**  
- `median_cost_r` in a sane band  
- No obvious **single-regime** dependency in period breakdowns  

If nothing passes, improve **strategy library / features**, not Layer 3 scaffolding.

## 13. Step 10 — Layer 3 smoke (later only)

Only after successful rerun and gate:

- **2–3 folds**, **train ~36 months**, **test ~3 months**, step **3 months**  
- **Reduced** Layer 2 grid  
- **QQQ only**  
- Still **not** live-ready  

---

**Reminder:** None of the commands in this file were executed as part of Commit E.
