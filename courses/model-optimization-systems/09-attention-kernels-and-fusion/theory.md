# Online softmax recurrence

The key mathematical trick behind tiled exact attention is that softmax can be updated block by block without storing all scores at once.

For a row of attention scores $x_1,\dots,x_n$, the stable softmax denominator is:

$$
l = \sum_i e^{x_i-m}
$$

where:

$$
m = \max_i x_i
$$

Now suppose the row arrives in blocks. For the old blocks, keep:

$$
m_\text{old} = \max_{i \in \text{old}} x_i
$$

$$
l_\text{old} = \sum_{i \in \text{old}} e^{x_i-m_\text{old}}
$$

For a new block $b$, compute:

$$
m_b = \max_{j \in b} x_j
$$

$$
l_b = \sum_{j \in b} e^{x_j-m_b}
$$

The combined maximum is:

$$
m_\text{new} = \max(m_\text{old}, m_b)
$$

The combined denominator is:

$$
l_\text{new} =
e^{m_\text{old}-m_\text{new}}l_\text{old}
+ e^{m_b-m_\text{new}}l_b
$$

The exponentials rescale both partial sums into the same reference frame. This is the whole numerical stability story: every block may have used its own maximum, but the merged denominator is as if all scores had been normalized by the final maximum.

## Including values

Attention is not just softmax probabilities. It is a weighted sum of value vectors:

$$
o = \sum_i p_i v_i
$$

where:

$$
p_i = \frac{e^{x_i-m}}{l}
$$

It is usually easier to maintain an unnormalized numerator:

$$
n = \sum_i e^{x_i-m}v_i
$$

Then:

$$
o = \frac{n}{l}
$$

When a new block arrives, compute its block numerator:

$$
n_b = \sum_{j \in b} e^{x_j-m_b}v_j
$$

and merge:

$$
n_\text{new} =
e^{m_\text{old}-m_\text{new}}n_\text{old}
+ e^{m_b-m_\text{new}}n_b
$$

Finally:

$$
o_\text{new} = \frac{n_\text{new}}{l_\text{new}}
$$

The next coding lab asks you to implement exactly this one-row version.

## The merge is associative, and that is worth more than it looks

Write the state of a partial computation as the triple $(m, l, n)$. The merge
rule above defines a binary operation on such triples, and it is worth checking
that this operation is **associative**: merging blocks 1 and 2 and then block 3
gives the same triple as merging block 1 with the merge of blocks 2 and 3. Both
routes rescale every partial sum into the reference frame of the same final
maximum, and $\max$ and addition are themselves associative.

An associative merge over a set of blocks is a **reduction**, and reductions do
not have to be evaluated left to right. They can be evaluated as a tree, in
parallel, in any order. So the same algebra that lets one thread stream through
key blocks sequentially also lets a hundred thread blocks process disjoint
ranges of keys independently and combine their partial results afterwards.

Sequential streaming is what saves memory during prefill. Parallel reduction is
what saves *latency* during decode, where there is only one query row and
almost nothing else to parallelize over. Both fall out of the same three-line
recurrence, which is why it is worth implementing carefully rather than
importing.

## Recomputation: trading FLOPs for traffic in the backward pass

The forward pass is only half the problem during training. A standard backward
pass needs the probability matrix $P$ to compute gradients, and $P$ is exactly
the $L \times L$ object the forward pass went to such lengths not to write.

The resolution is neither to store it nor to recompute it from scratch. The
forward pass saves the output $O$ and the per-row statistics $(m, l)$ — that is
$O(L)$ values, not $O(L^2)$. The backward pass recomputes each tile of $S$ and
$P$ on chip from $Q$, $K$, and $V$, using the saved statistics so that no second
pass over the row is needed to recover the maximum. Each tile is consumed
immediately and discarded.

This is gradient checkpointing applied at the granularity of a kernel rather
than a layer, and the accounting is favorable for a reason specific to
attention:

| | Standard backward | Tiled backward |
|---|---|---|
| HBM traffic | $\Theta(L^2)$ | $\Theta(L^2d^2/M)$ |
| FLOPs | $1\times$ | about $2.5\times$ |
| Wall clock | slower | faster |

Doing two and a half times the arithmetic and finishing sooner only makes sense
because attention sits far below the compute roof. In a memory-bound regime,
FLOPs are nearly free and bytes are the currency. The identical trade applied to
an already compute-bound kernel would be a straight loss. That is the general
lesson worth carrying out of this module: recomputation pays exactly when the
roofline says you have compute to spare, and module 2's arithmetic is how you
check before committing.

## Why FlashAttention-2 was a rewrite rather than a tweak

FlashAttention-1 removed the traffic bottleneck and immediately exposed two
others.

**Non-matmul FLOPs are not equal to matmul FLOPs.** On an A100, BF16 matmul runs
at 312 TFLOP/s while non-matmul FP32 work runs at 19.5 TFLOP/s — a factor of 16.
An exponential, a division, or a rescale therefore costs about sixteen times
what its FLOP count suggests. FlashAttention-1 rescaled its output accumulator
by $1/l$ on every block. FlashAttention-2 keeps the accumulator unnormalized
throughout and divides by $l$ exactly once, at the end. Algebraically identical,
materially faster.

**Parallelism was tied to batch and heads.** FlashAttention-1 assigned one thread
block per (batch, head) pair. At batch 1 with 32 heads on a 108-SM GPU, two
thirds of the machine idles — precisely the long-sequence, small-batch case that
motivated the kernel. FlashAttention-2 adds a parallel dimension over query
blocks, which is legal because different query rows share no state.

