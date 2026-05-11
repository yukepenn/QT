# Layer 1 — v2 Batch 1 (QQQ 2023–2024)

## Runs

- Six strategies, tag `layer1_v2_batch1_qqq_2023_2024`.
- `sweep_manifest.csv` / `sweep_manifest.md` — per-strategy status, **capped** flag, paths to `results.csv` under `src/strategies/testing_parameters_results/`.

## Candidates

- `select_candidates.py` manifest mode → **20** YAMLs (`selected_candidates/`).
- **No candidates:** `intraday_ma_crossover`, `donchian_channel_breakout` — see `no_candidate_strategies.txt`.
- Thresholds: `candidate_selection_config.md`.

## Supersedes

- Earlier partial `rsi_failure_swing`-only selection under the same tag is **superseded** by this unified manifest + selection pass.

Interpretation: `../strategy_library_v2_batch1_summary.md`.
