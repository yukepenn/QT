# QT — QQQ 1-minute RTH intraday research framework

## 1. What QT is

QT is a **local, research-only** codebase for studying **QQQ 1-minute regular-trading-hours (RTH)** intraday strategies using historical IBKR-style bars.

- **Research-only:** offline backtests, sweeps, and diagnostics — not live trading, not broker execution, and not a profitability claim.
- **Symbol focus:** QQQ is the primary complete dataset in this repo; treat other symbols as experimental unless coverage is explicitly verified.

## 2. Target architecture (reset in progress)

The codebase is moving to a **single canonical execution accounting layer** under `src/execution/`. Backtest and combiner become **adapters** that build `TradeIntent` rows and call `execution.path.simulate_trade_path`; legacy Numba paths that duplicate fills/exits/R live under `**/legacy/` with import shims until parity migration finishes.

| Layer | Role |
|-------|------|
| **data** | Load, normalize, validate bars (`src/data/`) |
| **features** | No-lookahead columns (`src/features/`) |
| **strategies** | Raw candidate signals (`src/strategies/`) |
| **execution** | Canonical fills, exits, PnL (`src/execution/`) |
| **management** | Exit-plan templates (`src/management/`) |
| **backtest** | Single-strategy adapter (`src/backtest/`) |
| **combiner** | Candidate arbitration; must call execution (`src/combiner/`) |
| **router** | Permission / quality scaffold (`src/router/`) |
| **walkforward** | Harnesses only; no duplicate accounting (`src/walkforward/`) |
| **portfolio** | Sizing / equity helpers (`src/portfolio/`) |
| **research** | Thin runners and curated results only (`src/research/`) |
| **utils** | Config / IO / validation (`src/utils/`) |

Design references: `docs/ARCHITECTURE.md`, `docs/MODULE_OWNERSHIP.md`, `docs/EXECUTION_SEMANTICS.md`, `docs/SIGNAL_CONTRACT.md`, `docs/ARCHITECTURE_RESET_SUMMARY.md`.

Prior Layer 1–3 research outputs and Champion benchmarks remain **historical priors**, not canonical truth for execution semantics.

Deeper indexes: `PROJECT_STATUS.md`, `NEXT_HANDOFF.md`, `src/research/results/RESULTS_INDEX.md`, `src/combiner/results/RESULTS_INDEX.md` (where present).

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
