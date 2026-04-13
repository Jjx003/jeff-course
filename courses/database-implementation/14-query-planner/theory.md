# Theory: Query Planner — Running Basic SELECT

## The Query Lifecycle

Every SQL statement you submit travels through a pipeline before the first result row
appears.  Understanding this pipeline is the difference between a DB user and a DB
engineer.

```
SQL text
  → Tokenizer  (break into words and symbols)
  → Parser     (build Abstract Syntax Tree)
  → Binder     (resolve names to catalog objects)
  → Logical Planner  (build operator tree)
  → Optimizer  (rewrite rules + cost-based choices)
  → Physical Planner (choose SeqScan vs IndexScan, NLJ vs HashJoin)
  → Executor   (drive the volcano iterator tree)
  → Results
```

In production systems each stage is thousands of lines of code.  Here we compress the
whole pipeline into a single file — without sacrificing the key abstractions.

## Why Separation of Concerns Matters

If the parser and executor are entangled, you cannot swap PostgreSQL's planner for a
learned cost model without rewriting the executor.  With clean stage boundaries you can:

- Plug in a new optimizer rule without touching execution code
- Replace SeqScan with a B+ tree scan by changing one factory function
- Test the parser in isolation with unit tests on the AST

This is not academic tidiness — it is the reason database internals can evolve over
decades without full rewrites.

## Volcano / Pull Model Recap

Each physical operator implements three methods:

| Method | Purpose |
|--------|---------|
| `Init()` | Open resources, initialize child operators |
| `Next()` | Return the next output tuple (or null if done) |
| `Close()` | Release resources |

Execution is demand-driven: the root calls `Next()`, which propagates down the tree.  The
leaf operator (SeqScan) pulls from storage; intermediate operators (Filter, Projector)
transform and forward tuples.  No intermediate results are materialized unless explicitly
requested (e.g., sort or hash join).

For this module we use an in-memory vector of rows, so `Init()` just resets an iterator
and `Next()` walks the vector.

## What a Real System Adds

This module deliberately omits:

- **Transactions and concurrency** — in a real system every read and write happens inside
  a transaction with locks or MVCC snapshots.  Without this, two concurrent queries can
  see inconsistent data.
- **Write-Ahead Log (WAL)** — crash recovery requires that every change is logged before
  it is applied to the data pages.  We skip this entirely.
- **Catalog** — a real binder resolves table and column names against a persistent system
  catalog.  We hard-code the schema.
- **Error handling** — malformed SQL should return a useful error message, not a crash.

Skipping these is fine for learning.  The important takeaway is that the parse →
plan → execute pipeline is the *skeleton* onto which all those features hang.
