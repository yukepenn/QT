# Run from QT repository root (parent of `src/`).
# Example: Set-Location "D:\OneDrive - Washington University in St. Louis\QT"
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "=== compileall ==="
python -m compileall -q src

Write-Host "=== pytest (full) ==="
python -m pytest -q

Write-Host "=== strategies loader ==="
python -m src.strategies.loader --list

Write-Host "=== artifact validation ==="
python -m src.research.validate_research_artifacts `
  --root src/research/results/exit_overlay_diagnostics_v2 `
  --csv-only `
  --output src/research/results/exit_overlay_diagnostics_v2/exit_overlay_diagnostics_v2_artifact_validation.csv

Write-Host "=== tracked-heavy ==="
git ls-files | Select-String -Pattern "top_runs|trades.csv|compact_trades|enriched.csv|scored_trades|trade_context_panel.csv|overlay_trade_results.csv|overlay_trade_results_v2.csv|\.parquet|\.npy|\.npz|\.memmap"

Write-Host "Done. Alignment/overlay: see full_panel_commands.md"
