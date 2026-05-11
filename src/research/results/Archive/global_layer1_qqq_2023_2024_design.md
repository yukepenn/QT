# Global Layer 1 design — QQQ 2023–2024 (v1)

## Scope

| Item | Choice |
|------|--------|
| Symbol | **QQQ** only (no SPY) |
| Window | **2023-01-01** → **2024-12-31** |
| Purpose | Build a **global candidate library** across all strategies marked runnable in `global_strategy_audit_v1` |
| Core | **Strict** selection only; diagnostic relaxed grids are **out of scope** for the authoritative core |

## Strategy inputs

- **Source of truth:** `src/research/results/global_strategy_audit_v1/strategy_eligibility_matrix.csv`
- **Runner:** `python src/research/run_global_layer1.py` reads `recommended_testing_yaml` per row.
- **YAML policy:** use audit’s pick — **latest tuned** `*_tuned_vN.yaml` when present, else **focused**, else default only when validated and grid is acceptable.
- **Sides:** long / short / both only where the audit’s `short_support_label` and YAML axes already support it. **No** synthetic shorts on long-only systems.

## Grid policy

- **Full grid** when `raw_grid_size <= 1500`.
- If `raw_grid_size > 1500`: strategy is **skipped** with `REVIEW_GRID_TOO_LARGE` in audit; runner also enforces `--max-grid-size` (default **1500**) and records skip reason — **no silent capping** on the first global pass.
- Strategies excluded from READY statuses in the audit are not run.

## Strict selection (Layer 1 library)

Applied via `select_candidates.py` after sweeps:

| Filter | Value |
|--------|--------|
| min_trades | 30 |
| min_profit_factor | 1.05 |
| min_total_r | 0 |
| max_drawdown_r | -60 |
| max_avg_bars_held | 150 |
| max_eod_count | 0 |
| max_end_of_data_count | 0 |
| top_per_strategy | 5 |
| sort | `candidate_score` |

## Diversity and QA

- After selection: `candidate_signal_diversity.py` on `selected_candidates/` → `global_candidate_signal_diversity_qqq_2023_2024_v1/`.
- If duplicate pure-signal groups dominate, document and optionally maintain **`selected_candidates_diverse`** in a follow-up — **do not** silently replace the strict set without documentation.
- Fast-context smoke: `check_selected_candidates_fast_context.py` on Jan 2023 slice.

## Explicit non-runs

- No Global Layer 2 until Layer 1 outputs pass conditional gates.
- No mini-WFO, full WFO, or live/paper in this phase.

## Re-run full universe

The audit lists **30** strategies with READY status and `raw_grid_size <= 1500`. To sweep all of them:

```bash
python src/research/run_global_layer1.py \
  --asset equity \
  --symbol QQQ \
  --start 2023-01-01 \
  --end 2024-12-31 \
  --audit src/research/results/global_strategy_audit_v1/strategy_eligibility_matrix.csv \
  --output-root src/research/results/layer1_global_qqq_2023_2024_v1 \
  --tag layer1_global_qqq_2023_2024_v1 \
  --max-grid-size 1500 \
  --select-candidates
```

Omit `--strategy-limit` for the full set. Use `--strategy-limit N` only for smoke or disk/time-budgeted partial runs (document partiality in `layer1_global_summary.md` / `NEXT_HANDOFF.md`).
