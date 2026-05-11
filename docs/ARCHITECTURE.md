# QT target architecture

Layers (target):

1. **data** — bars IO + validation  
2. **features** — no-lookahead columns  
3. **strategies** — raw candidate signals  
4. **execution** — canonical fills / exits / PnL (**new**)  
5. **management** — exit-plan templates  
6. **backtest** — single-strategy adapter  
7. **combiner** — candidate arbitration (calls execution)  
8. **router** — permission / quality (scaffold)  
9. **walkforward** — harnesses (orchestration)  
10. **portfolio** — sizing / equity helpers (scaffold)  
11. **research** — thin runners only  
12. **utils** — cross-cutting helpers  

Legacy accounting code is isolated under `**/legacy/**` with import shims for transition.
