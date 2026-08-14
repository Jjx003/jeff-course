# Hints

Work in TODO order. Get the non-causal three-way comparison printing `True`
before you touch the causal branch — the causal path reuses the same recurrence
and only adds masking, so debugging both at once wastes time.

## Getting the naive path right first

Everything else is checked against this, so it has to be boring and correct:

```python
scores = (q @ k.transpose(-1, -2)) / math.sqrt(head_dim)
shifted = scores - scores.amax(dim=-1, keepdim=True)
weights = torch.exp(shifted)
probs = weights / weights.sum(dim=-1, keepdim=True)
return probs @ v
```

`q @ k.transpose(-1, -2)` broadcasts over the leading `(batch, heads)`
dimensions, so no reshaping or `einsum` is needed. If your output shape is not
`(2, 4, 256, 64)`, you transposed the wrong pair of axes.

Check it against `scaled_dot_product_attention` before writing anything else. If
those two do not agree, nothing downstream will.

## The three running statistics

Shapes are the whole battle. Per query tile:

```python
running_max   = torch.full((batch, heads, rows, 1), float("-inf"))
running_denom = torch.zeros((batch, heads, rows, 1))
accumulator   = torch.zeros((batch, heads, rows, head_dim))
```

The trailing `1` on the first two is what makes `running_denom * correction`
and `accumulator * correction` broadcast without any index arithmetic. Reductions
that feed them keep `keepdim=True` for the same reason.

## The update, one line at a time

```python
new_max = torch.maximum(running_max, scores.amax(dim=-1, keepdim=True))
correction = torch.exp(running_max - new_max)
probs = torch.exp(scores - new_max)

running_denom = running_denom * correction + probs.sum(dim=-1, keepdim=True)
accumulator = accumulator * correction + probs @ v_block
running_max = new_max
```

Two things to notice. `probs` is exponentiated against `new_max` directly, not
against a tile-local maximum, which saves a rescale of the new tile. And
`running_max = new_max` must come *last*: assign it early and `correction`
becomes `exp(0) = 1`, which silently disables the rescaling and gives you an
answer that is right only when the maxima happen to be non-increasing.

## Causal tile classification

Use absolute positions, not positions within the tile:

```python
q_index = torch.arange(q_start, q_end).unsqueeze(-1)   # (rows, 1)
k_index = torch.arange(kv_start, kv_end).unsqueeze(0)  # (1, cols)
scores = scores.masked_fill(k_index > q_index, float("-inf"))
```

The mask broadcasts against the trailing two dimensions of a
`(batch, heads, rows, cols)` score block, so it does not need the batch or head
axes.

The two boundary conditions are easy to get off by one. The tile is entirely in
the future when its first key is past the last query row, `kv_start > q_end - 1`.
It needs a mask when its last key is past the first query row,
`kv_end - 1 > q_start`. With a query tile of 64 and a KV tile of 64 you should
skip exactly 6 of 16 pairs and mask exactly 4 of them.

## Common mistakes

- Rescaling the denominator but not the accumulator. Everything looks plausible
  and the output is wrong by whatever factor the maxima drifted.
- Normalizing inside the tile loop. The accumulator must stay unnormalized until
  every tile is merged.
- Assigning `running_max = new_max` before computing `correction`.
- Initializing `running_max` to `0.0` instead of `-inf`. This is invisible on
  data with positive scores and wrong on data without.
- Merging a fully masked tile instead of skipping it. Its maximum is `-inf`, so
  `running_max - new_max` becomes `-inf - (-inf) = nan` and the NaN propagates
  through every subsequent tile.
- Using `scores.max(dim=-1)` and forgetting it returns a `(values, indices)`
  tuple. `amax` returns a tensor.
- Dropping `keepdim=True`, after which the correction broadcasts along the wrong
  axis and silently produces the wrong shape rather than an error.
- Writing `scores * (1.0 / math.sqrt(d))` in one implementation and
  `scores / math.sqrt(d)` in the other. They differ in the last bit, which
  muddies the comparison you are trying to make.
- Building a full mask tensor of shape `(seq, seq)` inside the tiled loop. That
  reintroduces the $L^2$ allocation the exercise is about, even if the score
  block stays small.

## Sanity checks

- `output shape` is `(2, 4, 256, 64)` and `output dtype` is `torch.float32`.
- `softmax scale (1/sqrt(head_dim))` is `0.12500` — head_dim 64 gives exactly
  1/8.
- Non-causal: `KV tiles computed: 4`, `KV tiles skipped: 0`.
- Causal: `tile pairs total: 16`, `computed: 10`, `skipped: 6`,
  `fraction of tile pairs skipped: 0.3750`.
