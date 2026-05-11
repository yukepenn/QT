# Layer2 candidate robustness v1 — baseline inventory

## Git

| Field | Value |
|--------|--------|
| Branch | `main` (at pack time; verify `git branch --show-current`) |
| Repo tip | Run `git log -1 --oneline` after local commit (**this work** adds candidate audit + docs) |
| Prior fixed-profile OOW research anchor | `dbd2817` — `Research: run fixed profile out-of-window validation` |

## Handoff decisions

| Source | Decision |
|--------|----------|
| `NEXT_HANDOFF.md` (pre-audit) | **`REVISIT_LAYER2_CANDIDATE_SELECTION`** |
| `fixed_profile_oow_v1/fixed_profile_oow_decision.md` | **`REVISIT_LAYER2_CANDIDATE_SELECTION`** |

## l2_core candidate root

- Path: `src/research/results/layer1_global_qqq_2023_2024_v2/selected_candidates_l2_core/selected_candidates`
- **YAML count:** 66
- **Families (audit grouping):** afternoon 4, indicator 19, opening_trap 12, other 7, pa 16, vwap 8 (from `family_group()` on each YAML)

## QQQ windows (nominal)

Window bounds loaded from `fixed_profile_oow_v1/data_availability.csv` when present (else parquet scan + `default_windows`).

| window_id | Role |
|-----------|------|
| early_oow | 2020–2022 (clipped to data) |
| insample_ref | 2023–2024 |
| late_oow | 2025–2026-04 (clipped) |
| full_available | full span (optional; **not** used for primary labels in v1 pack) |

## This audit execution scope (v1 pack)

- **Families run:** `vwap`, `indicator` only (**27** candidates × **3** windows = **81** combiner runs).
- **Not run in v1 pack:** `opening_trap`, `pa`, `afternoon`, `other` (remaining **39** YAMLs).
- **Combiner envelope:** singleton `--candidate-ids` replays with default config `fixed_profile_oow_v1/configs/layer2_fixed_vwap_mtp2.yaml` (execution/router envelope only; candidate parameters unchanged).
- **Signal cache:** off (no `--use-signal-cache`).

## Local raw run availability

- **Root:** `src/research/results/layer2_candidate_robustness_v1/local_runs/<candidate_segment>/<window_id>/run_*`
- **Expected local-only:** `trades.csv`, `config_resolved.yaml`, other combiner artifacts — **do not commit**.

## Curated manifests (committed)

- `candidate_audit_run_manifest.csv` / `run_execution_manifest.csv` — last run session
- `run_discovery_manifest.csv` — filesystem scan of `local_runs/**/metrics.json`

## Missing files

- None required for interpretation of the **vwap+indicator** slice; full **66×3** matrix intentionally incomplete pending extended audit.
