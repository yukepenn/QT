import numpy as np
import pandas as pd

from src.backtest.engine import run_strategy_backtest
from src.backtest.backtest_config import BacktestConfig


def test_run_strategy_backtest_smoke():
    n = 20
    rng = np.arange(n)
    df = pd.DataFrame(
        {
            "session_date": ["2024-01-02"] * n,
            "ts_utc": pd.date_range("2024-01-02 14:30", periods=n, freq="min", tz="UTC"),
            "ts_ny": pd.date_range("2024-01-02 09:30", periods=n, freq="min"),
            "minute_from_open": rng,
            "open": np.linspace(100, 101, n),
            "high": np.linspace(100.5, 101.5, n),
            "low": np.linspace(99.5, 100.5, n),
            "close": np.linspace(100.2, 101.2, n),
            "sig_valid": [False] * 3 + [True] + [False] * (n - 4),
            "sig_side": [0] * 3 + [1] + [0] * (n - 4),
            "sig_stop": [float("nan")] * 3 + [99.0] + [float("nan")] * (n - 4),
            "sig_target": [float("nan")] * n,
            "sig_target_mode": [""] * 3 + ["fixed_r"] + [""] * (n - 4),
            "sig_target_r": [float("nan")] * 3 + [2.0] + [float("nan")] * (n - 4),
            "sig_risk_per_share": [float("nan")] * 3 + [1.0] + [float("nan")] * (n - 4),
            "sig_reason": [""] * n,
            "sig_strategy": ["test"] * n,
            "sig_entry_ref": [pd.NA] * n,
        }
    )
    cfg = BacktestConfig()
    trades, summ = run_strategy_backtest(df, config=cfg)
    assert summ["trades"] >= 0
