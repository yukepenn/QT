# Side-flip / inverse diagnostic — design

## Why negative R does not imply inverse profitability

- **Path dependence:** realized R depends on the sequence of stops, targets, partial fills, and session exits.
- **Target/stop asymmetry:** long-only research configs do not mirror a short book by sign flip alone.
- **Max-hold / EOD exits:** flattening rules are not symmetric for a hypothetical opposite position.
- **Slippage / limits:** limit-touch and gap behavior break naive sign symmetry.

## What we ran in v1

The combiner exposes **no** supported “invert side” replay flag. The shipped artifact is a **`non_executable_sign_proxy`**: `side_flip_proxy_total_r = -total_r` on **existing fixed-profile aggregate rows** (`side_flip/side_flip_metrics.csv`).

## What this proves vs does not prove

| Claim | Supported? |
|-------|--------------|
| “If we flipped signs on the same path-dependent PnL stream we would earn +X R” | **No** (not simulated) |
| “Aggregate long profile R was negative in window W” | **Yes** (from fixed-profile CSV) |
| “Negating headline R is a bookkeeping identity” | **Yes** (trivial) |

## Production / research boundary

- **Not** production short support.
- **Not** evidence that contrarian shorts exist in this codebase.
- Any future short research needs **explicit strategy + risk model**, not combiner sign hacks.
