"""Generic YAML/config validation helpers (strategy, backtest, combiner)."""

from __future__ import annotations

from typing import Any, Iterable

_MINUTE_MAX = 389
_SIDE_CHOICES = frozenset({"long_only", "short_only", "both"})
_COMBINER_PRIORITY = frozenset({"metadata_priority", "score_adjusted_priority", "score_adjusted_policy"})


def get_nested(cfg: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = cfg
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return default
        cur = cur[p]
    return cur


def has_nested(cfg: dict[str, Any], path: str) -> bool:
    cur: Any = cfg
    for p in path.split("."):
        if not isinstance(cur, dict) or p not in cur:
            return False
        cur = cur[p]
    return True


def validate_choice(name: str, value: Any, allowed: Iterable[str]) -> None:
    allowed_set = set(allowed)
    s = str(value)
    if s not in allowed_set:
        raise ValueError(f"{name}: invalid value {value!r}; allowed={sorted(allowed_set)}")


def validate_bool(name: str, value: Any) -> None:
    if not isinstance(value, bool):
        raise ValueError(f"{name}: expected bool, got {type(value).__name__} ({value!r})")


def validate_positive_number(name: str, value: Any, *, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    if value is None:
        raise ValueError(f"{name}: expected a positive number, got None")
    try:
        x = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name}: not a number ({value!r})") from e
    if x <= 0:
        raise ValueError(f"{name}: must be > 0, got {value!r}")


def validate_nonnegative_number(name: str, value: Any, *, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    if value is None:
        raise ValueError(f"{name}: expected a non-negative number, got None")
    try:
        x = float(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name}: not a number ({value!r})") from e
    if x < 0:
        raise ValueError(f"{name}: must be >= 0, got {value!r}")


def validate_int_at_least(name: str, value: Any, min_value: int, *, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    if value is None:
        raise ValueError(f"{name}: expected int >= {min_value}, got None")
    try:
        x = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name}: not an int ({value!r})") from e
    if x < min_value:
        raise ValueError(f"{name}: must be >= {min_value}, got {value!r}")


def validate_minute_value(name: str, value: Any, *, allow_none: bool = False) -> None:
    if value is None and allow_none:
        return
    if value is None:
        raise ValueError(f"{name}: minute is None")
    try:
        x = int(value)
    except (TypeError, ValueError) as e:
        raise ValueError(f"{name}: minute must be int-like, got {value!r}") from e
    if x < 0 or x > _MINUTE_MAX:
        raise ValueError(f"{name}: minute must be in [0, {_MINUTE_MAX}], got {x}")


def validate_minute_range(
    start_name: str,
    start: Any,
    end_name: str,
    end: Any,
    *,
    allow_none_start: bool = False,
) -> None:
    if start is None or end is None:
        if allow_none_start and start is None:
            validate_minute_value(end_name, end)
            return
        return
    validate_minute_value(start_name, start)
    validate_minute_value(end_name, end)
    es, ee = int(start), int(end)
    if ee <= es:
        raise ValueError(f"{end_name} must be > {start_name} (got {ee} <= {es})")


def validate_long_only_mvp(cfg: dict[str, Any], *, strategy_name: str) -> None:
    sig = cfg.get("signal") or {}
    if "side" not in sig:
        return
    s = str(sig["side"])
    if s != "long_only":
        raise ValueError(
            f"{strategy_name}: MVP implements long-only signals; signal.side must be 'long_only', got {s!r}"
        )


def validate_common_backtest_section(bt: dict[str, Any]) -> None:
    if not bt:
        return
    mh = bt.get("max_hold_minutes")
    if mh is not None:
        validate_positive_number("backtest.max_hold_minutes", mh)
    if "eod_exit_minute" in bt:
        validate_minute_value("backtest.eod_exit_minute", bt.get("eod_exit_minute"))
    nna = bt.get("no_new_after_minute")
    eod = bt.get("eod_exit_minute")
    if nna is not None and eod is not None:
        if int(nna) > int(eod):
            raise ValueError(
                f"backtest.no_new_after_minute ({nna}) must be <= backtest.eod_exit_minute ({eod})"
            )


def validate_common_strategy_config(cfg: dict[str, Any]) -> None:
    sig = cfg.get("signal") or {}
    risk = cfg.get("risk") or {}
    bt = cfg.get("backtest") or {}

    if "side" in sig:
        validate_choice("signal.side", sig["side"], _SIDE_CHOICES)

    validate_minute_range(
        "signal.entry_start_minute",
        sig.get("entry_start_minute"),
        "signal.entry_end_minute",
        sig.get("entry_end_minute"),
    )

    if "max_trades_per_day" in risk:
        validate_int_at_least("risk.max_trades_per_day", risk.get("max_trades_per_day"), 1)

    tm = str(risk.get("target_mode", "fixed_r"))
    if tm == "fixed_r" and "target_r" in risk and risk.get("target_r") is not None:
        validate_positive_number("risk.target_r", risk.get("target_r"))

    tr_sig = sig.get("target_r")
    if tr_sig is not None:
        validate_positive_number("signal.target_r", tr_sig)

    validate_common_backtest_section(bt)


def validate_common_combiner_config(cfg: dict[str, Any]) -> None:
    ex = cfg.get("execution") or {}
    sy = cfg.get("system") or {}
    cf = cfg.get("conflict") or {}

    validate_nonnegative_number("execution.slippage_per_share", ex.get("slippage_per_share", 0.0))
    validate_nonnegative_number("execution.commission_per_trade", ex.get("commission_per_trade", 0.0))
    validate_nonnegative_number("execution.min_risk_per_share", ex.get("min_risk_per_share", 0.0))

    mop = int(sy.get("max_open_positions", 1))
    if mop != 1:
        raise NotImplementedError(
            f"system.max_open_positions must be 1 for current combiner engine (got {mop})"
        )

    validate_int_at_least("system.max_trades_per_day", sy.get("max_trades_per_day", 1), 1)

    if "daily_max_loss_r" in sy:
        dml = sy["daily_max_loss_r"]
        if dml is None:
            raise ValueError("system.daily_max_loss_r must be set and negative")
        if float(dml) >= 0:
            raise ValueError(f"system.daily_max_loss_r must be < 0, got {dml!r}")

    validate_nonnegative_number(
        "system.cooldown_after_loss_minutes",
        sy.get("cooldown_after_loss_minutes", 0),
    )

    eod = int(ex.get("eod_exit_minute", 389))
    nna = int(ex.get("no_new_after_minute", eod))
    validate_minute_value("execution.eod_exit_minute", eod)
    validate_minute_value("execution.no_new_after_minute", nna)
    if nna > eod:
        raise ValueError(
            f"execution.no_new_after_minute ({nna}) must be <= execution.eod_exit_minute ({eod})"
        )

    pol = str(cf.get("priority_policy", "metadata_priority"))
    if pol not in _COMBINER_PRIORITY:
        raise ValueError(
            f"conflict.priority_policy invalid: {pol!r}; allowed={sorted(_COMBINER_PRIORITY)}"
        )
