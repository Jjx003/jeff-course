# Theory: Predicate Pushdown

## The Query Optimiser's Job

A SQL query specifies **what** to compute, not **how**. The optimiser's job is to choose the physical execution plan that computes the same result with minimum cost. It does this in two phases:

1. **Logical optimisation** (rule-based): rewrite the logical plan to an equivalent but cheaper form. Predicate pushdown is the most impactful rule.
2. **Physical optimisation** (cost-based): choose physical operators (e.g., hash join vs. sort-merge join) based on estimated cardinality and I/O cost.

---

## Why Predicate Pushdown Reduces Cost

Without pushdown:
```
Filter [emp.id > 1000]
  Join
    Scan(employees, 10^6 rows)
    Scan(departments, 10^3 rows)
```
The join produces up to $10^6 \times 10^3 = 10^9$ intermediate rows before the filter discards 99.9% of them.

With pushdown:
```
Join
  Filter [emp.id > 1000]     ← executes first
    Scan(employees, 10^6 rows)  → ~1000 rows
  Scan(departments, 10^3 rows)
```
The join now processes $10^3 \times 10^3 = 10^6$ rows — a 1000x reduction in join input. The filter is applied as close to the data source as possible, reducing the cardinality of every operator above it.

This is the **relational algebra equivalence**: $\sigma_{p}(A \bowtie B) = \sigma_{p}(A) \bowtie B$ when $p$ references only $A$.

---

## Rule-Based vs. Cost-Based Optimisation

**Rule-based** (always apply if the rule fires):
- Predicate pushdown
- Projection pushdown (eliminate unused columns early)
- Constant folding (`WHERE 1 = 1` → remove filter)
- Join reordering (for some simple cases)

**Cost-based** (apply only if estimated cost improves):
- Join reordering for multi-way joins (dynamic programming over join orders)
- Physical operator selection (hash join vs. NLJ vs. sort-merge)
- Index vs. table scan selection

PostgreSQL uses both. Its rule-based phase fires ~50 rules; then the cost-based planner uses dynamic programming to find the optimal join order. The two phases are cleanly separated.

---

## Plan Tree Representation

A logical plan is a tree of **relational algebra operators**:
- $\sigma$ (sigma): selection (filter)
- $\pi$ (pi): projection
- $\bowtie$ (bowtie): join
- Scan: base table access

Rewrites transform one tree into an equivalent tree. The equivalences come from the laws of relational algebra (commutativity, associativity, distributivity of selection over join).

---

## Cascading Rewrites

One rule application may enable another. After pushing a filter below a join, the filter may now be adjacent to another join it can pass through. Real optimisers apply rules in a fixed-point loop: keep applying until no rule fires. For this module, a single recursive pass is sufficient.
