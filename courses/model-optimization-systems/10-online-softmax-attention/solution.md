# Solution walkthrough

## One identity does all the work

The recurrence looks like it has several moving parts, but it reduces to a
single fact: changing the reference point in a sum of exponentials multiplies
every term by the same constant.

$$
\sum_{i} e^{x_i - \mu'} = e^{\mu - \mu'} \sum_i e^{x_i - \mu}
$$

Because the constant factors out, it applies unchanged to the denominator
$\sum e^{x_i - \mu}$ and to the accumulator $\sum e^{x_i - \mu} v_i$. That is why
one `correction` variable is enough, and why applying it to only one of the two
is the bug everyone writes first — the result stays finite and plausible, and
the ratio $O/l$ is wrong by exactly the factor that was dropped.

In code the whole algorithm is six lines:

```python
new_max = torch.maximum(running_max, scores.amax(dim=-1, keepdim=True))
correction = torch.exp(running_max - new_max)
probs = torch.exp(scores - new_max)
running_denom = running_denom * correction + probs.sum(dim=-1, keepdim=True)
accumulator = accumulator * correction + probs @ v_block
running_max = new_max
```

Note that `probs` is exponentiated against `new_max` rather than a tile-local
maximum. The two-maximum formulation in most write-ups is equivalent, but it
applies the identity twice — once to the old state and once to the new tile —
where writing the new tile directly into the final frame only needs it once.

The `keepdim=True` calls are not stylistic. They keep `running_denom` at
`(batch, heads, rows, 1)` so that both the denominator update and the
`(batch, heads, rows, head_dim)` accumulator update broadcast against the same
`correction` tensor with no index arithmetic.

## Why two references instead of one

The program checks the tiled output against `naive_attention` *and* against
`scaled_dot_product_attention`, and the two references against each other.

A single reference only catches bugs you made once. Scale the scores by
$1/\sqrt{d}$ in neither implementation, or transpose the same wrong axis in
both, and a two-way check reports agreement. The third comparison —
`naive vs sdpa`, which involves none of the tiled code — is what pins the
reference itself to a known-good kernel.

## The tolerance and what it is measuring

`torch.allclose(rtol=1e-5, atol=1e-6)` with a separate `max abs diff < 1e-5`
threshold. float32 has a machine epsilon near $1.19 \times 10^{-7}$ and the
outputs are $O(1)$, so one ulp is about $10^{-7}$. The measured differences are
near $5 \times 10^{-7}$ — a few ulps, consistent with summing 256 terms in a
different order.

The important calibration is that this tolerance cannot hide a real error. A
missing rescale is not a rounding-scale mistake; it is a relative error of
$e^{\Delta m}$, where $\Delta m$ is however much the running maximum moved. On
this data that is orders of magnitude above $10^{-6}$.

The exact differences go to stderr, not stdout, for the same reason the timings
do: they depend on the host's BLAS reduction order and would make
`expected_output/python.txt` machine-specific. Notice that `naive vs sdpa`
disagree by the same order of magnitude as anything involving the tiled path.
Neither of those is student code. The disagreement is a property of float32
reduction order, not of the algorithm.

## Causal masking: three cases, and the one that matters

With a query tile of 64 and a KV tile of 64 over 256 positions, the 16 tile
pairs split into 6 skipped, 4 masked, and 6 computed with no mask at all.

Skipping the future tiles is the case worth being precise about. A masked score
of $-\infty$ contributes $e^{-\infty} = 0$ to both running sums, so computing a
fully masked tile and merging it is arithmetically harmless and completely
wasted. Worse, merging it is not even harmless in floating point: that tile's
maximum is $-\infty$, so `running_max - new_max` evaluates `-inf - (-inf)`, which
is NaN, and the NaN survives every subsequent tile. The skip is required for
correctness as written, not only for speed.

With $T$ tiles per axis the skipped fraction is $(T-1)/2T$, which is $0.375$ at
$T=4$ and approaches $1/2$ as sequences get long. Halving the work is why
production kernels take a mask *type* rather than a generic mask tensor: a
kernel handed an opaque `(L, L)` boolean tensor cannot prove a tile is entirely
masked without reading it.

## Memory: the small number and the real number

At the lab's shape the reduction is `4.0x`, which is just `seq / tile`. That is
supposed to look underwhelming. The argument is asymptotic, and the sweep makes
it concrete: at $L = 65536$ the full score matrix is 128 GiB and one tile is
128 MiB.

$L^2$ versus $L$ is the entire claim. Everything else about FlashAttention —
IO-awareness, register blocking, warp specialization — is engineering on top of
a recurrence whose only requirement is three running statistics per query row.

## The timings say tiling is slower, and that is correct

```text
[measured] naive attention: 0.484 ms
[measured] tiled attention (python loop): 1.215 ms
[measured] scaled_dot_product_attention: 0.314 ms
```

The tiled implementation is two to three times slower than the version it
replaces, run to run.
Nothing is wrong. Naive attention is two large BLAS matmuls; the tiled version
is the same arithmetic split into small matmuls, wrapped in a Python loop, with
a fresh allocation for every intermediate. Every tile's scores still travel to
main memory and back, so the tiling has given up vectorization without
collecting the locality it was meant to buy.

The locality only arrives when the tile loop lives inside one kernel and the
running statistics stay in registers and shared memory across iterations. That
is the difference between the recurrence and FlashAttention, and it is why
`scaled_dot_product_attention` beats both.

Stating this plainly matters, because the measurement is right there in the
session log. A walkthrough that implied the Python loop was fast would be
contradicted by the first run.

## What production kernels add

The recurrence you implemented is the core; a real kernel adds:

- tiling over query blocks as well as KV blocks, so query tiles run in parallel
  across streaming multiprocessors;
- tile sizes chosen against shared-memory capacity and tensor-core shapes rather
  than a round number;
- fused scaling, masking, and dropout so no intermediate is written out;
- a backward pass that recomputes tiles instead of storing probabilities,
  trading arithmetic for memory in the other direction;
- mask specialization, so causal, sliding-window, and bidirectional attention
  each get a loop that skips what it can prove is zero.

None of those change the mathematics. They are all in service of keeping
$m$, $l$, and $O$ on chip for the duration of the loop.
