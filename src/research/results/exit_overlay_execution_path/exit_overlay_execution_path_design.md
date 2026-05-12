# Exit overlay on execution path — design

## Objective

Evaluate **Champion** candidates on repo-local QQQ bars by:

1. Building a **baseline** trade list with **`simulate_combiner_canonical`** (**`execution_backed`** engine via combiner YAML + CLI defaults in `run_combiner_fixed_config` path used by the runner).
2. For each non-baseline overlay, **replaying** each baseline trade through **`simulate_trade_path`** with a modified **`TradeIntent`** and/or **`ExitPlan`**.

There is **no** third replay engine: all R math stays inside **`src/execution/`**.

## Profiles

| Profile | Candidate IDs |
|---------|----------------|
| `pa_only_mtp1_meta` | `PA_BUY_SELL_CLOSE_TREND_003` |
| `pa_gap_mtp2_meta` | `PA_BUY_SELL_CLOSE_TREND_003`, `GAP_ACCEPTANCE_FAILURE_001` |

CLI accepts **comma-separated** `--profile pa_only_mtp1_meta,pa_gap_mtp2_meta` to emit **one** set of aggregate CSVs for smoke.

## Windows

- **Smoke (required):** QQQ **2024-01-01** … **2024-01-31**
- **Repo coverage (optional, executed):** earliest … latest QQQ partition under `data/raw/ibkr` discovered at run time (**2020-01-01** … **2026-04-30** on this workspace).

## Overlays

| Overlay | Mechanism | Support |
|---------|-----------|---------|
| `baseline_execution_backed` | combiner canonical aggregates | **supported** |
| `max_hold_tighten_60` | `ExitPlan.max_hold_bars_cap` min with 60 | **supported** |
| `no_followthrough_exit_5bars` | `ExitPlan` NFT fields (5 bars, 0.05 R) | **supported** |
| `trend_swing_2r` | `TradeIntent.target_r = 2.0` when `fixed_r` | **supported** |
| `trail_after_1r_simple` | needs arm-after-R on trailing in `ExitPlan` | **unsupported_in_current_execution_contract** |
| `runner_after_1r_reference` | scale ladder / runner not modeled | **unsupported_in_current_execution_contract** |

## Limits

- **Per-trade replay sensitivity:** non-baseline overlays do **not** re-walk the full Layer2 bar cursor; they answer “if this baseline fill happened, how would this exit plan behave?” which is adequate for **diagnostic** comparison but not a full production overlay scheduler.

Machine-readable principles: `exit_overlay_execution_path_design.csv`.
