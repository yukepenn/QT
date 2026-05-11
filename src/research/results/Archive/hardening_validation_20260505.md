# Hardening validation — 2026-05-05 (Commit E)

Light validation only; **no** full Layer 1/2 reruns, **no** IBKR pull.

## Results

| Check | Result |
|--------|--------|
| `python -m pytest -q` | **64 passed** |
| `python -m compileall -q src` | **OK** (no errors) |
| `python src/strategies/loader.py --list` | **OK** — 10 strategies listed |
| QQQ `read_bars` smoke (2020-01, `--head 3`) | **OK** — 8190 rows in window, duplicates 0 |
| `build_features.py` smoke (QQQ, Jan 2020, ORB 15) | **OK** — `registry_validation=passed`, 137 final columns |
| `check_strategy_fast_parity.py` (`failed_orb`, 2 combos) | **OK** — `TOTAL_MISMATCH_FIELDS approx=0` |
| `combiner/run.py` smoke (`trap_family`, `--no-save`, Jan 2020) | **OK** — run completed, metrics printed |

## Boundary greps

| Command | Expected / actual |
|---------|-------------------|
| `rg "LOOKAHEAD" src/strategies` | **`src/strategies/strategy/base.py`** only — rejects `required_features` containing LOOKAHEAD (guard), not strategy YAML requiring those columns |
| `rg "_feat_key" src --glob "*.py"` | **No matches** — duplicate feature-key helpers removed from Python sources |
| `rg "FAILED_ORB_001|…" src/combiner/postprocess.py src/combiner/behavior.py` | **No matches** — no hardcoded candidate IDs in generic postprocess/behavior |
| `rg "data/raw" .gitignore` | **`data/raw/`** present — raw tree ignored |

*Recorded on Windows / Python 3.11.4.*
