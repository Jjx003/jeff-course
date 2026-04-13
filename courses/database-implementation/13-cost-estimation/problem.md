# Statistics and Cost Estimation

## Your Task

Build a statistics layer and cost model that the optimizer uses to reason about query plans.

### 1. Column and Table Statistics

```cpp
struct ColumnStats {
    int64_t min_val;
    int64_t max_val;
    size_t  num_distinct;
};

struct TableStats {
    size_t num_tuples;
    std::unordered_map<std::string, ColumnStats> columns;
};
```

### 2. Predicate Operator Enum

```cpp
enum class Op { EQ, LT, GT, LEQ, GEQ };
```

### 3. `Selectivity`

```cpp
double Selectivity(const TableStats& stats, const std::string& col, Op op, int64_t val);
```

Return the estimated fraction of tuples satisfying the predicate.  Use these formulas
(all results clamped to `[0.0, 1.0]`):

| Op  | Formula |
|-----|---------|
| EQ  | `1.0 / num_distinct` |
| LT  | `(val - min_val) / (max_val - min_val + 1.0)` |
| GT  | `(max_val - val) / (max_val - min_val + 1.0)` |
| LEQ | `(val - min_val + 1.0) / (max_val - min_val + 1.0)` |
| GEQ | `(max_val - val + 1.0) / (max_val - min_val + 1.0)` |

Edge cases:
- If `num_distinct == 0` for EQ, return `0.0`.
- If the column is not found in `stats.columns`, return `1.0` (assume no filtering).

### 4. Plan Node

```cpp
enum class NodeType { SCAN, FILTER, JOIN };

struct PlanNode {
    NodeType    type;
    std::string table_name;   // SCAN only
    std::string filter_col;   // FILTER only
    Op          filter_op;    // FILTER only
    int64_t     filter_val;   // FILTER only
    std::vector<PlanNode*> children; // 1 child for FILTER, 2 for JOIN
};
```

### 5. `EstimateCost`

```cpp
double EstimateCost(const PlanNode* node,
                    const std::map<std::string, TableStats>& all_stats);
```

| Node type | Cost |
|-----------|------|
| SCAN      | `stats[table_name].num_tuples` |
| FILTER    | `Selectivity(...) * EstimateCost(child)` |
| JOIN      | `EstimateCost(left) * EstimateCost(right)` |

### 6. Demo `main()`

Build the following scenario and print:

```
Table 'orders': 10000 tuples
Selectivity(amount > 500): 0.50
Selectivity(status == 1): 0.10
Plan cost (scan orders): 10000.00
Plan cost (filter amount>500): 5000.00
Plan cost (join orders x customers): 500000.00
```

**Setup:**
- Table `orders`: 10 000 tuples; column `amount` with min=0, max=999, NDV=1000;
  column `status` with min=0, max=9, NDV=10.
- Table `customers`: 1 000 tuples (no per-column stats needed for the demo).

**Plans to cost:**
1. SCAN over `orders`
2. FILTER `amount > 500` over SCAN `orders`
3. JOIN of (FILTER `amount > 500` over SCAN `orders`) × (SCAN `customers`)

## Constraints

- Compile with `g++ -std=c++20 -Wall -Wextra`.
- Use only the C++ standard library.
- No memory leaks: clean up all `PlanNode*` after use.
