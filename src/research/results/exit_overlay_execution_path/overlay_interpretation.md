# Overlay interpretation

## Baseline reproducibility

The **`baseline_execution_backed`** rows in `overlay_smoke_summary.csv` reproduce the **combiner canonical** trade counts for the Jan 2024 QQQ window on this machine (**16** trades for `pa_only_mtp1_meta`, **23** for `pa_gap_mtp2_meta`), consistent with the prior **`combiner_adapter_parity`** smoke scale (not a byte-identical `total_r` parity claim vs legacy).

## Supported vs unsupported

- **Supported overlays:** `baseline_execution_backed`, `max_hold_tighten_60`, `no_followthrough_exit_5bars`, `trend_swing_2r` — all expressed via **`TradeIntent`** / **`ExitPlan`** + **`simulate_trade_path`**.
- **Unsupported:** `trail_after_1r_simple`, `runner_after_1r_reference` — reasons deduped in `overlay_unsupported.csv` and echoed in `unsupported_overlay_capabilities.csv` (dry-run probe).

## Overlay economics (high level)

| Overlay | PA-only smoke | PA+GAP smoke | Repo coverage (both profiles) |
|---------|---------------|--------------|-------------------------------|
| Baseline | Best total_R in window | Baseline PF_R ~1.45 | Baseline total_R highest |
| max_hold_60 | Lower total_R | Much lower total_R | Lower total_R vs baseline |
| NFT 5b / 0.05R | Lower total_R | **Negative** total_R | Large total_R haircut |
| trend_swing_2r | Slightly higher total_R | Near baseline total_R | Modest change vs baseline |

**Max-hold tighten** and **NFT** behave as aggressive **time / stagnation** exits: they materially reduce exposure but, on this champion slice, **cut winners** more than they improve the aggregate R profile.

**Trend swing 2R** is **contract-valid** but not decisively better once the second candidate competes (GAP profile), and still lacks explicit drawdown analytics here.

## Trailing / runner gap

Trailing-after-R and runner references require **richer `ExitPlan` / policy** (arm rules, partials, ladder) than the current diagnostic contract exposes. Marked **`unsupported_in_current_execution_contract`** — do **not** fake with external math.

## Management promotion?

No overlay meets the bar for immediate promotion into **`src/management/`**: supported overlays are mostly **harmful** to Jan smoke and/or long-span totals on this slice, and advanced overlays are **unsupported**.

Machine-readable labels: `overlay_key_findings.csv` (mirrored for reviewers as `exit_overlay_execution_path_key_findings.csv`).
