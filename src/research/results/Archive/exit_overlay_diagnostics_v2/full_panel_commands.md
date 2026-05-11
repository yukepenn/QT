# full_panel_commands

PowerShell examples from repo root (`QT`). **`--data-dir`** defaults to `data/raw/ibkr`; override if your IBKR parquet lives elsewhere.

## 1) Input check (quick)

```powershell
python -c "import pandas as pd; p=r'src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv'; df=pd.read_csv(p); print(len(df), len(df.columns))"
```

## 2) Full-panel alignment

```powershell
python -m src.research.run_exit_overlay_diagnostics_v2 `
  --local-panel src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv `
  --v1-root src/research/results/exit_overlay_diagnostics_v1 `
  --output-root src/research/results/exit_overlay_diagnostics_v2 `
  --data-dir data/raw/ibkr `
  --mode alignment `
  --profiles pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta `
  --windows early_oow,insample_ref,late_oow,full_available `
  --aggregate-only `
  --local-row-output
```

Runtime: ~5 minutes on this machine for 10,628 × 15 configs.

## 3) Overlay (only if `alignment_decision.md` is PASS or PASS_WITH_WARNINGS)

**Skipped** for this cycle (`ALIGNMENT_FAIL`). When eligible:

```powershell
python -m src.research.run_exit_overlay_diagnostics_v2 `
  --local-panel src/research/results/local_detailed_trade_context_replay_v1/local_rows/trade_context_panel.csv `
  --v1-root src/research/results/exit_overlay_diagnostics_v1 `
  --output-root src/research/results/exit_overlay_diagnostics_v2 `
  --data-dir data/raw/ibkr `
  --mode overlay `
  --alignment-config src/research/results/exit_overlay_diagnostics_v2/alignment/alignment_best_config.yaml `
  --profiles pa_only_mtp1_meta,pa_gap_mtp2_meta,primary_mtp2_meta `
  --windows early_oow,insample_ref,late_oow,full_available `
  --overlays baseline_original,combiner_clone_replay,max_hold_tighten_60,trend_swing_2R_contextual,runner_after_1R_trail_vwap_contextual,runner_after_1R_trail_atr_contextual,no_followthrough_exit_5bars_contextual `
  --ambiguity-policies stop_first,target_first,skip_ambiguous `
  --aggregate-only `
  --local-row-output `
  --skip-existing
```

## 4) Artifact validation

```powershell
python -m src.research.validate_research_artifacts `
  --root src/research/results/exit_overlay_diagnostics_v2 `
  --csv-only `
  --output src/research/results/exit_overlay_diagnostics_v2/exit_overlay_diagnostics_v2_artifact_validation.csv
```

## 5) Tracked-heavy check (PowerShell)

```powershell
git ls-files | Select-String -Pattern "top_runs|trades.csv|compact_trades|enriched.csv|scored_trades|trade_context_panel.csv|overlay_trade_results.csv|overlay_trade_results_v2.csv|\.parquet|\.npy|\.npz|\.memmap"
```

Expected: **no output** (no tracked heavy paths).
