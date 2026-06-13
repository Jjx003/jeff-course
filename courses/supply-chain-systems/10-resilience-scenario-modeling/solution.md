# Solution Walkthrough

The baseline expected loss is probability multiplied by impact.

For an applicable mitigation, residual expected loss is:

```python
baseline * (1 - risk_reduction)
```

The net value then subtracts the mitigation's annual cost from the expected-loss reduction.

Only the alternate port routing has positive simple expected value in this data. The other mitigations may still be justified if they protect strategic customers, prevent existential loss, or satisfy regulatory requirements, but the simple expected-value argument alone is not enough.
