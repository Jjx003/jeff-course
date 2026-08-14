# Solution walkthrough

## Units first

Almost every wrong answer in the graded section is a units answer. Bandwidth is
quoted in decimal GB/s, so weight traffic is divided by `1e9`. GPU capacity is
quoted in binary units, so the KV cache is divided by `1024 ** 3`. Peak compute
arrives in TFLOP/s and has to become FLOP/s before it divides anything.

Keeping those separate is not pedantry. A GB/GiB slip is a 7 percent error, which
is small enough to look like a plausible answer and large enough to move a
capacity decision.

## Reading bytes off tensors

`dtype_bytes` returns `torch.empty(0, dtype=dtype).element_size()`. A zero-element
tensor carries its dtype, so this is free and exact. The point is not that BF16 is
hard to remember; it is that the byte count and the dtype cannot drift apart if
one is derived from the other. The same discipline catches the case where someone
later switches `KV_DTYPE` to `float8_e4m3fn` and forgets a hardcoded 2.

The KV slab makes the same move at a larger scale. Rather than multiplying six
literals, allocate one token's keys and values for every layer:

```python
torch.empty(LAYERS, 2, kv_heads, HEAD_DIM, dtype=KV_DTYPE)
```

`80 * 2 * 8 * 128 = 163840` values at 2 bytes gives `327680` bytes per token for
GQA, and `2621440` for MHA. Multiplying by 8192 tokens gives 2.50 GiB and 20.00
GiB. The factor of 8 between them is the whole argument for grouped-query
attention, expressed in bytes rather than adjectives.

## The two floors

`41.79 ms` from bandwidth against `0.142 ms` from compute. The ratio is about 295,
which is the same 295 that appears in the ridge point — not a coincidence, since

$$
\frac{t_\text{memory}}{t_\text{compute}} = \frac{I_\text{ridge}}{I}
$$

and $I = 1$ FLOP/byte at batch 1. Seeing the same number twice from two different
directions is the cheapest available check that the arithmetic is right.

## The intensity table is the lesson

The one line that carries the module:

```python
intensity = decode_flops(batch) / weight_bytes
```

`weight_bytes` does not depend on batch. That single asymmetry — FLOPs scale with
batch, weight traffic does not — is why batching is the first optimization in
every serving stack. With BF16 weights the algebra collapses to $I = b$:

$$
I = \frac{2 P b}{2 P} = b
$$

so the crossover sits at the ridge point itself, near batch 295. The table shows
batch 256 memory-bound and batch 1024 compute-bound, bracketing it.

The `per_token_floor_ms` column is where the payoff is visible: `41.791` at batch
1, `0.163` at batch 256, and then `0.142` at batch 1024, where it stops improving
because compute has become the binding constraint. A factor of 256 in per-token
latency floor, with no change to the model, the precision, or the kernels.

The honest limit on that table is spelled out in the theory notes: it accounts
only for weight traffic. KV-cache reads are per-sequence, so they do not amortize
across the batch, and past roughly batch 52 at 8192-token contexts they exceed the
weight read entirely. The table is a correct statement about the term that
quantization attacks, not a complete latency model.

## What the measurement adds

The analytic half of this module could be done on paper. The measured half cannot,
and it is what stops the roofline from becoming a comfortable abstraction.

Two kernels at opposite ends of the intensity axis:

- `torch.add(x, 1.0, out=y)` on 32M float32 elements. One add per element against
  8 bytes of traffic: `0.125` FLOP/byte, below every real ridge point.
- A `2048 x 2048` float32 matmul: $2n^3$ FLOPs against $3n^2$ elements, so
  $n/6 \approx 341$ FLOP/byte, above every real ridge point.

The byte-accounting convention for the bandwidth number is stated explicitly in
the code: one full read of `x` plus one full write of `y`, so
`tensor_bytes(x) + tensor_bytes(y)`. Writing to a preallocated `out=` tensor keeps
a 128 MiB allocation per iteration out of the measurement.

The three harness requirements are not ceremony:

1. Warmup, because the first call pays for allocation, autotuning, and CUDA
   context setup.
2. Repetition with best and median reported, because one sample is a story about
   one scheduling accident.
3. `torch.cuda.synchronize()` on both sides of the interval, because launches are
   asynchronous. Skip it and the matmul appears to run in microseconds, implying
   throughput the hardware does not have. That failure mode is worth inducing once
   on purpose: a measurement that beats the vendor peak is always a broken
   measurement.

## The gap is the point

One run on an RTX 2070 SUPER measured `351.5 GB/s` against a 448 GB/s specified
peak and `7430.1 GFLOP/s` against roughly 9 TFLOP/s of specified FP32 throughput.
That is 78 to 82 percent of peak, which is a good result for a hand-written loop
and still short of the number on the box. Its measured ridge point came out near
`21 FLOP/byte` rather than the H100-class `295.22` in the graded section.

Nothing about that is a defect. Peak numbers assume ideal access patterns, full
occupancy, no launch overhead, and sustained clocks. Real kernels give some of each
back. That is exactly why the roofline is written as a floor on time rather than a
prediction of it, and why the model stays useful anyway: the *class* of the
bottleneck is robust to a 20 percent efficiency loss, even though the predicted
latency is not.

The practical reading is diagnostic. Measured time near the floor means the
remaining wins are in moving fewer bytes or doing less work — quantization,
batching, caching. Measured time far above the floor means there is implementation
headroom to recover first, and reaching for a new numeric format would be solving
the wrong problem.
