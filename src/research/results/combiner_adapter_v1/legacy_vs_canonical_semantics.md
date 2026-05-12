# Legacy vs canonical semantics (known differences)

| Topic | Legacy (Numba reference) | Canonical adapter v1 |
|-------|---------------------------|-------------------------|
| Entry timing | Matrix-driven intrabar competition | Signal bar `b`, entry `b+1` open via `simulate_trade_path` |
| Rejections | Rich `REJ_*` codes | Minimal; invalid intents skipped |
| `recompute_target` flag | Honored in legacy | Ignored; execution materializes fixed-R at entry |
| Multi-candidate same bar | Full Numba arbitration | `choose_highest_priority` on competing valids |
| Parity | Baseline for research | **Not expected** yet — label `PARITY_NOT_RUN` until harnessed |
