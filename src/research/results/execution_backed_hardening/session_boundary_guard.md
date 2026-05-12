# Session-boundary guard (Layer2 execution-backed)

**Problem:** `entry_bar = cursor + 1` could land on the first bar of the **next** `session_date` while the signal was still on the prior session’s last bar.

**Fix:** After bounds check, skip the signal when `meta_arrays["session_date"][entry_bar] != sess_day` (same check as `sess_day` taken at `cursor`).

**Regression:** `tests/test_execution_backed_hardening.py::test_session_boundary_skips_next_session_entry`.