A third change is subtler and pays off in shared memory. Within a thread block,
FlashAttention-1 split the *key/value* range across warps, so each warp produced
a partial output for the same query rows and the warps had to write partials to
shared memory and synchronize to combine them. FlashAttention-2 splits the
*query* rows across warps instead. Each warp then owns its output slice
outright, needs no cross-warp reduction, and never touches shared memory for
partials. Same math, different assignment of work to warps, and roughly a
2× end-to-end speedup — reaching 50 to 73 percent of the A100's theoretical
maximum.

## What FlashAttention-3 buys on Hopper

FlashAttention-2 leaves the tensor cores waiting: first for data to arrive, then
for the softmax to finish. FlashAttention-3 attacks both with hardware features
that did not exist on Ampere.

- **Warp specialization.** Warps are split into producers and consumers.
  Producers issue asynchronous Tensor Memory Accelerator copies and do no math;
  consumers do math and never wait on an address computation. They coordinate
  through async barriers, so the next tile is arriving while the current one is
  being multiplied.
- **Interleaving the softmax with the GEMM.** The exponential runs on the
  special function units, whose throughput is orders of magnitude below the
  tensor cores'. Running softmax and matmul strictly in sequence idles whichever
  unit is not currently in use. FlashAttention-3 schedules two warpgroups out of
  phase so that one performs its softmax while the other performs its GEMM.
- **FP8 with incoherent processing.** Naively casting Q and K to FP8 fails on
  outlier channels, the same failure mode as module 3. The fix borrowed from
  QuIP is to multiply Q and K by a random orthogonal matrix — a Hadamard
  transform with random signs, computable in $O(d\log d)$. This is exact,
  because $(QH)(KH)^\top = QK^\top$ for orthogonal $H$, and it spreads outlier
  mass across all channels before quantization, cutting FP8 error by roughly
  2.6×.

The reported result is 1.5 to 2.0× over FlashAttention-2 on H100, around
740 TFLOP/s in FP16 and near 1.2 PFLOP/s in FP8. Note that the last item is not
really a kernel-scheduling trick at all: it is the quantization theory from
module 3 reappearing inside an attention kernel. The stack layers in this course
are a teaching device, not a wall.

## Decode needs a different kernel again

Everything above optimizes prefill, where there are many query rows. In decode
there is exactly one query row per sequence, so FlashAttention-2's parallelism
over query blocks yields a single block and the occupancy problem returns in a
worse form: only batch × heads units of parallel work, against a long KV cache.

FlashDecoding uses the associativity established at the top of this page. It
splits the **key/value** dimension into chunks, computes a partial
$(m, l, O)$ for each chunk in parallel across many thread blocks, then runs a
small second kernel that merges the partials with the same rescaling rule. The
sequential recurrence becomes a parallel tree reduction, and a batch-1 decode
step can finally use the whole GPU.

| Phase | Rows of Q | Natural parallelism | Kernel strategy |
|---|---|---|---|
| Prefill | many | query blocks × heads × batch | stream over KV, sequential merge |
| Decode | one per sequence | heads × batch only | split KV, parallel merge |

This is why serving stacks ship separate prefill and decode attention kernels,
and why a benchmark that reports one number for "attention" is not telling you
much.

## Prefill versus decode

LLM inference has two very different phases:

| Phase | What happens | Common bottleneck |
|---|---|---|
| Prefill | Process the prompt tokens, often many at once | Attention/MLP throughput and long-context memory traffic |
| Decode | Generate one or a few new tokens per request | KV-cache reads, scheduling, memory bandwidth |

FlashAttention-style kernels are especially visible during prefill because many prompt tokens attend over many previous prompt tokens. During decode, each request often contributes one new query token, so the computation shape changes. Decode performance depends heavily on KV-cache layout, batching, and how efficiently the system reads old keys and values.

This distinction is why serving benchmarks report time-to-first-token and output tokens per second separately. A change that improves prefill may not improve decode, and vice versa.

## Layout and precision

Fast kernels care about details that high-level equations ignore:

- head dimension,
- number of query heads versus KV heads,
- causal versus bidirectional masks,
- packed versus padded batches,
- tensor memory layout,
- dtype of Q, K, V, and output,
- whether dropout is needed,
- whether rotary embeddings are fused,
- whether quantized values must be dequantized inside the kernel.

In training, backward pass support also matters. In inference, the key questions are usually latency, throughput, memory footprint, and numerical tolerance. FP8 and low-bit paths can be excellent on the right hardware, but they need calibration and careful validation on the actual model and task.

## Practical caveats

Kernel claims are easy to overgeneralize. Keep these distinctions clear:

- Exact tiled attention changes memory traffic, not the mathematical attention result.
- Approximate or sparse attention changes the computation itself.
- Weight quantization reduces model storage and matmul bandwidth, but it does not automatically reduce KV-cache memory.
- KV-cache quantization reduces serving memory, but it can affect long-context retrieval quality.
- Fusion can make one path fast while making unusual shapes harder to support.

## Going deeper

- FlashAttention paper: https://arxiv.org/abs/2205.14135
- FlashAttention-2 paper: https://arxiv.org/abs/2307.08691
- FlashAttention-3 paper: https://arxiv.org/abs/2407.08608
- FlashAttention repository: https://github.com/Dao-AILab/flash-attention
- TensorRT-LLM attention documentation: https://nvidia.github.io/TensorRT-LLM/advanced/gpt-attention.html
- FlashDecoding, splitting the KV dimension for batch-1 decode: https://pytorch.org/blog/flash-decoding/
- Online normalizer calculation for softmax (Milakov and Gimelshein), the recurrence this module is built on: https://arxiv.org/abs/1805.02867
- QuIP, the source of the incoherence-processing trick FlashAttention-3 reuses for FP8: https://arxiv.org/abs/2307.13304
