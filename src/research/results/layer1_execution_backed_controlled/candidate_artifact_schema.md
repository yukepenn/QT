# Candidate artifact schema — Layer1 controlled (future run)

**Future output root (runs):** `src/research/results/layer1_execution_backed_controlled/selected_candidates/`  
**This design task:** does **not** write real candidate YAML (only reserved folder + this schema). The **next** run task creates YAML + indices.

## Required YAML / metadata fields (per candidate)

| Field | Description |
|-------|-------------|
| `candidate_id` | Stable string, e.g. `PA_BUY_SELL_CLOSE_TREND_L1_001` |
| `strategy_name` | Loader key (`pa_buy_sell_close_trend`, …) |
| `strategy_family` | High-level grouping (e.g. `pa`, `gap`, `cci`) |
| `setup_type` | If known from strategy metadata |
| `symbol` | `QQQ` |
| `side` | `long` / policy alignment |
| `strategy_config` | Frozen merged dict (or path + hash) |
| `feature_config` | Frozen feature dict slice (or hash only + archive path under result root, **not** Archive legacy) |
| `execution_engine` | **`execution_backed`** (recommended stamp; aligns with Layer2 vocabulary) |
| `execution_semantics_version` | From `ExecutionPolicy.semantics_version` at run time |
| `execution_policy_hash` | Hash of slippage, commission, same_bar, eod, min_risk, etc. |
| `signal_contract_version` | e.g. `standard_sig_v1` |
| `feature_config_hash` | SHA256 short (already computed in sweep rows) |
| `strategy_config_hash` | From sweep `config_hash` or recomputed |
| `data_root` | `data/raw/ibkr` (repo-relative) |
| `data_window` | `start` / `end` ISO strings |
| `created_git_sha` | `git rev-parse HEAD` |
| `created_at` | UTC ISO timestamp |
| `layer` | `1` |
| `selection_gate_label` | e.g. `L1_STRICT_V1` |
| `metric_summary` | Embedded dict or sidecar JSON path (curated only) |

## Aggregates / indices (next run)

| Artifact | Purpose |
|----------|---------|
| `sweep_results.csv` | One row per combo (existing sweep writer shape + any extensions) |
| `selected_candidates_summary.csv` | Top picks + reasons |
| `selected_candidates_index.csv` | Map `candidate_id` → file path |
| `candidate_rejects_summary.csv` | Gate failures |
| `feature_config_inventory.csv` | Distinct feature hashes used |
| `strategy_grid_inventory.csv` | Grid provenance |
| `execution_policy_inventory.csv` | Policy fingerprints used |

**Forbidden in git:** raw per-trade CSV panels, `local_rows`, `local_runs`, `top_runs`, large memmap/npy.
