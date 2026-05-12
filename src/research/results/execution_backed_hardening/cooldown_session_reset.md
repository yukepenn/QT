# Cooldown reset on new session

**Problem:** `reset_day` cleared daily counters but left `cooldown_until_bar` from a late-session loss, blocking the **next** session’s early bars.

**Fix:** `CombinerState.reset_day` now sets `cooldown_until_bar = -1` and `open_positions = 0` (defensive flat state for a new `session_date` in this sequential combiner model).

**Regression:** `tests/test_execution_backed_hardening.py::test_reset_day_clears_cooldown_and_open_positions`.
