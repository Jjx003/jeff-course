# Theory: Join Operators

## Join Algorithms

A join combines rows from two relations where a predicate holds. The three classical physical join algorithms are:

| Algorithm | Time | Space | Best for |
|-----------|------|-------|----------|
| Nested-loop join | $O(N \cdot M)$ | $O(1)$ | Tiny inputs, arbitrary predicates |
| Hash join | $O(N + M)$ | $O(N)$ for build | Equality joins on large tables |
| Sort-merge join | $O(N \log N + M \log M)$ | $O(N + M)$ (or $O(1)$ if pre-sorted) | Equality joins, already sorted, merge-sorted output |

---

## Nested-Loop Join (NLJ)

```
for each outer (left) tuple L:
    for each inner (right) tuple R:
        if join_pred(L, R): emit (L, R)
```

$O(N \cdot M)$ comparisons. For 1 million × 1 million tables: $10^{12}$ comparisons — catastrophic.

**Block NLJ**: read the outer in chunks that fit in the buffer pool. Inner is scanned once per outer chunk rather than once per outer row. Reduces I/O from $O(N \cdot M / B)$ to $O(N \cdot M / B^2)$ where $B$ is the buffer pool size.

NLJ is appropriate when the inner table fits in the buffer pool (pin it and loop) or when the join condition is non-equality (hash join doesn't apply).

---

## Hash Join

**Build phase**: scan the **smaller** (left) relation; hash each row on the join key into an in-memory hash table.

**Probe phase**: scan the **larger** (right) relation; for each row, look up the join key in the hash table. Emit all matches.

Time: $O(N + M)$. Space: $O(N)$ for the hash table — must fit in memory for the simple case. When it doesn't (skewed data, large relations), use **Grace hash join**: partition both relations to disk by hash, then join each partition pair independently.

PostgreSQL's hash join uses Grace; DuckDB uses partitioned hash join with SIMD probing. Both dominate NLJ for large equality joins.

---

## Build Side Selection

Always build on the **smaller** relation. The optimizer estimates cardinality (number of rows after filters) for each input and chooses accordingly. A wrong build-side choice doubles memory usage and may spill to disk unnecessarily.

---

## Output Schema

When two relations are joined, the output tuple has all columns from both. This is a **horizontal concatenation** of the two byte arrays. The output schema is the union of both schemas with adjusted offsets.

For index-nested-loop join (a variant), the inner relation is accessed via an index — the outer row's key is looked up in a B+ tree, and matching inner rows are retrieved directly. This reduces $O(N \cdot M)$ to $O(N \cdot \log M)$ — a huge win for selective joins.

---

## Pipelining vs. Materialisation

NLJ and hash join differ in when they materialise:

- **NLJ**: inner is re-scanned for every outer tuple. To avoid repeatedly hitting disk, the inner is pinned in the buffer pool (no materialisation needed if it fits).
- **Hash join**: build side is **fully materialised** into the hash table before the probe begins. This breaks the pipeline but enables O(1) probing.

In a fully pipelined query plan, hash join is a **pipeline breaker**: nothing flows through it until the build phase completes. This is why query planners carefully decide where to place hash joins to minimise pipeline breaks.
