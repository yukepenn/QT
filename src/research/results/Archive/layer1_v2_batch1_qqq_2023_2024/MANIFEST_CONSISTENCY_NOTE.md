# Layer 1 v2 Batch 1 — manifest consistency (QQQ 2023–2024)

**Date:** 2026-05-09

After commit `281cc4a`, a background sweep could rewrite `sweep_manifest.csv` / `sweep_manifest.md` with new timestamps or absolute `sweep_folder` paths while leaving `selected_candidates.csv` and YAMLs stale.

**Action taken:** Working tree was compared to `HEAD` (`281cc4a`). There was **no** unstaged diff on `sweep_manifest.csv`, `sweep_manifest.md`, `selected_candidates.csv`, or `candidate_summary.md`, so **no `git restore` was required**. Canonical tracked artifacts remain aligned.

**Policy:** If future runs change only manifest paths/timestamps and candidates are unchanged, restore manifests from the last known-good commit and record that here. If manifest `results_csv` paths change materially, rerun `select_candidates.py` from the current manifest and regenerate the full candidate bundle (Case B).
