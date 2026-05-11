# Numba fastpath design (feature build) — **design only**

This document lists candidate Numba kernels **not** implemented in the feature-performance pass. Each must preserve **session boundaries** and **no lookahead** (shift / prior bar semantics unchanged).

| Kernel | Current pandas location | Expected benefit | Lookahead risk | Test focus | Priority |
|--------|-------------------------|------------------|----------------|------------|----------|
| `session_rolling_mean_shifted` | `volume.py` — `volume_ma_*_prior` | High (hot path every sweep) | Low if `shift(1)` kept outside rolling sum | First bar NaN per session; match `ratio` | **P1** |
| `session_rolling_std` | `volatility.py` — `ret_std_*` | Medium | Low (uses `ret_1m` only) | Match std vs pandas on fixture | **P1** |
| `session_rolling_max_min_shifted` | `price_action.py` — `rolling_high_*_prior` / `rolling_low_*_prior` | High | **High** if max/min include current bar — must mirror `.max().shift(1)` | Match second-bar prior high test | **P1** |
| `session_rolling_mean` (TR ATR) | `volatility.py` — `atr_like_*` | Medium | Low | Match `atr_like` | **P1** |
| `session_expanding_std` | `vwap.py` — `vwap_std` | Medium | Medium (expanding uses only past in session) | Match `vwap_z` distribution | **P2** |
| `session_vwap_cumsum` | `vwap.py` — cumulative PV / V | Medium | Low | First-bar VWAP vs typical price | **P2** |
| `vwap_persistence_shifted_mean` | `vwap.py` — `vwap_persistence_above/below_*` | Medium | Low (`shift(1)` after rolling mean) | NaN first bar; match persistence | **P2** |
| Bollinger / Donchian rolling | `channels.py` | Medium on wide configs | Medium | Golden vs pandas | **P2** |
| RSI / MACD / ADX | `indicators.py` | Medium | Medium–high (recursive warmups) | Strategy parity + small windows | **P3** |
| `pa_swing_prior_high_low` | `pa_swings.py` | High for PA-heavy grids | High — needs swing audit | PA regression + no-lookahead suite | **P3** |

## Recommendation

Ship **pandas concat batching** first (done in v1). Re-profile Global Layer 1 after rerun; if `feature_build` is still >50% of sweep wall time, prototype **P1** kernels behind a feature flag with strict parity tests.
