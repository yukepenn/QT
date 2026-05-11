# In-sample sanity (2023–2024)

Compare `actual_*` to reference economics in `insample_sanity_metrics.csv`.
Tolerance: ~8% trades and ~3R total_r (see `sanity_pass` column).

If all rows show `NOT_RUN`, execute combiner replays under `local_runs/<profile>/insample_ref/` then re-run `postprocess`.
