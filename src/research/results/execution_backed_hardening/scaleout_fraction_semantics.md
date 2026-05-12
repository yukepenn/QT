# Scale-out fraction semantics

**Contract (types + docs):** `ScaleOutRule.exit_fraction` applies to **remaining** quantity after prior scale-out legs.

**Implementation fix:** `_maybe_scale_out` in `path.py` now uses `qty_part = qty_rem * float(rule.exit_fraction)` (was incorrectly `qty * exit_fraction`).

**Regression:** Two rules at `0.5` each → first leg `qty_frac=0.5`, second `0.25` (75% exited, 25% left for later exits) — `tests/test_execution_backed_hardening.py::test_scale_out_fraction_applies_to_remaining_qty`.
