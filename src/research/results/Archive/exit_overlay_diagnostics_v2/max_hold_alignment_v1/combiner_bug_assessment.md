# Combiner bug assessment (max_hold_alignment_v1)

## Verdict

**No strong evidence of a production combiner bug from alignment alone.**

Dominant pattern: replay reaches **stop/target on a strictly earlier bar index** than `panel_exit_idx` while the panel labels **`max_hold`** at `exit_idx`.
That is consistent with **clone vs archived panel materialization drift** (entry bar, stop level, session bar alignment, or missing trace), 
or with **panel rows that are not byte-for-byte replayable** from published fields alone.

## Recommended follow-up (separate task if pursued)

- **`COMBINER_MAX_HOLD_SEMANTICS_AUDIT_FIX`** only if independent replay from combiner trade logs (not panel) confirms wrong `exit_reason` / `exit_idx` for these sessions.
