# Shard a transformer block with tensor parallelism

The reading claimed a specific piece of algebra: a transformer layer can be cut
across $p$ GPUs so that every weight matrix is sharded, no GPU ever holds a
full activation of the MLP's inner dimension, and the whole layer needs exactly
**two** all-reduces. This lab makes you build that cut and then prove all three
claims against an unsharded reference — including the strongest possible
version of "matches": bit-exact equality in exact arithmetic.

There is no cluster here. The "devices" are entries of a Python list, and the
collective is a function you write. That is not a limitation; it is the point.
Tensor parallelism is linear algebra plus bookkeeping, and every bug you can
write in it — wrong chunk axis, a nonlinearity applied to partial sums, an
extra collective — is visible on a CPU with four simulated ranks. The things a
real cluster adds (NCCL, streams, topology) change the constants, not the
algebra, and the analytic table at the end handles the constants.

## The shapes

A small GQA transformer block, sharded four ways:

- hidden 256, FFN 1024, so $W_\text{up}$ is $1024 \times 256$ and
  $W_\text{down}$ is $256 \times 1024$;
- 8 query heads and 4 KV heads of dimension 32, so each rank owns 2 query
  heads and 1 KV head — the same head-sharding arithmetic that makes TP 8 the
  ceiling for an 8-KV-head 70B model;
- batch 2, sequence 6, single forward pass, no cache.

Note the nn.Linear convention throughout: weights are stored
`(out_features, in_features)` and applied as `x @ W.T`. "Column parallel"
splits **output** features (dim 0 of the stored tensor); "row parallel" splits
**input** features (dim 1). Getting these two backwards is the classic first
bug, and the round-trip check catches it immediately.

## Part 1 — Sharding and the ledger

Implement `shard_columns`, `shard_rows`, and the `CommLedger`. The ledger's
`all_reduce` sums a list of per-rank partials and records the payload; its
`ring_bytes_per_gpu` converts payloads to wire traffic using the ring
all-reduce bound from the reading:

$$
\text{bytes per GPU} = \frac{2(p-1)}{p} \times \text{payload}
$$

For this block the payload is one activation tensor —
$2 \times 6 \times 256 \times 4$ bytes $= 12288$ — and the ring moves `18432`
bytes per GPU. Small numbers, but the accounting discipline is the deliverable:
a TP implementation that cannot say how many bytes it moved is not finished.

## Part 2 — The MLP, cut correctly

`tp_mlp` column-shards $W_\text{up}$, row-shards $W_\text{down}$, and calls
`all_reduce` exactly once. The composition works because the elementwise
nonlinearity never mixes columns:

$$
\sigma(XW_\text{up}^\top)W_\text{down}^\top
= \sum_{i=1}^{p} \sigma(XW_{\text{up},i}^\top)\,W_{\text{down}}^{(i)\top}
$$

The fp32 check `allclose(atol=1e-5)` passes, but notice what it cannot tell
you: whether the remaining $\sim 10^{-7}$ residual is summation-order rounding
(harmless) or a genuinely wrong cut that happens to be small on this input
(catastrophic). Part 3 separates those.

## Part 3 — The exact-arithmetic certificate

Run the same `tp_mlp` on integer-valued tensors in float64 with ReLU. Every
product and partial sum is an integer below $2^{53}$, so floating point is
exact, ReLU maps integers to integers, and **any** discrepancy between the
sharded and unsharded paths would survive to the `torch.equal` check
undamped. The check prints `bit-exact equal: True`: the cut itself is algebra,
and the fp32 residual in Part 2 is therefore rounding, not error. This is the
same certificate style as module 4's pack/unpack round-trip — move the test
into a domain where arithmetic is exact, and tolerance arguments disappear.

## Part 4 — Attention, and the full block

`tp_attention_block` shards heads: each rank projects with its column-shards
of $W_q, W_k, W_v$, runs causal attention over its **local** heads only (the
GQA broadcast stays on-rank: 2 query heads share 1 KV head), and applies its
row-shard of $W_o$ to produce a partial sum. One all-reduce. The full block —
attention plus MLP — then reports `all-reduces per layer: 2`, which is the
number the reading's 160-collectives-per-token claim is built from.

## Part 5 — The wrong cut, measured

`wrong_cut_mlp` does the tempting thing: row-shard $W_\text{up}$ so each rank
only needs a slice of $x$, apply GELU to each rank's partial pre-activation,
and sum afterwards. The result has a relative error of `0.4299` — not a
rounding-level disagreement but a 43-percent-of-norm different function,
produced by code that runs without any error and returns tensors of exactly
the right shape. The fix would be an all-reduce *before* the nonlinearity,
doubling the per-layer collectives; the column-then-row ordering exists to
avoid exactly that.

## Part 6 — What the collectives cost at scale

Finish `collective_cost_table`: the module-2 constants (140 GB of BF16
weights, 3.35 TB/s per GPU), 160 all-reduces per decode token at a fixed
10 µs each. The table lands at a `6.82` ms step floor for TP 8 — a `6.12x`
speedup on eight GPUs — with the gap entirely explained by the 1.6 ms
collective term that parallelism cannot shrink.

Do not change the starter constants or the output labels. The grader checks
printed stdout.

## Recap

You cut a transformer block across four simulated devices, proved the cut
exact in exact arithmetic, showed the layer needs exactly two all-reduces,
measured the 43-percent error of the plausible wrong cut, and priced the
collectives at 70B scale. The next module turns from making serving fast to
measuring whether it actually is: percentiles, TTFT and ITL, and the two ways
a load generator can lie to you.
