# Layer reachability — combiner_adapter_parity

| Path | Status | Notes |
|------|--------|--------|
| Layer1 backtest sweep smoke | **OK** | |
| Layer1 pipeline validation | **OK** | |
| Layer2 legacy_reference import | **OK** | Lazy archive load |
| Layer2 execution_backed import | **OK** | `adapter.simulate_combiner_canonical` |
| Layer2 execution_backed tiny synthetic | **OK** | `tests/test_combiner_adapter_parity.py` |
| Layer2 legacy tiny synthetic | **PARTIAL** | Same synthetic matrix: legacy may emit **0** trades vs execution **1** (see `parity/parity_summary.csv`) — drift catalogued, not hidden |
| Layer3 dry-run import | **OK** | `runner.py` imports `run_combiner_fixed_config` |
| Layer3 fixed-profile dry-run | **NOT_RUN** | Intentionally not executed (no mini-WFO / full smoke) |
| Exit overlay (execution path) | **PARTIAL** | Resume only after stronger matrix parity or harnessed real slices |
| Router integration | **BLOCKED** | Out of scope |

## Answers (task checklist)

1. **NotImplementedError on Layer2?** No — resolved in prior adapter commit; this pass adds explicit engines and stamps.
2. **execution_backed smoke possible?** Yes synthetically; real QQQ bars not present in repo CI paths → `smoke/NOT_RUN` unless user runs `--try-real-smoke` locally.
3. **Layer3 reach combiner?** Import path OK; default combiner engine remains **legacy_reference** for stability.
