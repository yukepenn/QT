"""Optional accelerated path.

Delegates to :func:`src.execution.path.simulate_trade_path` until a Numba port
exists with parity tests.
"""


def simulate_trade_path_fast(*args, **kwargs):
    from src.execution.path import simulate_trade_path

    return simulate_trade_path(*args, **kwargs)
