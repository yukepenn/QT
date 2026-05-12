# QT — QQQ 1-minute RTH intraday research framework

## 1. What QT is

QT is a **local, research-only** codebase for studying **QQQ 1-minute regular-trading-hours (RTH)** intraday strategies using historical IBKR-style bars. **Repo-local `data/raw/ibkr/`** holds a **small committed** set of 1m equity bar shards (QQQ + SPY) for reproducible smoke and parity; do not point research runners at external `D:\` roots when a repo-local path suffices.

- **Research-only:** offline backtests, sweeps, and diagnostics — not live trading, not broker execution, and not a profitability claim.
- **Symbol focus:** QQQ is the primary complete dataset in this repo; treat other symbols as experimental unless coverage is explicitly verified.

## 2. Target architecture (reset in progress)

The codebase uses a **single reference execution accounting layer** under `src/execution/` (including **materialization** of entry fill, initial risk, and targets from raw `TradeIntent`, plus **`min_risk_per_share`** rejection and scale-out sizing on **remaining** quantity). The **backtest** package provides `run_strategy_backtest` (reference single-strategy adapter) and a **Layer 1 sweep** entrypoint (`python -m src.backtest.sweep`): **`--smoke`** runs a deterministic synthetic grid; **`--validate-pipeline`** checks wiring without accounting. Historical Numba sweep/backtest code lives under **`archive/legacy_backtest/`** (not imported by mainline). **Layer 2 combiner** supports **`--engine legacy`** / **`legacy_reference`** (lazy-loaded archived Numba under **`archive/legacy_combiner/`**) and **`--engine execution_backed`** (alias **`canonical`**) via `simulate_combiner_canonical` → `src.execution.path.simulate_trade_path` (same-session next-bar entry, cooldown cleared on new session in `state`); default CLI token remains **legacy** for compatibility. **Real QQQ slice parity** (repo-local `data/raw/ibkr`, Jan 2024) is recorded under `src/research/results/combiner_adapter_parity/` (dual-engine smoke + drift classification). Post-hardening smoke notes: `src/research/results/execution_backed_hardening/`.

| Layer | Role |
|-------|------|
| **data** | Load, normalize, validate bars (`src/data/`) |
| **features** | No-lookahead columns (`src/features/`) |
| **strategies** | Raw candidate signals (`src/strategies/`) |
| **execution** | Canonical fills, exits, PnL (`src/execution/`) |
| **management** | Exit-plan templates (`src/management/`) |
| **backtest** | Single-strategy adapter; Layer 1 sweep **synthetic + real-symbol MVP** (`src/backtest/`) |
| **combiner** | Candidate arbitration — **`legacy_reference`** Numba vs **`execution_backed`** adapter (`src/combiner/`) |
| **router** | Permission / quality scaffold (`src/router/`) |
| **walkforward** | Layer 3 harnesses; default combiner engine may remain **`legacy_reference`** in some callers until explicitly migrated (`src/walkforward/`) — repo-local **execution_backed** real smoke is documented under `combiner_adapter_parity/` |
| **portfolio** | Sizing / equity helpers (`src/portfolio/`) |
| **research** | Thin runners and curated results only (`src/research/`) |
| **utils** | Config / IO / validation (`src/utils/`) |

Design references: `docs/ARCHITECTURE.md`, `docs/MODULE_OWNERSHIP.md`, `docs/LAYER_FLOW.md`, `docs/EXECUTION_SEMANTICS.md`, `docs/SIGNAL_CONTRACT.md`, `docs/BACKTEST_SWEEP_DESIGN.md`, `docs/CANONICAL_COMBINER_DESIGN.md`, `docs/LEGACY_RESULTS_POLICY.md`, `docs/MAINLINE_LEGACY_SURGERY_PLAN.md`, `docs/ACCOUNTING_BOUNDARY_REVIEW.md`, `docs/EXECUTION_TEST_MATRIX_SUMMARY.md`.

### Smoke check (Layer 1 + execution)

- Run `python scripts/canonical_execution_smoke.py` (synthetic OHLC) and `python -m pytest -q` before resuming strategy research.
- Run `python -m src.backtest.sweep --smoke` to exercise the canonical sweep + `run_strategy_backtest` path without QQQ parquet.
- Run `python -m src.backtest.sweep --validate-pipeline --strategy <name>` for metadata-only wiring checks; add `--symbol` / `--start` / `--end` / `--data-root` for full pipeline validation when local parquet exists.
- Trailing, exit order, scale fill policy, and gross vs net R are documented in `docs/EXECUTION_SEMANTICS.md` and `docs/EXECUTION_TEST_MATRIX_SUMMARY.md`.

Prior Layer 1–3 research outputs and Champion benchmarks remain **historical priors** (see `docs/LEGACY_RESULTS_POLICY.md`), **not** current canonical truth for execution semantics until regenerated under `src/execution`.

## 3. Current Champion v0 (frozen)

| Profile | Role | Candidates |
|---------|------|------------|
| `pa_only_mtp1_meta` | **CLEAN_BASELINE** | `PA_BUY_SELL_CLOSE_TREND_003` |
| `pa_gap_mtp2_meta` | **DEFAULT_COMBINED** | PA + `GAP_ACCEPTANCE_FAILURE_001` |
| `primary_mtp2_meta` | **BREADTH_REFERENCE_ONLY** | PA + GAP + `CCI_EXTREME_SNAPBACK_003` |

Champion v0 is **long-only, intraday-only**, and treated as a **frozen benchmark** for research comparisons — not a promoted production system.

## 4. Current active direction

- **Primary:** finish the **architecture reset** — one execution engine, adapters, tests, and documentation — before resuming overlay or large research sweeps.
- **Do not** run WFO / mini-WFO / live / paper / SPY-first / broad Layer 2 grids as part of this reset unless explicitly re-scoped.
- **Scalp / short:** remain **roadmap-only** until explicit gates exist.

Recent research artifacts (e.g. exit overlay alignment) live under `src/research/results/` and are **diagnostic context** for the reset, not headline execution truth.

## 5. Artifact policy

| Committed | Not committed (local-only / gitignored) |
|-----------|------------------------------------------|
| Curated aggregate **CSV/MD**, review bundles, source maps, small validation CSVs | Raw `trades.csv`, row-level `trade_context_panel.csv`, `local_rows/**`, `local_runs/**`, sweep folders, `top_runs/`, logs, `.cache/`, parquet/npy/npz/memmap |

**Never** `git add .` for this repo class — stage paths explicitly.

## 6. How to review the repo

1. Start at **`NEXT_HANDOFF.md`** (operating context + validation snapshot).
2. Read **`PROJECT_STATUS.md`** for the current decision and scope boundaries.
3. Open the latest **result-root** `CHATGPT_REVIEW_BUNDLE.md` + `SOURCE_MAP.csv` (human navigation aids).
4. Prefer **summaries and small CSVs** over trying to interpret huge raw grids in GitHub’s CSV renderer.

## 7. Current non-goals

- Full / mini / reduced **walk-forward** automation runs during the architecture reset (unless explicitly re-approved in a handoff).
- **Live / paper** trading, **SPY-first** research, or **broad Layer 2** sweeps as a default loop.
- **Production regime router** wiring inside the combiner, **hard** regime filters, or **short** execution paths until execution parity is settled.
- Editing **selected candidate YAMLs** or **strategy signal semantics** except metadata needed for contracts.

---

**Handoff / status:** `NEXT_HANDOFF.md`, `PROJECT_STATUS.md`, `CHANGES.md`, `PROGRESS.md`  
**Artifact policy detail:** `docs/ARTIFACT_POLICY.md` (if present)
