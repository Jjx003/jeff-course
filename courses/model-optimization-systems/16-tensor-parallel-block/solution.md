# Solution walkthrough

## The whole trick is two chunk calls

`shard_columns` is `torch.chunk(w, tp, dim=0)` and `shard_rows` is `dim=1`.
Everything else in the module is arranging for those two cuts to compose. The
composition rule is worth internalizing as a grammar: a column-parallel layer
*produces* sharded activations, a row-parallel layer *consumes* them, and any
elementwise operation may sit between the two for free. An all-reduce is
required exactly where a sharded producer meets a consumer that needs the full
vector — which in a transformer layer happens twice, immediately before each
norm.

## Why the ledger is part of the solution

The `CommLedger` is eight lines, and it changes what the program *is*: without
it, `tp_mlp` is a slow way to compute an MLP; with it, the program states a
falsifiable claim — this block communicates `12288` payload bytes in exactly
one collective — and the assertions hold the claim to account. Real TP stacks
carry the same discipline as NCCL debug counters and profiler traces. The
habit of making communication countable is most of what "distributed systems
engineer" means in inference work.

## The certificate is the interesting test

The fp32 `allclose` check would have passed for a subtly wrong implementation
that, say, dropped one rank's partial on inputs where that partial happened to
be small. The integer/float64/ReLU run closes that loophole: every partial is
integer-valued, every sum is exact, and `torch.equal` gives a yes/no answer
with no tolerance to hide behind. Once it prints `True`, the fp32 residual is
*attributable* — the only difference between the paths is summation order —
and the standard error model bounds it at $O(n \cdot 2^{-24})$ for the
1024-term reduction, comfortably inside `1e-5`.

This move — port the computation to a domain where arithmetic is exact, then
test for equality — is reusable far beyond TP. Module 4 used it for bit
packing; module 12 used exact block-content equality for the paged cache. It
is the cheapest strong test in numerical systems work.

## The wrong cut fails loudly here and silently in production

`wrong_cut_mlp` returns a tensor of the right shape with a relative error of
`0.4299`. Nothing crashes. In a real serving stack, this bug class appears
when someone shards a layer whose structure they misread — a gated MLP where
the gate and up projections were chunked inconsistently, a fused QKV weight
split at the wrong offsets — and the model does not error; it just gets
mysteriously worse. The defense is exactly this lab's structure: an unsharded
reference and an equivalence test in CI, run on every parallelism
configuration you ship.

## Reading the cost table

The table's last column — `1.86x, 3.47x, 6.12x` — is the honest sales pitch
for tensor parallelism. Two structural facts:

- The collective term (1.6 ms) is constant while the memory term shrinks, so
  efficiency falls monotonically: 93%, 87%, 77%. Extrapolate to TP 16 over
  InfiniBand ($\alpha$ roughly 3×) and the marginal GPUs buy under 2 ms
  against nearly 5 ms of communication — which is why nobody does that.
- The table charges $\alpha$ but not the bandwidth term, because at batch 1
  the payload is 16 KB and the wire time is nanoseconds. At prefill the same
  table would need the bandwidth term and the conclusion flips toward "TP
  scales fine." Always ask which regime a scaling number was measured in.

One more thing the table quietly teaches: the TP 1 row is fictional (140 GB
does not fit on one 80 GB GPU), so every real speedup claim for this model has
a baseline problem. The defensible comparisons are between deployable
configurations — TP 2 INT4 versus TP 8 BF16 — and those trade quality, cost,
and latency rather than sitting on one axis.
