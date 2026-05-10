# PA Batch A — implementation summary

## 1. Purpose

- Brooks / **price action** direction as **features → coarse regimes → plugins**, not hand-coded subjective candle labels.
- **Batch A** = four long-only MVP strategies on **QQQ** using **`pa_*`** and existing shared columns.
- **Formal Layer 1** PA Batch A (2023–2024) **not** run in this phase unless explicitly approved later.

## 2. Feature foundation

| Area | Files |
|------|--------|
| Bar shape | `src/features/price_action.py` |
| Prior-exclusive swings | `src/features/pa_swings.py` (new) |
| PA regime scores | `src/features/regime.py` |
| Proximity | `src/features/levels.py` (`near_*_atr`) |
| Config / key / pipeline | `build_types.py`, `feature_config.py`, `feature_key.py`, `build_features.py` |

**No-lookahead:** rolling prior highs/lows and derived range/breakout/failed-breakout columns use **shifted** session groupby rolls; no centered pivots; PA strategies do not require `*_LOOKAHEAD` features.

**Deferred:** delayed-confirmed pivot structures; richer wedge/leg models.

## 3. Strategies implemented

### pa_trading_range_bls_hs

- **Family:** `pa_trading_range` (`metadata.yaml`).
- **Purpose:** Buy-low in a **trading range** using `pa_trading_range_score_*`, range thirds, confirmations — **not** prior-day trap, not VWAP reversal, not ORB.
- **Required features (examples):** `pa_trading_range_score_{30,60}`, `pa_range_*_{30,60}`, `pa_failed_breakout_down_*`, `bull_reversal_bar`, wicks, `range_efficiency_30`, `vwap_cross_count_30`, `atr_like_20`.
- **Entry:** range score + close in lower third + confirm (reversal / failed break / wick) + min range width (ATR) + optional strong-bear block.
- **Stops / targets:** `range_low` / `signal_low` / `atr_buffer`; `fixed_r` / `range_mid` / `upper_third`.
- **YAML:** `src/strategies/parameters/pa_trading_range_bls_hs.yaml`, focused `src/strategies/testing_parameters/pa_trading_range_bls_hs_focused.yaml`.

### pa_failed_range_breakout_trap

- **Family:** `pa_range_breakout_failure`.
- **Purpose:** Trap after **failed rolling-range** breakdown — **not** ORB failure template.
- **Features:** `pa_range_high/low`, `pa_breakout_down`, `pa_failed_breakout_down`, `pa_close_back_inside`, `pa_followthrough_down`, `pa_trading_range_score`, `bull_reversal_bar`, `atr_like_20`.
- **Entry:** failed-break or inside+reversal proxy; block strong follow-through down; optional TR regime filter.
- **Stops / targets:** `failed_extreme` / `range_low_buffer` / `signal_low`; `fixed_r` / `range_mid` / `range_high`.
- **YAML:** `parameters/pa_failed_range_breakout_trap.yaml`, `testing_parameters/pa_failed_range_breakout_trap_focused.yaml`.

### pa_tight_channel_pullback

- **Family:** `pa_channel_pullback`.
- **Purpose:** With-trend pullback in **tight bull channel** per `pa_tight_bull_channel_score_*` — not ORB/VWAP core plugins.
- **Features:** tight bull score, `pa_pullback_depth_atr_*`, `pa_climax_score_*`, range columns, `bull_reversal_bar`, `close_near_high`, `vwap`, `atr_like_20`.
- **Stops / targets:** `pullback_low` / `signal_low` / `atr_buffer`; `fixed_r` / `range_high`.
- **YAML:** `parameters/pa_tight_channel_pullback.yaml`, `testing_parameters/pa_tight_channel_pullback_focused.yaml`.

### pa_mtr_reversal

- **Family:** `pa_major_trend_reversal`.
- **Purpose:** Coarse **bear → bull** reversal after prior bear channel + test of low / failed break — long-only MVP.
- **Features:** `pa_tight_bear_channel_score_*`, `pa_failed_breakout_down_*`, `pa_prior_low/high`, `pa_wedge_push_count_*`, range columns, `bull_reversal_bar`, `atr_like_20`.
- **Stops / targets:** `major_low` / `signal_low` / `atr_buffer`; `fixed_r` / `prior_swing_high`.
- **YAML:** `parameters/pa_mtr_reversal.yaml`, `testing_parameters/pa_mtr_reversal_focused.yaml`.

**Loader:** `src/strategies/loader.py` registers all four (**29** strategies total). **`metadata.yaml`** entries include `conflict_group: QQQ_directional` and cost sensitivity hints.

## 4. Tests

| Test file | Role |
|-----------|------|
| `tests/test_pa_features_no_lookahead.py` | Prior high / parity vs manual roll; no LOOKAHEAD in PA strategies; feature_key / columns |
| `tests/test_pa_strategy_registration.py` | load, validate default + focused merge, `supports_fast`, keys |
| `tests/test_pa_*_signal.py` (×4) | Synthetic feature rows → valid long geometry + negative controls |
| Parity CLI | `pa_batch_a_parity_smoke.{md,csv}` |
| Jan sweep | `pa_batch_a_jan2025_smoke.{md,csv}` |

## 5. Known limitations

- Long-only MVP; coarse scores; no centered pivots; no advanced delayed pivots.
- **Jan 2025 smoke:** two strategies had **no trades** on the evaluated combo slice (see smoke CSV) — expect to validate signal rate on longer Layer 1 windows.

## 6. Next recommended step (exactly one)

**`RUN_PA_BATCH_A_LAYER1_2023_2024`**

**Rationale:** full **`pytest`** green; **`compileall`** OK; loader lists **29** strategies; fast **parity** clean for all four PA names + **`failed_orb`** regression; **`required_features`** contain **no LOOKAHEAD**; Jan smokes **completed** (exit 0) with non-empty sweep result CSVs; unit tests demonstrate signal paths. Sparse Jan fills for two strategies are a **research** follow-up, not a parity failure.

## 7. Explicit non-runs

- Formal **Layer 1** PA Batch A 2023–2024 **not** executed in this commit without separate user approval.
- **Layer 2**, **mini-WFO**, **full WFO**, **live/paper** — not run.
