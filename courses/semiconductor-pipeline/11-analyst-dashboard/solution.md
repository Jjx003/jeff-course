# Solution Walkthrough

The solution keeps each metric in its own helper so the ranking logic is easy to audit.

## Metric helpers

`utilization(item)` divides demand by effective capacity. `months_to_clear_backlog(item)` divides backlog by monthly clearance rate. Neither helper rounds the result, because rounding inside model logic can change rankings near ties.

`constraint_score(item)` applies the exercise weights:

$$
0.55u + 0.30b + 0.15s
$$

where $u$ is utilization, $b$ is backlog months, and $s$ is strategic weight.

## Ranking

The ranking key is:

```python
(-constraint_score(item), -utilization(item), item["name"])
```

The negative signs turn score and utilization into descending sorts. The name stays positive so ties are stable and alphabetical.

## Formatting

The summary function returns strings rather than printing. This makes the helper testable and lets `main()` decide how to display the dashboard. Numeric fields use `:.2f`, which gives deterministic output for grading.
