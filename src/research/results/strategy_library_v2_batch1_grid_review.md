# Strategy Library v2 Batch 1 — focused grid review

## Policy

- Target **≤ 2000** raw cartesian combos per `*_focused.yaml` where practical.
- Layer 1 2023–2024 runs use **`--max-combos 500`** when raw grid **> 2000** (documented as **capped** in `sweep_manifest.csv`).
- **Donchian** grid was adjusted (wider `min`/`max` channel width vs ATR, earlier `entry_start_minute`, `require_volume_expansion` fixed to `[false]` only) to land at **1728** combos and reduce Jan-only starvation.

## Per-strategy

| Strategy | raw_grid | >2000 | Action |
|----------|---------:|-------|--------|
| intraday_ma_crossover | 2304 | yes | Sweep capped 500 |
| rsi_failure_swing | 3072 | yes | Sweep capped 500 |
| bollinger_squeeze_breakout | 6144 | yes | Sweep capped 500 |
| bollinger_band_fade_chop | 6144 | yes | Sweep capped 500 |
| donchian_channel_breakout | 1728 | no | Full exhaust |
| consecutive_bar_exhaustion | 6144 | yes | Sweep capped 500 |

## Interpretation

- **Bollinger** families pay a **combinatorics tax**; capped sweeps explore an arbitrary slice — treat leaderboard as **indicative**, not exhaustive.
- **Donchian** is now **searchable** at full grid but still **failed** conservative candidate filters on 2023–2024 (see `no_candidate_strategies.txt`).
- **Intraday MA** grid is only modestly over 2000; still capped for runtime parity with other Batch 1 runs.

See `strategy_library_v2_batch1_grid_review.csv` for the same table in machine form.
