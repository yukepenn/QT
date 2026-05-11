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

## Exit priority (intrabar evaluation order)

1. Stop / target (subject to ambiguity policy)
2. Scale-out rules (if enabled on `ExitPlan`)
3. Trailing stop trigger (if enabled)
4. Max hold
5. EOD / session close
6. End of data

## Max hold

- Counted from **entry bar** as bar index `0` along the held path.
- Evaluated **after** stop/target (and scale/trailing hooks) on each bar unless `ExecutionPolicy.max_hold_policy` specifies otherwise.

## PnL and R

- **Gross PnL/share:** price delta × side, before commission.
- **Net PnL/share:** gross − allocated commission / qty.
- **R multiple:** net PnL per share ÷ **initial risk per share** at entry (positive risk definition).
- **Multi-leg / partials:** total R = Σ `qty_frac_i × leg_r_i` with Σ `qty_frac_i = 1` after scaling.

## MFE / MAE

- Computed from the **observed intratrade path** using bar high/low relative to entry and side, without lookahead beyond the current bar.

## Invalid trades

- Invalid stop side → reject intent.
- Non-positive risk → reject intent.
- Missing target under `fixed_r` → reject unless explicit relaxed policy flags (default: reject).

## Canonicality

The **`src/execution/`** package is the **only** canonical implementation of these semantics for new code paths. Legacy Numba engines remain under `**/legacy/`** for transition only.
