# Layer reachability — combiner_adapter_parity (updated for repo-local real smoke)

| Path | Status | Notes |
|------|--------|--------|
| Layer1 backtest sweep smoke | **OK** | |
| Layer1 pipeline validation | **OK** | |
| Layer2 legacy_reference import | **OK** | Lazy archive load |
| Layer2 execution_backed import | **OK** | `adapter.simulate_combiner_canonical` |
| Layer2 execution_backed tiny synthetic | **OK** | `tests/test_combiner_adapter_parity.py` |
| Layer2 legacy tiny synthetic | **PARTIAL** | Toy matrix: legacy may emit **0** trades vs execution **1** (`parity/parity_summary.csv`) — catalogued |
| Layer2 execution_backed real smoke (`data/`) | **OK** | Jan 2024 QQQ; `smoke/real_execution_backed_smoke_summary.csv` |
| Layer2 legacy_reference real smoke (`data/`) | **OK** | Same slice; `smoke/real_legacy_reference_smoke_summary.csv` |
| Layer2 dual-engine real parity | **OK** | `REAL_PARITY_PASS_WITH_EXPLAINED_DIFFS` — `parity/real_data_parity_*` |
| Layer3 import | **OK** | `runner.py` imports `run_combiner_fixed_config` |
| Layer3 fixed-profile dry-run | **NOT_RUN** | Intentionally not executed (no mini-WFO / full smoke) |
| Layer3 default engine | **PARTIAL** | Some callers still default **`legacy_reference`** until explicitly switched |
| Exit overlay (execution path) | **OK** | Real smoke + row schema support resuming overlay diagnostics on execution-backed rows (research-only) |
| Router integration | **BLOCKED** | Out of scope |
| Future Layer1/2/3 rebuild around execution-backed PnL | **PARTIAL** | Credible path; incremental migration not started in this task |

## Checklist answers

1. **Is execution-backed Layer2 ready for future research?** **Yes** — repo-local real smoke passes; readiness label **`EXECUTION_BACKED_READY_FOR_RESEARCH`** (`execution_backed_readiness.md`).
2. **Is Layer3 still defaulting to legacy_reference?** **Partially** — imports use shared `run_combiner_fixed_config`; default `engine` argument may still read **`legacy`** token in some CLIs until callers opt in to **`execution_backed`**.
3. **Can we resume exit overlay on the execution path?** **Yes** — decision **`RESUME_EXIT_OVERLAY_ON_EXECUTION_PATH`** (`combiner_adapter_parity_decision.md`).
4. **Can we begin rebuilding Layer1/2/3 around execution-backed PnL later?** **Yes, incrementally** — not a blocker from this parity pass; follow-on work is separate from exit-overlay resume.
