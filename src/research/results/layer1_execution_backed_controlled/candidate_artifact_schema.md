# Candidate artifact schema — Layer1 controlled (future run)

## Runtime root (Layer2 `candidate_root`)

**Active library (combiner `load_candidates`):**  
`src/strategies/testing_parameters_results/l1_execution_backed_controlled/`

- Only **flat** `*.yaml` files (no subfolders unless loader gains recursion).
- Produced by **`python -m src.research.run_layer1_execution_backed_controlled promote --write`** after sweeps.

## Research / staging (audit only)

`src/research/results/layer1_execution_backed_controlled/selected_candidates/` — optional staging or docs; **not** the canonical runtime root unless you explicitly point Layer2 there.

## Required YAML fields (must match `src/combiner/candidate.py::load_candidate_yaml`)

| Field | Description |
|-------|-------------|
| `candidate_id` | Stable string, e.g. `PA_BUY_SELL_CLOSE_TREND_L1E_001` |
| `strategy` | Loader key (**not** `strategy_name` alone) |
| `symbol` | e.g. `QQQ` |
| `asset` | Optional; default `equity` in loader |
| `candidate_rank` | Optional; defaults from id suffix |
| `config` | Full merged frozen dict with **`features`**, **`signal`**, **`risk`**, **`backtest`** (**not** `strategy_config` as sole key) |
| `metrics` | Dict (trade_count, total_r, PF_R, …) — **not** only `metric_summary` |
| `metadata` | `family`, `conflict_group`, `default_priority`, active minute window, `allowed_sides`, `default_management_mode`, … |
| `selection` | `gate_label`, `score`, `warning`, … |
| `source` | `results_csv`, `sweep_folder` (repo-relative strings preferred) |

### Additional top-level block (allowed; not read into `Candidate` dataclass)

| Block | Description |
|-------|-------------|
| `execution` | e.g. `execution_engine: execution_backed`, `execution_semantics_version`, `signal_contract_version` |

## Aggregates written by promotion (`--write`)

| Artifact | Purpose |
|----------|---------|
| `CANDIDATE_INDEX.csv` | candidate_id → yaml filename |
| `selected_candidates_summary.csv` | promoted sweep rows |
| `candidate_rejects_summary.csv` | gate failures |

**Forbidden in git:** raw per-trade CSV panels, `local_rows`, `local_runs`, `top_runs`, large memmap/npy.
