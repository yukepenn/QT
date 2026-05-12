# Scale-out regression status

**Contract:** `ScaleOutRule.exit_fraction` applies to **remaining** quantity after prior scale-outs.

**Code:** `src/execution/path.py` (`_maybe_scale_out`).

**Tests:** `tests/test_execution_backed_hardening.py::test_scale_out_fraction_applies_to_remaining_qty` and execution path tests — **no new test required** for this alignment task.
