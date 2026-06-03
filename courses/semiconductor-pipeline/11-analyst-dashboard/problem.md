# Build an Analyst Bottleneck Dashboard

Semiconductor analysts often translate qualitative stories into small quantitative screens. A screen does not replace judgment, but it helps ask sharper questions:

- Which supply-chain layer is running closest to capacity?
- Which layer has the longest backlog?
- Which constraint combines high utilization, long lead time, and high strategic importance?

In this exercise you will implement helper functions for a tiny embedded dataset. The output is deterministic and has no external dependencies.

## Your task

Open `starter/python.py` and complete these functions:

1. `utilization(item)`  
   Return `demand_units / capacity_units`.

2. `months_to_clear_backlog(item)`  
   Return `backlog_units / monthly_clear_rate`.

3. `constraint_score(item)`  
   Return a weighted score:

   $$
   0.55 \times \text{utilization}
   + 0.30 \times \text{months_to_clear_backlog}
   + 0.15 \times \text{strategic_weight}
   $$

4. `summarize_top_constraints(items, top_n=3)`  
   Rank items by descending `constraint_score`, then descending `utilization`, then ascending `name`. Return a list of formatted strings:

   ```text
   <rank>. <name> | util=<utilization>x | backlog=<months> mo | score=<score> | note=<note>
   ```

   Use two decimals for every numeric field.

## Dataset fields

Each dictionary has:

| Field | Meaning |
|---|---|
| `name` | Supply-chain layer being tracked |
| `capacity_units` | Monthly effective capacity in comparable units |
| `demand_units` | Monthly demand in the same units |
| `backlog_units` | Work waiting to be cleared |
| `monthly_clear_rate` | Realistic monthly backlog clearance rate |
| `strategic_weight` | Analyst judgment from 1.0 to 5.0 |
| `note` | Short qualitative reason |

## Expected behavior

The starter file includes a `main()` that prints:

- A header line.
- The top three constraints.
- Two diagnostic lines for selected layers.

Your completed solution should match `expected_output/python.txt` exactly.
