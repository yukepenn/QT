# Preflight — controlled Layer1 (from repo root)
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
python -m compileall -q src
python -m pytest -q
python -m src.strategies.loader --list
python -m src.backtest.sweep --validate-pipeline --strategy pa_buy_sell_close_trend --symbol QQQ --start 2024-01-02 --end 2024-01-05 --data-root data/raw/ibkr

# Dry-run smoke
python -m src.backtest.sweep --strategy pa_buy_sell_close_trend --symbol QQQ --start 2024-01-02 --end 2024-01-05 --data-root data/raw/ibkr --dry-run --max-combos 1

$DATA_ROOT = "data/raw/ibkr"
$START = "2023-01-01"
$END = "2024-12-31"
$OUT = "src/research/results/layer1_execution_backed_controlled/runs"

# Real sweeps (NEXT TASK — uncomment when ready)
# python -m src.backtest.sweep --strategy pa_buy_sell_close_trend --symbol QQQ --asset equity --start $START --end $END --data-root $DATA_ROOT --grid src/strategies/testing_parameters/pa_buy_sell_close_trend_focused.yaml --max-combos 64 --output-root "$OUT/pa_buy_sell_close_trend_2023_2024_m64"
# python -m src.backtest.sweep --strategy gap_acceptance_failure --symbol QQQ --asset equity --start $START --end $END --data-root $DATA_ROOT --grid src/strategies/testing_parameters/gap_acceptance_failure_focused.yaml --max-combos 64 --output-root "$OUT/gap_acceptance_failure_2023_2024_m64"
# python -m src.backtest.sweep --strategy cci_extreme_snapback --symbol QQQ --asset equity --start $START --end $END --data-root $DATA_ROOT --grid src/strategies/testing_parameters/cci_extreme_snapback_focused.yaml --max-combos 32 --output-root "$OUT/cci_extreme_snapback_2023_2024_m32"

python -m src.research.validate_research_artifacts --root src/research/results/layer1_execution_backed_controlled --csv-only --output src/research/results/layer1_execution_backed_controlled/layer1_execution_backed_controlled_artifact_validation.csv
