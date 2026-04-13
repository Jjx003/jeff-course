# Theory: Statistics and Cost Estimation

## Why the Optimizer Needs Cardinality Estimates

A query optimizer's job is to pick the *cheapest* plan from an exponential space of
alternatives.  "Cheapest" means fewest tuples flowing through the tree — fewer tuples
means fewer I/Os and less CPU work.  Without numbers, the optimizer is guessing.
Cardinality estimation turns guessing into arithmetic.

The key insight: **we do not need exact counts, we need relative ordering**.  If filter A
produces 100 rows and filter B produces 10,000, it does not matter that both estimates are
off by 20 % — we still know to apply A first.

## Equi-Width Histograms

The simplest per-column statistic is an **equi-width histogram**.  Split the column's
value range $[min, max]$ into $B$ equal-width buckets.  For each bucket $i$ covering
$[lo_i, hi_i)$, record a tuple count $c_i$.

Bucket width: $w = (max - min) / B$

Given a value $v$, its bucket index is $\lfloor (v - min) / w \rfloor$.  Lookup is $O(1)$.

For this module we use a degenerate histogram with a single bucket, which reduces to
knowing only $min$, $max$, and the number of distinct values $NDV$.

## Selectivity Formulas

**Equality** ($col = v$): assume values are uniformly distributed across $NDV$ distinct values.

$$sel_{EQ} = \frac{1}{NDV}$$

**Less-than** ($col < v$): fraction of the range below $v$.

$$sel_{LT} = \frac{v - min}{max - min + 1}$$

**Greater-than** ($col > v$): symmetric.

$$sel_{GT} = \frac{max - v}{max - min + 1}$$

**Inclusive variants** ($\leq$, $\geq$): shift by one unit.

$$sel_{LEQ} = \frac{v - min + 1}{max - min + 1}, \quad sel_{GEQ} = \frac{max - v + 1}{max - min + 1}$$

All results are clamped to $[0, 1]$.

## Cost Model

We use a simplified *cardinality-as-cost* model:

| Node  | Cost formula |
|-------|-------------|
| SCAN  | $num\_tuples$ |
| FILTER | $sel \times cost(child)$ |
| JOIN (nested-loop) | $cost(left) \times cost(right)$ |

The join formula models a naive nested-loop join where every left tuple is paired with
every right tuple.  Real optimizers add I/O cost terms and distinguish hash joins, but the
structure is the same.

## Reality Check

The uniform-distribution assumption breaks the moment data is skewed.  A column storing US
state codes is anything but uniform — California has 10× more rows than Wyoming.
Real systems address this with:

- **Denser histograms** (more buckets = better approximation)
- **Most-Common-Values (MCV) lists** — track the top-$k$ values exactly, use the histogram
  for the rest (this is what PostgreSQL does)
- **Multi-column statistics** — correlated columns (city, state) require joint histograms
- **Sampling** — scan a random 1 % of the table at ANALYZE time and extrapolate

Cost estimation is an active research area.  Getting it wrong by even 2× can cause the
optimizer to choose a plan that is orders of magnitude slower.
