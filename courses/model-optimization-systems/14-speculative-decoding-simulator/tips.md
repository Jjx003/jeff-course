# Hints

## Implementation hints

- Sum powers `acceptance ** i` for `i` from 1 through `draft_length`.
- Add one fallback token to the committed-token estimate.
- Compute cost as `1 + draft_length * draft_cost`.
- Return `committed / cost`.
- Use the requested formatting exactly; the expected output is deterministic.

## Sanity checks

Before worrying about the starter scenarios, check the shape of your function:

- If `acceptance` increases, speedup should increase.
- If `draft_cost` increases, speedup should decrease.
- If `draft_length` increases while acceptance is high, speedup may increase.
- If `draft_length` increases while acceptance is low, speedup may flatten or
  even become unattractive.

For `draft_length = 0`, a generalized version of the formula would give speedup
1. This starter may not include that case, but it is a useful mental anchor.

## Debugging formatting

If your math looks right but the grader disagrees:

- Check whether the output is rounded to the same number of decimals.
- Check scenario order.
- Check labels and punctuation.
- Check that you did not print extra debugging lines.

## Going deeper

After the exercise, try modifying a local copy with a dynamic draft-length rule:

```text
if recent_acceptance > 0.85: draft 6
elif recent_acceptance > 0.65: draft 4
else: draft 2
```

That still is not production serving, but it captures an important idea: the
best speculative policy adapts to the request stream.
