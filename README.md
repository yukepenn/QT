# QT — QQQ 1-minute RTH intraday research framework

## 1. What QT is

QT is a **local, research-only** codebase for studying **QQQ 1-minute regular-trading-hours (RTH)** intraday strategies using historical IBKR-style bars.

- **Research-only:** offline backtests, sweeps, and diagnostics — not live trading, not broker execution, and not a profitability claim.
- **Symbol focus:** QQQ is the primary complete dataset in this repo; treat other symbols as experimental unless coverage is explicitly verified.

## 2. Current architecture

| Layer | Role |
|-------|------|
| **Data / features / strategies** | Parquet ingest, feature builders, `BaseStrategy` plugins, YAML parameters + sweep grids |
| **Layer 1** | Per-strategy candidate sweeps; curated YAMLs under `src/research/results/layer1_*` |
| **Layer 2** | Combiner research (multi-candidate systems, cost-aware summaries) — **no production “smart router”** in the combiner |
| **Layer 3** | Fixed-profile smoke / stability / OOW-style checks under `src/walkforward/` + `src/research/results/layer3_*` |
| **Playbook Router Research Cycle** | Metadata-driven router / quality / exit-overlay **design** artifacts under `src/research/results/playbook_router_research_cycle_v1/` |
| **Local-only row diagnostics** | Detailed trade-context replay builds a **local-only** `trade_context_panel.csv` (gitignored); committed outputs are **aggregate CSV/MD only** |

Deeper indexes: `PROJECT_STATUS.md`, `src/research/results/RESULTS_INDEX.md`, `src/combiner/results/RESULTS_INDEX.md`.

## 3. Current Champion v0 (frozen)

| Profile | Role | Candidates |
|---------|------|------------|
| `pa_only_mtp1_meta` | **CLEAN_BASELINE** | `PA_BUY_SELL_CLOSE_TREND_003` |
| `pa_gap_mtp2_meta` | **DEFAULT_COMBINED** | PA + `GAP_ACCEPTANCE_FAILURE_001` |
| `primary_mtp2_meta` | **BREADTH_REFERENCE_ONLY** | PA + GAP + `CCI_EXTREME_SNAPBACK_003` |

Champion v0 is **long-only, intraday-only**, and treated as a **frozen benchmark** for research comparisons — not a promoted production system.

## 4. Current active research direction

- **Do not** keep polishing Champion v0 parameters.
- **Do** refine **offline** router filters + trade-quality scoring using the decision-time panel (still no combiner wiring).
- **Likely next high-edge increment:** **exit overlay diagnostics** (trend swing / runner style behaviors) once router/quality evidence is “good enough” or plateauing.
- **Scalp / short:** remain **roadmap-only** until dedicated branches exist with explicit non-goals and gates.

Latest offline refinement cycle: `src/research/results/router_quality_refinement_v2/`.

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

- Full / mini / reduced **walk-forward** automation runs (unless explicitly re-approved in a handoff).
- **Live / paper** trading, **SPY-first** research, or **broad Layer 2** sweeps as a default loop.
- **Production regime router** wiring inside the combiner, **hard** regime filters, or **short** execution paths.
- Editing **selected candidate YAMLs** or **strategy signal semantics** during router/quality research cycles.

---

**Handoff / status:** `NEXT_HANDOFF.md`, `PROJECT_STATUS.md`, `CHANGES.md`, `PROGRESS.md`  
**Artifact policy detail:** `docs/ARTIFACT_POLICY.md` (if present)
