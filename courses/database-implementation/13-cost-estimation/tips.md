# Tips: Statistics and Cost Estimation

- **Clamp selectivity to [0.0, 1.0]** — a predicate like `amount > 9999` on a column
  with max=999 should return 0.0, not a negative number.  Use
  `std::clamp(result, 0.0, 1.0)` or an explicit `if`.

- **Integer division is a silent killer** — `(val - min_val) / (max_val - min_val + 1)`
  is all-integer arithmetic if you forget to cast.  Always write
  `(val - min_val) / (max_val - min_val + 1.0)` or cast the numerator to `double` first.

- **EQ with num_distinct == 0** — guard against divide-by-zero explicitly; return `0.0`
  when NDV is zero.

- **JOIN cost blows up fast** — the nested-loop model multiplies cardinalities, so even
  moderate table sizes produce huge numbers.  This is exactly why real optimizers go to
  great lengths to avoid cross products and prefer index lookups.

- **`std::map` vs `std::unordered_map`** — `TableStats::columns` uses `unordered_map`
  for O(1) column lookup; the outer `all_stats` uses `std::map` (ordered) just to keep
  the interface deterministic.  Either would work in practice.

- **Output formatting** — use `std::fixed << std::setprecision(2)` to print costs with
  exactly two decimal places, matching the expected output.
