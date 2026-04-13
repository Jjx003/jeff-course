# Join Operators

## Your Task

Implement two join executors that both implement `AbstractExecutor`.

### `NestedLoopJoinExecutor`

```cpp
class NestedLoopJoinExecutor : public AbstractExecutor {
public:
    NestedLoopJoinExecutor(
        AbstractExecutor* left,
        AbstractExecutor* right,
        std::function<bool(const Tuple&, const Tuple&)> join_pred);
    void   Init()  override;
    Tuple* Next()  override;
    void   Close() override;
};
```

Algorithm:
1. On `Init()`: materialise the **left** side into a `std::vector<Tuple>`.
2. On each `Next()`:
   - Advance the right cursor; if exhausted, advance left cursor and reset right.
   - Call `join_pred(left_tuple, right_tuple)` on each pair.
   - Return the first matching pair as a **concatenated tuple** (left columns then right columns).
3. Return `nullptr` when all pairs exhausted.

### `HashJoinExecutor`

```cpp
class HashJoinExecutor : public AbstractExecutor {
public:
    HashJoinExecutor(
        AbstractExecutor* left,
        AbstractExecutor* right,
        std::function<int32_t(const Tuple&)> left_key_fn,
        std::function<int32_t(const Tuple&)> right_key_fn);
    void   Init()  override;
    Tuple* Next()  override;
    void   Close() override;
};
```

Algorithm:
1. On `Init()`: **build phase** — materialise left side; build `std::unordered_map<int32_t, std::vector<Tuple>>`.
2. On each `Next()`: **probe phase** — advance right side, look up `right_key_fn(right_tuple)` in the hash map. If hit, yield matches one at a time as concatenated tuples.
3. Return `nullptr` when probe exhausted.

### Concatenated tuple

For a join result, create a new `Tuple` whose `data_` is the left tuple's bytes followed by the right tuple's bytes. For printing, create a combined `Schema` with left columns then right columns.

## What to Print

Use two tables:
- **employees**: `id INT32, name VARCHAR` — rows: `(1, Alice), (2, Bob), (3, Carol)`
- **departments**: `emp_id INT32, dept VARCHAR` — rows: `(1, Eng), (2, Mkt), (2, Sales)`

Join condition: `employees.id == departments.emp_id`.

```
NestedLoopJoin (employees JOIN departments ON id=emp_id):
1 | Alice | 1 | Eng
2 | Bob | 2 | Mkt
2 | Bob | 2 | Sales

HashJoin (employees JOIN departments ON id=emp_id):
1 | Alice | 1 | Eng
2 | Bob | 2 | Mkt
2 | Bob | 2 | Sales
```

## Constraints

- Compile with `g++ -std=c++20 -Wall -Wextra`.
- Include the full Tuple/Schema/Value/TableHeap/SeqScanExecutor stack from module 10.
- Hash join result rows may appear in a different order than NLJ — that is acceptable.
