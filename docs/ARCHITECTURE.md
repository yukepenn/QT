# QT target architecture

Layers (target):

1. **data** — bars IO + validation  
2. **features** — no-lookahead columns  
3. **strategies** — raw candidate signals  
4. **execution** — canonical fills / exits / PnL (`src/execution/`, including `materialize.py` + `path.simulate_trade_path`)  
5. **management** — exit-plan templates  
6. **backtest** — single-strategy adapter (`run_strategy_backtest`); Layer 1 **grid sweep** placeholder at `src/backtest/sweep.py` (`--legacy` → `legacy/sweep_legacy.py`)  
7. **combiner** — candidate arbitration (legacy Numba sim re-exported explicitly from `combiner/legacy/` until execution-backed adapter)  
8. **router** — permission / quality (scaffold)  
9. **walkforward** — Layer 3 harnesses (orchestration; not canonical until combiner uses execution)  
10. **portfolio** — sizing / equity helpers (scaffold)  
11. **research** — thin runners only  
12. **utils** — cross-cutting helpers  

See **`docs/LAYER_FLOW.md`**, **`docs/CANONICAL_SWEEP_DESIGN.md`**, **`docs/CANONICAL_COMBINER_DESIGN.md`**, **`docs/LEGACY_RESULTS_POLICY.md`**.

Legacy accounting code is isolated under `**/legacy/**` with explicit CLI flags (`--legacy` sweep) and thin shims for transition.
