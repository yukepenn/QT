# Side-flip diagnostic (non-executable)

`side_flip_proxy_total_r` is **−total_r** from the fixed-profile combiner replay CSV. It is **not** a replay of inverted stops/targets or mirrored limit logic. Do not treat as production short evidence.

## Read-through on indicator mtp1/2/3

For every window, the proxy mirrors the sign of the realized long profile `total_r`. Where the long profile was **positive** on 2023–2024 (`insample_ref`), the proxy row is **negative** by construction. That algebraic flip **does not** describe an executable contrarian strategy and **does not** validate a “short the bundle” hypothesis.

## Verdict

**Inverse hypothesis not supported** for production or research promotion beyond bookkeeping curiosity. Any future contrarian work needs explicit short mechanics and a different simulator contract.
