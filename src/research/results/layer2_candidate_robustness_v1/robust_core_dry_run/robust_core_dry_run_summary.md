# Robust core dry-run

**Status:** PASS (research-only manifest; **not** a production candidate root)

**Gate rationale:** thresholds met

**KEEP_CORE candidates:** 10

**Families represented (KEEP_CORE):**

```
audit_family
opening_trap    4
pa              4
indicator       2
```

**Caveats:**

- `GAP_ACCEPTANCE_FAILURE_001`–`004` replay with **identical** window metrics in this audit — treat as **one effective signal family** for diversity planning.
- Dry-run uses the same singleton combiner envelope as the audit (`layer2_fixed_vwap_mtp2.yaml` default).
