# Execution semantics

**Version:** `execution_semantics: "1.0"`

## Bar convention

- Input bars are sorted ascending by timestamp, unique index, timezone-normalized (`ts_utc`).
- Strategy signal is evaluated on bar **`i`** (signal row aligned to decision bar).
- **Default entry:** next bar **`i + 1`** at **open** (unless `ExecutionPolicy.entry_timing` overrides in a future revision).

## Side convention

- **Long:** `+1`
- **Short:** `-1` (may be disabled via `ExecutionPolicy.allow_short`)

## Slippage and fills

Slippage is **per share**, applied **once** at each fill. Commission is **per round-trip trade** unless otherwise noted in policy.

| Event | Long fill | Short fill |
|-------|-----------|------------|
| Entry | `open + slip` | `open - slip` |
| Stop exit | `stop - slip` | `stop + slip` |
| Target exit | `target - slip` | `target + slip` |
| Time / EOD exit | `close - slip` | `close + slip` |

## Same-bar stop/target ambiguity

- Default: **`stop_first`** (`AmbiguityPolicy.STOP_FIRST`).
- `target_first` exists only for sensitivity analysis, not headline reporting.

## Exit priority (per bar, before advancing)

1. **Stop / target** (same-bar ambiguity via `ExecutionPolicy.same_bar_policy`; default `stop_first`).
2. **Trailing stop** using the level **carried in from the prior bar** only (see below).
3. **Scale-out** rules (touch-based trigger on favorable `high`/`low`). Raw exit price for the scale leg is set by `ExecutionPolicy.scale_fill_policy`:

   - **`close`** (default): bar **close** (conservative).
   - **`trigger_price`:** theoretical touch price at `entry ± trigger_r × risk` (then slippage applied).

4. **No-followthrough** (observed closes only; never overrides an earlier stop/target exit on the same bar because those are checked first).
5. **Max hold** (effective hold = `min(intent.max_hold_bars, exit_plan.max_hold_bars_cap)` when both set).
6. **EOD** (`minute_from_open >= eod_exit_minute`).
7. **End of data** (terminal close).

After a bar completes **without** a full exit, the engine **ratchets** the
trailing stop price using that bar’s range so it may trigger **starting on the
next bar**. The current bar’s favorable extreme **does not** tighten the trail
and then stop you on the **same** bar under this default (no trailing
lookahead).

## Targetless trades (`target_mode == "none"`)

No fixed profit target is materialized. Materialization requires a non–END_DATA-only exit path (trailing, max-hold on intent or plan cap, configured no-followthrough pair, or **active** EOD). For validation, EOD counts as active only when `eod_exit_minute < 500` (tests commonly use `999` to disable forced EOD for this check). Scale-out without trailing does **not** satisfy targetless validation by itself.

## Trailing (default conservative)

- **Check:** compare `low`/`high` to the trail stop computed from highs/lows
  **through the previous bar** (inclusive of entry through `t-1`).
- **Update:** after scale/NFT/max-hold/EOD checks, fold bar `t` into the best
  favorable price and move the chandelier trail for use on bar `t+1`.

## Scale-out vs stop same bar

If a stop and a scale-out **touch** would both occur, **stop / target** wins
first (step 1 before step 3).

## Max hold

- Counted from **entry bar** as bar index `0` along the held path.
- Evaluated **after** structured exits above on each bar unless
  `ExecutionPolicy.max_hold_policy` specifies otherwise.

## PnL and R

- **Gross PnL/share:** Σ `qty_frac_i ×` signed delta per share for each leg.
- **Net PnL/share:** gross − **one** `commission_per_trade / qty` allocation
  for the whole trade (partials do not each pay the full round-trip again).
- **`gross_r_multiple`:** Σ `qty_frac_i × leg_r_i` using per-leg fills (no commission in `leg_r`).
- **`net_r_multiple`:** `net_pnl_per_share / initial_risk_per_share`.
- **`r_multiple`:** alias of **`net_r_multiple`** for headline reporting.
- **Multi-leg / partials:** Σ `qty_frac_i = 1` after scaling.

## MFE / MAE

- Computed from the **observed intratrade path** using bar high/low relative to entry and side, without lookahead beyond the current bar.

## Invalid trades

- Invalid side → reject intent (`ExitReason.REJECTED` on `TradeResult`).
- Short when `allow_short=False` → reject.
- Non-positive risk → reject intent.
- Missing target under `fixed_r` → reject unless explicit relaxed policy flags (default: reject).
- **`target_mode == "none"`** without a valid management/time exit path (per materialization rules) → reject at materialization.

## Canonicality

The **`src/execution/`** package is the **only** canonical implementation of these semantics for new code paths. Legacy Numba engines remain under `**/legacy/`** for transition only.
