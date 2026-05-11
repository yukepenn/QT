# replay_drift_hypotheses

| Hypothesis | How V2 tests | Status |
|------------|--------------|--------|
| Missing **exit slip** on stop/target/EOD | `slippage_policy=apply_like_combiner` vs `none` / `already_in_panel` | Primary v1 drift driver |
| Entry uses **panel price** vs **open+slip** | `entry_price_source` grid | Second-order |
| Risk uses **panel risk** vs **abs(entry-stop)** | `risk_policy` grid | Affects R denominator |
| Wrong first simulation bar | `start_bar_policy=entry_bar` vs `bar_after_entry` | Diagnostic |
| Target preview vs recompute | `target_policy` grid | tm=1 + target_r in panel |
| Forced exit path mismatch | `forced_exit_policy=max_hold` vs `panel_exit_idx` | Oracle-truncation diagnostic |
| Ambiguity | `same_bar_policy` × overlay `AmbiguityPolicy` | Sensitivity only |