- All six comparison lines print `allclose: True` and
  `max abs diff < 1e-05: True`.
- `full score matrix bytes: 2097152` and `one KV tile of scores bytes: 524288`,
  a reduction of `4.0x`.
- The sweep ends at `L=65536 full=131072.0 MiB tiled=128.0 MiB
  reduction=1024.0x`.

On stderr you should see the exact differences at roughly `5e-07`. If yours are
around `1e-03`, you have a real bug, not rounding — most likely a missing
rescale. If they are exactly `0.0` for the `tiled vs naive` pair, check that
your tiled function is not quietly calling the naive one.

## About the tolerance

The comparison uses `torch.allclose(a, b, rtol=1e-5, atol=1e-6)` plus a separate
`max abs diff < 1e-5` check.

Both are chosen against float32's machine epsilon of about $1.19 \times 10^{-7}$.
The attention outputs are convex combinations of standard-normal value vectors,
so their entries are $O(1)$ in magnitude, which makes one ulp roughly $10^{-7}$.
Summing 256 terms in two different orders, with rescalings in between, should
cost a small number of ulps. A tolerance of $10^{-6}$ absolute is a handful of
ulps: tight enough that a genuine algorithmic error cannot slip through — a
missing rescale is a *relative* error of $e^{\Delta m}$, which is orders of
magnitude larger — and loose enough that it does not fail on a machine with a
different BLAS or thread count.

The measured differences land near $5 \times 10^{-7}$, which is inside the
threshold but not by an enormous margin, and that is the honest picture: this is
reduction-order noise, not agreement to the bit. The same magnitude separates
`naive` from `scaled_dot_product_attention`, neither of which is your code.

That is also why the exact difference goes to stderr instead of stdout. It is a
real measurement, but it depends on the host's reduction order, so it cannot be
part of a byte-stable graded output.

## Reading the timings

The stderr timings are the part most likely to be misread. On the reference run:

```text
[measured] naive attention: 0.484 ms
[measured] tiled attention (python loop): 1.215 ms
[measured] scaled_dot_product_attention: 0.314 ms
```

Your tiled implementation is roughly two to three times *slower* than the naive
one, and the ratio moves around between runs. This is
expected and it is not a bug in your code. The naive path is two big BLAS
matmuls; yours is the same arithmetic chopped into small matmuls with Python
loop overhead and fresh tensor allocations on every iteration, and in PyTorch
every tile's intermediate still goes to main memory and back.

Tiling buys memory. Turning it into speed requires fusing the loop into one
kernel so the statistics stay in registers, which is what
`scaled_dot_product_attention` does and what your Python loop cannot. Absolute
numbers will vary on your machine; the ordering should not.

## Going deeper

- Set `KV_TILE` to `256` and confirm the tiled path degenerates to the naive one
  in a single tile, with the difference dropping toward zero.
- Set `KV_TILE` to `8` and watch the differences stay at the same order of
  magnitude. Tile size is a memory and scheduling knob, not an accuracy knob.
- Multiply one query row by a large constant so its raw scores reach the
  hundreds. Both stable paths are unaffected; delete the max subtraction from
  `naive_attention` and `torch.exp` overflows to `inf`, and `inf / inf` gives
  NaN.
- Increase `SEQ` to 4096 and time both paths again. The memory table stops being
  hypothetical.
- Add a query-tile loop to the non-causal path and confirm the output is
  unchanged. Real kernels tile both axes to parallelize over query blocks.
- Try `torch.backends.cuda.sdp_kernel` or `torch.nn.attention.sdpa_kernel` to
  force a specific backend and see which one your shapes actually dispatch to.

## References

- Milakov and Gimelshein, *Online normalizer calculation for softmax* (2018),
  arXiv:1805.02867 — the single-pass softmax recurrence this lab implements,
  derived before it was attached to attention.
- Rabe and Staats, *Self-attention Does Not Need $O(n^2)$ Memory* (2021),
  arXiv:2112.05682 — shows that the memory bound follows from chunked
  accumulation alone.
- Dao, Fu, Ermon, Rudra, and Ré, *FlashAttention: Fast and Memory-Efficient
  Exact Attention with IO-Awareness* (2022), arXiv:2205.14135 — the IO-aware
  fused kernel that made the recurrence fast as well as small.
- Dao, *FlashAttention-2: Faster Attention with Better Parallelism and Work
  Partitioning* (2023), arXiv:2307.08691 — better work partitioning and fewer
  non-matmul operations, and where the causal tile-skipping accounting is made
  explicit.
