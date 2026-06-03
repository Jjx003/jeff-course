# Hints and Going Deeper

## Hints

- The helper functions should accept one item dictionary at a time.
- Do not round inside `utilization`, `months_to_clear_backlog`, or `constraint_score`; round only when formatting output strings.
- Python's `sorted()` accepts a `key` function that can return a tuple. Use negative values for descending numeric sorts.
- `summarize_top_constraints` should return strings, not print them.

## Going deeper

- Try changing the score weights after passing the exercise. Which bottlenecks move up or down?
- Add a `policy_risk` field and decide whether it should be a separate score or part of `strategic_weight`.
- Think about whether capacity should be measured in wafers, packages, racks, megawatts, or revenue. The right unit depends on the question.
