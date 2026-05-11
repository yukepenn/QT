# Dry-run validation — local_detailed_trade_context_replay_v1

- git_tip: `92ba1fab0002929a9e6805ba896ef7c1a79a6567`
- planned_rows: **12**
- profiles: **3**
- windows: **4**
- context_windows: `20,30,60`
- decision_context_source: `signal_or_previous_bar`

## Policy
- Row-level outputs under `local_rows/**` are **local-only** (gitignored).
- Aggregates under `aggregates/**` are intended for commit.

