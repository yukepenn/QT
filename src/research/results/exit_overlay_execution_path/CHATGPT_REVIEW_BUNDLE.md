# CHATGPT_REVIEW_BUNDLE — exit overlay on execution path

Readable on GitHub **raw** without opening large CSVs. Curated root: `src/research/results/exit_overlay_execution_path/`.

---

## 1. Git / validation

- **Branch:** `main` (synced with `origin/main` at task start, tip `25a38bb`).
- **`python -m compileall -q src`:** OK.
- **`python -m pytest -q`:** **142** passed (includes `tests/test_exit_overlay_execution_path.py`).
- **`python -m src.strategies.loader --list`:** OK.
- **`python -m src.backtest.sweep --smoke`:** OK.
- **`python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend`:** OK.
- **`python -m src.combiner.run --help` / `src.combiner.sweep --help`:** OK.
- **`python -m src.research.run_combiner_adapter_parity --help`:** OK.
- **`python -m src.research.run_exit_overlay_execution_path --help`:** OK.
- **`validate_research_artifacts --csv-only`:** `exit_overlay_execution_path_artifact_validation.csv` (no absolute-path hits in CSV heads).

---

## 2. Why this task was needed

`EXECUTION_BACKED_READY_FOR_RESEARCH` was established, but **management-style exits** had not been evaluated on the **same accounting spine** as Layer2. This diagnostic answers whether simple overlays can be tested **without** a third PnL engine.

---

## 3. Architecture rule: execution is the only PnL truth

All overlays call **`src.execution.path.simulate_trade_path`**. Baseline trade selection uses **`simulate_combiner_canonical`** (execution-backed). No standalone fill/PnL helpers were added in `src/research/`.

---

## 4. Inputs: repo-local data and candidate root

- **Bars:** `data/raw/ibkr` (via `--bar-root data` → `resolve_ibkr_data_dir`).
- **Candidates:** `src/research/results/Archive/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates`.
- **IDs:** `PA_BUY_SELL_CLOSE_TREND_003`, `GAP_ACCEPTANCE_FAILURE_001` (via profiles `pa_only_mtp1_meta`, `pa_gap_mtp2_meta`; CLI supports comma-separated `--profile`).

---

## 5. Layer file map summary

`layer_file_map.csv` + `layer_file_map.md`: Layer1/2/3 files mapped to **active** vs **compatibility_reference**; **`src/execution/`** is the only layer that **should** own accounting math.

---

## 6. Cleanup inventory summary

`file_cleanup_candidates.csv`: **no deletes**; highlights **Archive / legacy** as long-lived compatibility trees and **`_local_only/`** as gitignored scratch under the result root.

---

## 7. Overlay design

`exit_overlay_execution_path_design.md` + `.csv`: six overlay names (normalized to lowercase/underscores), replay rules, and the **per-trade sensitivity** caveat.

---

## 8. Supported vs unsupported overlays

| Overlay | Status |
|---------|--------|
| `baseline_execution_backed` | supported (combiner aggregates) |
| `max_hold_tighten_60` | supported (`ExitPlan.max_hold_bars_cap`) |
| `no_followthrough_exit_5bars` | supported (`ExitPlan` NFT fields) |
| `trend_swing_2r` | supported (`target_r=2.0` when `fixed_r`) |
| `trail_after_1r_simple` | **unsupported** (no arm-after-R trailing threshold) |
| `runner_after_1r_reference` | **unsupported** (no runner ladder) |

Deduped reasons: `overlay_unsupported.csv` (4 rows + header).

---

## 9. Smoke results (QQQ Jan 2024)

From `overlay_smoke_summary.csv` (representative):

| Profile | Overlay | trades | total_r | profit_factor_r |
|---------|---------|--------|---------|-----------------|
| pa_only | baseline | 16 | 6.138 | 2.338 |
| pa_only | max_hold_60 | 16 | 4.277 | 2.318 |
| pa_only | nft_5b | 16 | 2.045 | 2.280 |
| pa_only | trend_2r | 16 | 6.624 | 2.444 |
| pa_gap | baseline | 23 | 4.412 | 1.452 |
| pa_gap | max_hold_60 | 23 | 1.558 | 1.185 |
| pa_gap | nft_5b | 23 | **-0.379** | 0.906 |
| pa_gap | trend_2r | 23 | 6.478 | 1.664 |

Trail + runner rows show **0** replayed trades because every trade records **unsupported** (not silently converted to baseline).

---

## 10. Optional repo-coverage results

**Ran:** full QQQ span in repo data (**2020-01-01** … **2026-04-30**). See `overlay_repo_coverage_summary.csv` and `overlay_repo_coverage_by_*`. Pattern matches smoke: **max_hold** and **NFT** reduce **`total_r`** vs baseline on both profiles; **trend_swing_2r** stays in the ballpark of baseline totals.

---

## 11. Interpretation

See `overlay_interpretation.md` + `overlay_key_findings.csv`. Short version: **supported overlays are mostly harmful** on this champion slice; **unsupported** overlays are honestly blocked pending **`ExitPlan` / policy** extensions.

---

## 12. Decision

**`USE_EXECUTION_BACKED_FOR_RESEARCH_AND_REBUILD_LAYER1_2_3`** — details in `exit_overlay_execution_path_decision.md`.

---

## 13. Explicit non-runs / risks

No WFO, live/paper, SPY sweeps, broad Layer2, Global Layer1, router production work, scalp/short, Champion YAML edits, legacy deletion, or heavy artifact commits (`_local_only/` gitignored). **Optional** `primary_mtp2_meta` + `CCI_EXTREME_SNAPBACK_003` third-candidate profile **not run** (smoke cost vs incremental insight).

---

## 14. Recommended next step

**`USE_EXECUTION_BACKED_FOR_RESEARCH_AND_REBUILD_LAYER1_2_3`**

---

## Appendix: key source files

| File | Role |
|------|------|
| `src/research/run_exit_overlay_execution_path.py` | Thin orchestrator |
| `src/combiner/adapter.py` | Baseline combiner canonical |
| `src/combiner/trade_intent_adapter.py` | `TradeIntent` construction |
| `src/execution/path.py` | `simulate_trade_path` |
| `src/execution/types.py` | `TradeIntent`, `ExitPlan` |
| `tests/test_exit_overlay_execution_path.py` | Pure helper tests |

Full map: `SOURCE_MAP.csv`.
