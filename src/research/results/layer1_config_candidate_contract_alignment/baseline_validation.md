# Baseline validation — contract alignment

See **`baseline_validation.csv`**. Full suite **163** `pytest` after changes.

Optional PA dry-run (repo root, repo-local data):  
`python -m src.backtest.sweep --strategy pa_buy_sell_close_trend --symbol QQQ --asset equity --start 2024-01-02 --end 2024-01-05 --data-root data/raw/ibkr --grid src/strategies/testing_parameters/pa_buy_sell_close_trend_focused.yaml --dry-run --max-combos 1 --no-save`
