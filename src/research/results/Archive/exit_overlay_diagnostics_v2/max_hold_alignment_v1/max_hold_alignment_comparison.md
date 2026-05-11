# max_hold alignment comparison

| config | max_hold_priority | trades | mean_abs_r_diff | total_r_diff | label |
|---|---|---:|---:|---:|---|
| cfg_0015 | intrabar_first | 10628 | 0.0349543967664403 | 52.40313920705445 | ALIGNMENT_FAIL |
| cfg_0016_mh_forced | forced_first_on_terminal_bar | 10628 | 0.0350812614617336 | 51.16054809772402 | ALIGNMENT_FAIL |
| cfg_0017_mh_panelauth | panel_exit_reason_authoritative | 10628 | 0.0349543967664403 | 52.40313920705445 | ALIGNMENT_FAIL |
| cfg_0018_mh_skipconf | skip_terminal_bar_conflicts | 10152 | 4.736853226742632e-15 | -5.215828572058774e-12 | ALIGNMENT_PASS |

**Note:** `skip_terminal_bar_conflicts` excludes max_hold-vs-stop/target mismatches from metrics; 
it is diagnostic-only and not an economic overlay baseline.
