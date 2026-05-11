# Fixed-profile OOW v1 — execution runbook

## Profiles

| id | config | candidate_set |
|----|--------|----------------|
| `vwap_mtp2` | `configs/layer2_fixed_vwap_mtp2.yaml` | `vwap_core` |
| `vwap_mtp1` | `configs/layer2_fixed_vwap_mtp1.yaml` | `vwap_core` |
| `indicator_mtp1` | `configs/layer2_fixed_indicator_mtp1.yaml` | `indicator_completion_core` |
| `indicator_mtp2` | `configs/layer2_fixed_indicator_mtp2.yaml` | `indicator_completion_core` |
| `indicator_mtp3` | `configs/layer2_fixed_indicator_mtp3.yaml` | `indicator_completion_core` (diagnostic) |

## Windows

From `inspect-data` → `data_availability.csv` (clipped to local QQQ parquet):

- `early_oow` — pre-2023
- `insample_ref` — 2023–2024
- `late_oow` — post-2024 through last available bar
- `full_available` — full clipped span

## Commands (repo root)

**Do not** pass `--use-signal-cache` on unsafe OneDrive roots (combiner defaults to YAML; fixed YAMLs do not enable cache).

```powershell
python -m src.research.fixed_profile_oow inspect-data --output-root src/research/results/fixed_profile_oow_v1

python -m src.research.fixed_profile_oow run --output-root src/research/results/fixed_profile_oow_v1 `
  --profiles vwap_mtp2,vwap_mtp1,indicator_mtp1,indicator_mtp2,indicator_mtp3 `
  --windows insample_ref,early_oow,late_oow,full_available `
  --skip-existing

python -m src.research.fixed_profile_oow enrich --output-root src/research/results/fixed_profile_oow_v1 `
  --profiles vwap_mtp2,vwap_mtp1,indicator_mtp1,indicator_mtp2 `
  --windows insample_ref,early_oow,late_oow

python -m src.research.fixed_profile_oow postprocess --output-root src/research/results/fixed_profile_oow_v1
```

Copy/paste variants: `run_commands_multiline.md`, `run_commands_powershell.ps1`.

## Artifacts

- **Local-only (do not commit):** `local_runs/**` (`trades.csv`, `trades_enriched.csv`, logs, large CSVs).
- **Committed:** curated metrics CSVs, summaries, `run_discovery_manifest.csv`, `run_execution_manifest.csv` (when present), YAMLs, this runbook.
