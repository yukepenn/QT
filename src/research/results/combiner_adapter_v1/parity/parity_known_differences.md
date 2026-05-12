# Known differences before parity harness

- Sequential canonical adapter does not reproduce every legacy rejection branch.
- Legacy uses combined matrix simulation; canonical walks selected trades one-by-one.
- Do not force canonical to match legacy bugs; document diffs per bar when parity harness runs.
