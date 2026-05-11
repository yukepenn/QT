# script_cleanup_inventory — router_quality_refinement_v2

| file | issue found | action taken | behavior changed | tests affected |
|------|-------------|--------------|------------------|----------------|
| `src/research/run_trade_quality_score_v2.py` | `json.dumps` used in `main()` but `import json` only under `__main__` | moved `import json` to module imports | **yes** (bugfix: module entry now works) | none added (existing diagnostics tests unaffected) |
| `src/research/run_local_trade_context_replay.py` | large but already structured; not minified | none | no | none |
| `src/research/run_offline_router_diagnostics.py` | readable | none | no | none |
| `src/research/build_trade_context_panel.py` | readable | none | no | none |
| `src/research/analyze_playbook_context.py` | readable | none | no | none |
| `src/research/run_router_quality_refinement_v2.py` | new runner | added | no (aggregate-only) | `tests/test_router_quality_refinement_v2.py` |
| `src/research/router_quality_refinement_v2_lib.py` | new pure helpers | added | no | `tests/test_router_quality_refinement_v2.py` |
