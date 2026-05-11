"""Optional accelerated path (placeholder until Numba parity tests exist)."""


def simulate_trade_path_fast(*args, **kwargs):
    from src.execution.path import simulate_trade_path

    return simulate_trade_path(*args, **kwargs)
