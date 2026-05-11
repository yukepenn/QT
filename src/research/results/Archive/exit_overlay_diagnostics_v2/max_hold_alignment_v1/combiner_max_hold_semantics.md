# Combiner max_hold semantics (audit)

Read-only audit of **`src/combiner/simulator.py`**. Production code was **not** modified in this task.

## Order of evaluation on each bar (long, in position)

For bar index `i` with `i >= entry_idx` and `side == 1`:

1. **Intrabar stop / target** using that bar’s **low / high** vs `stop_px` / `tgt_px`.
   - If **both** stop and target print in-range, **`EX_STOP` wins** (same as clone `stop_first` on ambiguous touch).
2. **Only if no exit yet (`exr == 0`)** and `max_hold_m > 0`: compute **`bars_held = i - entry_idx + 1`**. If **`bars_held >= max_hold_m`**, set **`EX_MAX_HOLD`** with **`raw_ex = clo`** (bar **close**) and apply long exit slip via `_numba_exit_px` / `_py_exit_price`.
3. **EOD**, **session end**, **end of data** — each gated on `exr == 0` in the same iteration, after max_hold.

### Numba-style reference

```423:460:src/combiner/simulator.py
        if i >= entry_idx:
            if side == 1:
                hit_stop = lw <= stop_px
                hit_tgt = hi >= tgt_px
                if hit_stop and hit_tgt:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _numba_exit_px(side, raw_ex, slip)
                elif hit_stop:
                    exr = EX_STOP
                    raw_ex = stop_px
                    ex_price = _numba_exit_px(side, raw_ex, slip)
                elif hit_tgt:
                    exr = EX_TARGET
                    raw_ex = tgt_px
                    ex_price = _numba_exit_px(side, raw_ex, slip)
            else:
                ...
        if exr == 0 and max_hold_m > 0:
            bh = i - entry_idx + 1
            if bh >= max_hold_m:
                exr = EX_MAX_HOLD
                raw_ex = clo
                ex_price = _numba_exit_px(side, raw_ex, slip)
```

### Python-loop mirror

```972:1009:src/combiner/simulator.py
        if i >= entry_idx:
            if side == 1:
                hit_stop = lw <= stop_px
                hit_tgt = hi >= tgt_px
                ...
        if exr == 0 and max_hold_m > 0:
            bh = i - entry_idx + 1
            if bh >= max_hold_m:
                exr = EX_MAX_HOLD
                raw_ex = clo
                ex_price = _py_exit_price(side, raw_ex, slip)
```

## Terminal max_hold bar vs intrabar

On the bar where **`bars_held` first reaches `max_hold_m`**, the combiner still evaluates **stop/target first** on that bar’s range. If neither fires, it exits **max_hold at the close** of that bar (plus slip). So **max_hold does not preempt intrabar stop/target** on the terminal bar.

## bars_held and exit index

At exit, trade log uses **`t_ex[tc] = i`** (exit bar index) and **`t_bh[tc] = i - entry_idx + 1`**, i.e. **inclusive bar count from entry bar**.

## Panel `exit_reason=max_hold`

The combiner semantics above imply **`max_hold` is only labeled if no intrabar stop/target fired on any bar up to and including the exit bar** under the simulator’s OHLC and price levels. Therefore, if a **research replay** hits stop/target on an **earlier** bar index than `panel_exit_idx` while the panel still says **`max_hold` at `exit_idx`**, that is **not** explained by “terminal bar max_hold first” — it indicates **path / materialization divergence** (different effective entry, stop/target, bar alignment, or panel trace limits), not the terminal ordering rule alone.

## Structured CSV

See `combiner_max_hold_semantics.csv` for a compact machine-readable summary.
