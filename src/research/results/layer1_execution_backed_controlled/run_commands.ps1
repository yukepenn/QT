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
$CAND = "src/strategies/testing_parameters_results/l1_execution_backed_controlled"
python -m src.research.run_layer1_execution_backed_controlled validate-candidates --candidate-root $CAND --allow-empty
# python -m src.research.run_layer1_execution_backed_controlled promote --runs-root $OUT --candidate-root $CAND --max-per-strategy 3 --min-trades 20 --min-profit-factor-r 1.05 --min-total-r 0.0 --gate-label L1_EXECUTION_BACKED_CONTROLLED_STRICT_V1
# python -m src.research.run_layer1_execution_backed_controlled promote --runs-root $OUT --candidate-root $CAND ... --write

python -m src.research.validate_research_artifacts --root src/research/results/layer1_execution_backed_controlled --csv-only --output src/research/results/layer1_execution_backed_controlled/layer1_execution_backed_controlled_artifact_validation.csv
