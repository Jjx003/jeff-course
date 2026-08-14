# Implement tiled attention with the online softmax recurrence

The previous reading argued that FlashAttention-style kernels compute *the same
math* as naive attention while moving far less data: stream blocks of keys and
values, keep small running statistics, never materialize the $L \times L$ score
matrix. That is a strong claim. "Exact up to floating-point rounding" is the
kind of sentence that is easy to write and easy to get wrong by one missing
rescale.

This lab makes you prove it. You will implement attention twice over real
multi-head tensors and check the streaming version against two independent
references, one of which is torch's own fused kernel.

The shapes are `(batch=2, heads=4, seq=256, head_dim=64)` with a KV tile of 64,
so every query row streams over 4 tiles. Everything runs on CPU in float32 with
seed 0 so your numbers match the grader's.

## Part 1 — Naive attention

Implement `naive_attention(q, k, v, causal=False)` the textbook way:

$$
\operatorname{scores} = \frac{QK^\top}{\sqrt{d}}, \qquad
P = \operatorname{softmax}(\operatorname{scores}), \qquad
O = PV
$$

Use the numerically stable softmax — subtract `scores.amax(dim=-1, keepdim=True)`
before exponentiating. When `causal` is set, mask every position where the key
index exceeds the query index with `float("-inf")` before the softmax.

This function deliberately allocates the full `(2, 4, 256, 256)` score tensor.
It is the thing the rest of the lab exists to avoid, and it is also the trusted
reference, so write it the obvious way and do not optimize it.

## Part 2 — Tiled attention

Implement `tiled_attention(q, k, v, kv_tile, q_tile, causal=False)`, which
returns `(output, tiles_computed, tiles_skipped)`.

For each query tile, initialize three running statistics per query row: a
running maximum $m = -\infty$, a running denominator $l = 0$, and an
unnormalized accumulator $O = 0$ of shape `(rows, head_dim)`. Then stream over
KV tiles. For each tile with scores $s$:

$$
m' = \max(m,\ \max_j s_j), \qquad
\alpha = e^{\,m - m'}, \qquad
p_j = e^{\,s_j - m'}
$$

$$
l \leftarrow \alpha l + \sum_j p_j, \qquad
O \leftarrow \alpha O + \sum_j p_j v_j, \qquad
m \leftarrow m'
$$

The same correction factor $\alpha$ rescales the denominator *and* the
accumulator. Divide by $l$ once, after the loop — never inside it.

The constraint that makes this exercise worth doing: the largest score tensor
you allocate is one `(rows, kv_tile)` block. If you find yourself concatenating
tiles, you have rebuilt the thing you were avoiding.

## Part 3 — Three-way equivalence

The program checks the tiled output against both `naive_attention` and
`torch.nn.functional.scaled_dot_product_attention`, and checks the two
references against each other. All three pairs must report `allclose: True`.

Two references rather than one is deliberate. If your tiled loop and your naive
loop share a bug — a wrong scale factor, a transposed argument — they will agree
with each other and disagree with `scaled_dot_product_attention`. A single
reference cannot catch a mistake you made twice.

Note what is printed and what is not. The exact max absolute difference between
two float32 attention outputs is a few ulps, and its precise value depends on
the BLAS reduction order of your machine, so it cannot be part of graded stdout.
The graded lines are a boolean `allclose` and a boolean threshold check; the
exact difference is written to **stderr**, which is streamed to you in the
session log but not graded. On the reference run those differences land around
`5e-07`.

## Part 4 — Causal masking

Add the causal path, verified against a causally masked `naive_attention` and
against `scaled_dot_product_attention(..., is_causal=True)`.

With a query tile of 64 and a KV tile of 64 over 256 positions, there are 16
tile pairs, and each falls into exactly one of three cases:

| Case | Condition | What to do |
|---|---|---|
| Entirely in the past | `kv_end - 1 <= q_start` | Compute with no mask |
| Straddles the diagonal | `kv_end > q_start + 1` | Apply a triangular mask |
| Entirely in the future | `kv_start > q_end - 1` | Skip the tile completely |

The third case is the point. A masked-out score contributes $e^{-\infty} = 0$ to
both the denominator and the accumulator, so a fully masked tile changes
nothing — computing it and then discarding it is pure waste. Your loop should
`continue` before touching the tile at all and count it in `tiles_skipped`. You
should see 10 computed and 6 skipped.

## Part 5 — Score memory, at this shape and asymptotically

Implement `score_bytes(batch, heads, seq, tile, element_size)`, returning the
bytes for the full `(batch, heads, seq, seq)` score matrix and for one
`(batch, heads, seq, tile)` block. Derive both from element counts and the real
`element_size` of the tensors, not from a hardcoded constant.

At this shape the full matrix is 2,097,152 bytes and one tile is 524,288 — a
factor of 4, which is just `seq / tile`. That is a small number, and it is
supposed to look unimpressive. The sweep underneath it is the actual argument:
holding batch, heads, and tile fixed, the full matrix grows as $L^2$ while the
tiled requirement grows as $L$.

Do not change the starter constants or the output labels. The grader checks
printed stdout.

## Recap

You have a streaming attention implementation that is numerically equivalent to
both the textbook version and a production fused kernel, a causal variant that
skips 37.5% of its tile pairs, and a memory table showing the score matrix going
from 128 GiB to 128 MiB at 64k context.

You will also notice, from the stderr timings, that your Python tiled loop is
*slower* than the naive version. That is the honest result and it is worth
sitting with: tiling is a memory optimization, and converting it into a speed
optimization requires a fused kernel, which is exactly what
`scaled_dot_product_attention` is.

The next module moves from computing attention to storing what attention reads:
KV-cache serving systems, paged attention, and prefix reuse.
