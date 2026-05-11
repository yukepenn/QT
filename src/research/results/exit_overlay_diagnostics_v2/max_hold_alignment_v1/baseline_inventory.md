# Baseline inventory — max_hold_alignment_v1

Frozen snapshot before documenting **max_hold** replay refinement (research-only).

## Git

- **Recorded tip:** `c342c7b9c963f0154ece92271ff88af7b66fcb6a` (`Research(exit): run full-panel overlay alignment`).
- **Remote:** `https://github.com/yukepenn/QT` — verify `main` after push of this cycle.

## Prior formal decision

- **`REFINE_REPLAY_ALIGNMENT`** (`exit_overlay_diagnostics_v2_decision.md`).

## Prior best alignment config

- **`cfg_0015`** — `intrabar_first` max-hold priority; see `alignment/alignment_best_config.yaml`.

## Full-panel metrics (pre–max_hold mode split, same headline row)

| Metric | Value |
|--------|------:|
| Panel rows | 10,628 |
| QQQ 1m bar rows | 617,160 |
| Mean abs R diff | ~0.03495 |
| Median abs R diff | 0 |
| Total R diff | ~+52.4R |
| Label | `ALIGNMENT_FAIL` |

## Max_hold drift summary (cfg_0015)

| Metric | Value |
|--------|------:|
| Panel `exit_reason=max_hold` rows | 5,188 |
| Replay `stop`/`target` while panel `max_hold` | 476 |
| Replay exit bar **before** `panel_exit_idx` | 476 |
| On `panel_exit_idx` | 0 |
| After `panel_exit_idx` | 0 |

## Alignment grid (this cycle)

- **18** configs (`iter_default_alignment_grid`), including **`cfg_0016_mh_forced`**, **`cfg_0017_mh_panelauth`**, **`cfg_0018_mh_skipconf`** (`alignment/alignment_config_manifest.csv`).

## Relevant files inspected

- `src/combiner/simulator.py` (numba + Python exit loops).
- `src/research/exit_overlay_alignment.py` (`combiner_clone_long_walk`, grid, aggregates).
- `src/research/run_exit_overlay_diagnostics_v2.py` (alignment runner, detail columns).
- `src/research/exit_overlay_sim.py` (`SimResult`, intrabar resolution).
- `tests/test_exit_overlay_alignment.py`.

## Local-only inputs (do not commit)

- `src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv`
- `src/research/results/exit_overlay_diagnostics_v2/local_rows/alignment_trade_detail.csv`
- `data/raw/ibkr/**` (QQQ partitions)

## Non-goals (this cycle)

- No production combiner semantics change.
- No Champion v0 YAML / strategy edits.
- No WFO, live, SPY, broad Layer2, Global Layer1.
- No row-level committed artifacts.
