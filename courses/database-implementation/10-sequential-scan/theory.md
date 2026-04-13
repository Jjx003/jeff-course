# Theory: Sequential Scan Executor

## The Volcano (Iterator) Model

Proposed by Graefe in 1994, the **Volcano model** (also called the **iterator model** or **pull model**) organises query execution as a tree of operator iterators. Each operator implements three methods:

```
Init()  — open the operator, reset state
Next()  — produce the next output tuple (or nullptr)
Close() — release resources
```

The top-level operator (e.g., the query's output) calls `Next()` repeatedly until it gets `nullptr`. Each `Next()` call may recursively call `Next()` on children operators.

```
Output
  └─ Filter (id > 2)
       └─ SeqScan (employees)
```

When `Output` calls `Filter.Next()`, `Filter` calls `Scan.Next()` until it gets a tuple that passes `id > 2`, then returns that tuple.

### Why pull-based?

- **Pipelining**: tuples flow one at a time from scan to filter to output — no full materialisation of intermediate results.
- **Composability**: every operator has the same interface; new operators can be added without changing existing ones.
- **Simplicity**: easy to reason about single-tuple semantics.

### Disadvantages

- **Function call overhead**: one virtual dispatch per tuple per operator.
- **Poor cache behaviour**: control flow bounces between operators rather than staying in one tight loop.
- **No vectorisation**: SIMD requires processing multiple tuples at once.

Modern systems (DuckDB, Velox) use **push-based** (Morsel-driven) or **vectorised** (column-at-a-time) execution to amortise these costs. But Volcano is still the dominant model for OLTP systems (PostgreSQL, MySQL) where latency per query matters more than throughput.

---

## TableHeap

A **heap file** is the simplest table storage format: an unordered collection of pages, each containing tuples in insertion order. No sorting, no clustering.

Heap files are the default storage structure in PostgreSQL (`pg_class` with `relkind='r'`). They are simple and fast for writes but require a full scan for queries without an index.

The scan starts at page 0, visits every slot on every page, and returns non-deleted tuples. With an index, the executor uses `IndexScan` instead — but `SeqScan` is the baseline.

---

## Predicate Evaluation

A predicate is a boolean function over a tuple. In the Volcano model, `SeqScanExecutor` applies the predicate to each candidate tuple and skips non-matching ones. This is called **selection** (σ in relational algebra):

$$\sigma_{\text{id} > 2}(\text{employees})$$

In an optimised executor, the predicate is inlined into the tight scan loop. In Volcano, it's a `std::function<bool(Tuple&)>` passed at construction time — flexible but incurs a virtual dispatch per tuple.

---

## Comparison to Push Model

In a **push-based** model (used by Hyper, LLVM-JIT engines), the scan pushes tuples into a pipeline of operators. Each pipeline is compiled to a tight loop with no virtual calls:

```cpp
// Push-based scan pseudo-code (compiled)
for (auto& page : heap) {
    for (auto& tuple : page) {
        if (id > 2) {        // predicate inlined
            output(tuple);   // continuation inlined
        }
    }
}
```

The result: no function call overhead, no virtual dispatch, fully vectorisable. DuckDB generates this pattern via its morsel-driven parallel execution engine.
