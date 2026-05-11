# combiner_semantics_inventory (long, max_open_positions=1)

Source: `src/combiner/simulator.py` (`_simulate_combiner_numba`).

| Topic | Convention |
|--------|-------------|
| Signal bar | Index `i` where candidate wins priority |
| Entry bar | **`entry_idx = i + 1`** — fill on **next bar open** |
| Entry price (long) | `open[i+1] + slippage_per_share` (default slip **0.01** in Layer2 YAMLs) |
| Stop | `stop_m[ci, i]` at **signal** bar `i` |
| Risk (long) | `act_risk = ent_price - stop_px` after entry slip |
| Target mode 1 | If `recomp_flag`: `tgt = ent_price ± target_r * act_risk`; else use preview matrix value |
| Same bar stop+target (long) | **`stop_first`** — both touched → stop exit |
| Exit price (long) | `_numba_exit_px`: **`raw_ex - slip`** on stop/target/EOD/max-hold |
| max_hold | Bars in trade: `i - entry_idx + 1`; exit at **close** with slip when `bh >= max_hold` |
| EOD | `minute >= eod_exit_minute` (default **389** in overlay harness, aligned with replay) |
| r_multiple | `(ex_price - ent_price) / act_risk` (long); commission tracked separately in `net` |
