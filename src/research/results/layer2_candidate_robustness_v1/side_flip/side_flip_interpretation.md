# Side-flip diagnostic (non-executable)

`side_flip_proxy_total_r` is **−total_r** from the fixed-profile combiner replay CSV. It is **not** a replay of inverted stops/targets or mirrored limit logic. Do not treat as production short evidence.

## Read-through on indicator mtp1/2/3

For every window, the proxy mirrors the sign of the realized long profile `total_r`. Where the long profile was **positive** on 2023–2024 (`insample_ref`), the proxy row is **negative** by construction. That algebraic flip **does not** describe an executable contrarian strategy and **does not** validate a “short the bundle” hypothesis.

## Verdict

**Inverse hypothesis not supported** for production or research promotion beyond bookkeeping curiosity. Any future contrarian work needs explicit short mechanics and a different simulator contract.

## Full-audit note (2026-05-11)

After **66 / 66** singleton replays, **`ANTI_PREDICTIVE_CANDIDATE`** expanded to **five** YAMLs (**`MACD_MOMENTUM_TURN_003`** plus **`MULTI_DAY_LEVEL_TRAP_001`–`004`**). These belong on a **research** queue only — see `future_side_flip_watchlist.csv`. **No** new side-flip combiner runs were **required** for this v1 completion; the existing non-executable proxy remains sufficient.

## Anti-predictive candidates (research queue)

These are **not** production shorts. Any executable side-flip diagnostic would be a **future** task.

- `MACD_MOMENTUM_TURN_003`
- `MULTI_DAY_LEVEL_TRAP_001`
- `MULTI_DAY_LEVEL_TRAP_002`
- `MULTI_DAY_LEVEL_TRAP_003`
- `MULTI_DAY_LEVEL_TRAP_004`
