# PA / Brooks overlap — refinement backlog (2026-05-10)

**Phase policy:** no new plugins for concepts already owned by ORB / VWAP / gap / trap strategies. **This phase:** documentation only — **no** default-behavior changes to existing strategies.

| Brooks-style overlap | Owner strategy(ies) | Why not a new plugin | Suggested refinement (future) | Risk | Tests | Status |
|---------------------|----------------------|----------------------|-------------------------------|------|-------|--------|
| Opening reversal at S/R | `failed_orb`, `prior_day_level_trap`, PA batch | Maps to existing anchors | Tighter entry window aliases only if equivalent | Parity regression | `check_strategy_fast_parity` on owner | **Backlog** |
| First 18-bar ORB | `orb_continuation`, `orb_retest_continuation` | Core ORB family | None in PA branch | High | ORB parity suite | **Backlog** |
| ORB breakout pullback | `orb_continuation`, `orb_retest_continuation` | Same | Optional diagnostic columns only | Medium | ORB parity | **Backlog** |
| Failed opening breakout trap | `failed_orb` | Canonical owner | Alias flags only with default-off | **High** | failed_orb parity | **Backlog** |
| Prior close reclaim | `prior_close_reclaim` | Dedicated plugin | None | Medium | Owner registration | **Backlog** |
| Multi-day level trap | `multi_day_level_trap` | Dedicated plugin | None | Medium | Owner tests | **Backlog** |
| VWAP Brooks context | `vwap_reclaim_reject`, `vwap_trend_pullback`, `vwap_reversal` | VWAP family | `require_vwap_context` style flags on PA only (already separate) | Low | PA parity | **Backlog** |

**Explicit:** No duplicate ORB / VWAP / gap plugins were added in PA Batch B/C. **`pa_generic_breakout_pullback`** uses **rolling prior range**, not `orb_*` columns.
