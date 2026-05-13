# Checkpoint / resume design

Real-symbol sweeps with `--output-root`, non-`--dry-run`, and without `--no-save` emit **`sweep_results_partial.csv`** (atomic temp+replace) and **`sweep_progress.json`** after each checkpoint interval (`--checkpoint-every`, default **1**). **`--resume`** skips `combo_id` rows already present in the partial CSV. On full completion the partial CSV is **removed**; final **`sweep_results.csv`** is written by the existing CLI writer. See **`checkpoint_resume_design.csv`**.
