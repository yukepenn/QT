# Decision — combiner_adapter_parity (repo-local real smoke)

## Label (exactly one)

**`RESUME_EXIT_OVERLAY_ON_EXECUTION_PATH`**

## Rationale

- Repo-local **`data/raw/ibkr`** is audited, small, and safe to commit; QQQ bars load for the January 2024 smoke window (**8190** rows, **21** sessions).
- **`execution_backed`** real combiner smoke **passes** for Champion candidates (`PA_BUY_SELL_CLOSE_TREND_003` and two-candidate with `GAP_ACCEPTANCE_FAILURE_001`) with stable non-empty metrics and stamped semantics columns.
- **`legacy_reference`** runs the **same** slices successfully; dual-engine comparison is **`REAL_PARITY_PASS_WITH_EXPLAINED_DIFFS`** — identical trade counts, small **`total_r`** drift classified as **`execution_backed_design_choice`** (fill / path semantics), not silent adapter failure.
- **`execution_backed`** is suitable as the **future research accounting path**; exact legacy PnL parity is **not** required when differences are explained and bounded on real data.
- Naming discipline preserved: only **`src/research/results/combiner_adapter_parity/`** as the formal parity root — no `canonical_v2` / `combiner_adapter_v2` / `exit_overlay_v3`.

## Recommended next step

**Resume exit-overlay work using execution-backed combiner trade rows** (diagnostics / alignment harnesses), still **without** production router or production exit-management, **without** WFO or live trading.

## Explicit non-runs (this task)

No WFO, mini-WFO, live/paper, SPY research sweeps, broad Layer2 sweeps, Global Layer1, new strategies, Champion YAML edits, raw row-level trade panels, `top_runs` / `local_runs`, `git add .`, production router, production exit-management, scalp/short research.
