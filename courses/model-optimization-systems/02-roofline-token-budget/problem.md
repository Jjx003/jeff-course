# Roofline math for token budgets

The previous module named the budgets in modern model serving: weight
bandwidth, compute throughput, activation memory, KV cache capacity, kernel
overhead, and scheduling. This exercise makes the first two quantitative, and
then it does something the reading could not: it checks the model against a real
machine.

You will write two things.

**Part 1** is an analytic roofline for one decode step of a 70B decoder-only
LLM. It derives byte counts from real tensor dtypes, produces the two lower
bounds on latency, locates the machine's ridge point, and sweeps batch size to
find where the workload stops being memory-bound. Every line of this goes to
**stdout** and is graded.

**Part 2** times two real torch kernels — one that can only be limited by
memory bandwidth and one that can only be limited by compute — and reports the
throughput each actually achieves. All of this goes to **stderr** and is not
graded.

## Why the output is split in two

Part 1 runs on CPU with a fixed seed and prints only exact integers, dtypes, and
rounded ratios. Nothing in it depends on your hardware, so your output matches
the reference byte for byte and the grader can compare printed lines.

Part 2 cannot work that way. A timing measurement is a property of your machine:
its memory subsystem, its core count, its clock behaviour, whether it has a GPU
at all. If those numbers went to stdout, the module would only pass on one
computer. Sending them to stderr means the session log shows you your own
hardware while the graded surface stays reproducible.

The awkward consequence is worth naming up front: the interesting numbers in
this module are the ungraded ones. Part 1 tells you what the hardware *cannot
beat*. Part 2 tells you what it *actually does*, and the distance between them
is the point of the whole exercise.

## Constants

The analytic section uses an H100-class accelerator and a 70B model:

- Parameters: 70B
- Weight dtype: BF16
- Approximate decode matmul FLOPs: $2 \times$ parameter count $\times$ batch
- Memory bandwidth: 3350 GB/s
- Peak BF16 compute: 989 TFLOP/s
- Layers: 80
- GQA KV heads: 8
- MHA KV heads: 64
- Head dimension: 128
- Context length: 8192
- KV dtype: BF16

Use decimal GB for bandwidth and GiB for cache capacity. Do not change the
print labels; the grader compares printed lines.

## Part 1a — Derive the bytes from tensors, not from literals

Two bytes per BF16 value is easy to assert and easy to get wrong, so the
starter asks you to read it off a tensor instead:

```python
def dtype_bytes(dtype):
    return torch.empty(0, dtype=dtype).element_size()
```

The same discipline applies to the KV cache. Rather than multiplying six
literals, allocate one token's worth of keys and values for the whole model:

```python
torch.empty(LAYERS, 2, kv_heads, HEAD_DIM, dtype=KV_DTYPE)
```

That is a real tensor — 320 KiB for the GQA shape, 2.5 MiB for MHA — and
`numel() * element_size()` gives its size with no arithmetic on your part. The
per-request cache is then that slab times the number of tokens. Habit worth
forming: when a byte count can be measured instead of asserted, measure it.

## Part 1b — The two floors

For one decode step at batch 1, with $B$ bytes moved, $F$ FLOPs, bandwidth
$\beta$, and peak throughput $\phi$:

$$
t_\text{memory} = \frac{B}{\beta}, \qquad t_\text{compute} = \frac{F}{\phi}
$$

Real latency is at least the larger of the two. With these constants the memory
floor is `41.79 ms` and the compute floor is `0.142 ms`, so weight traffic is
roughly 295 times more binding than arithmetic. That is not a small correction
to a compute-first intuition; it inverts it.

## Part 1c — Arithmetic intensity across batch size

This is the part the earlier version of this exercise was missing, and it is the
single most useful table in the module.

Arithmetic intensity is work per byte:

$$
I = \frac{F}{B}
$$

The machine's **ridge point** is the intensity at which its two peaks balance:

$$
I_\text{ridge} = \frac{\phi}{\beta}
= \frac{989 \times 10^{12}\ \text{FLOP/s}}{3350 \times 10^{9}\ \text{bytes/s}}
\approx 295.22\ \text{FLOP/byte}
$$

Below the ridge, bandwidth limits you. Above it, compute limits you.

Now sweep batch size. The decisive observation is that **weight bytes do not
grow with batch**: one pass over the weights serves every sequence in the step,
while FLOPs scale linearly with batch. So

$$
I = \frac{2 P b}{P \cdot \text{bytes per weight}} = \frac{2b}{2} = b
$$

for BF16 weights. Arithmetic intensity *equals* the batch size, which makes the
crossover trivial to read off: this workload stays memory-bound until batch size
passes about 295, and the sweep shows batch 256 memory-bound and batch 1024
compute-bound.

Report, for each batch in `[1, 4, 16, 64, 256, 1024]`: the step's FLOPs, its
intensity, the regime, the step latency floor, and the floor per token. The last
column falls from `41.791 ms` at batch 1 to `0.163 ms` at batch 256 — a factor
of 256, obtained without touching the model, the precision, or the kernels.
Past the ridge it flattens out at `0.142 ms`, because compute has become the
limit and more batch no longer buys reuse.

That single column is why batching is the first thing every serving system
does, and why every later module in this course is measured against a batched
baseline rather than a batch-1 one.

## Part 2 — Measure the machine

Now find out what the hardware really delivers. Two kernels, chosen to sit at
opposite ends of the roofline:

**Memory-bound:** `torch.add(x, 1.0, out=y)` on 32M float32 elements. One
floating-point add per element against 8 bytes of traffic, so
$I = 0.125$ FLOP/byte — far below any real machine's ridge point. Achieved
bandwidth is bytes moved divided by elapsed time.

Be explicit about what "bytes moved" means. The kernel reads every element of
`x` once and writes every element of `y` once, so the traffic is
`tensor_bytes(x) + tensor_bytes(y)`, which is $2 \times 128$ MiB. Counting only
the read halves your answer; counting a read of `y` as well inflates it. Write
your convention down, because a bandwidth number without an accounting rule is
not a measurement.

**Compute-bound:** a $2048 \times 2048$ float32 matmul. A dense $n \times n$
product does $2n^3$ FLOPs and moves $3n^2$ elements, so
$I = n/6 \approx 341$ FLOP/byte — above the ridge point of essentially every
current accelerator.

Three requirements make the measurement honest rather than decorative:

1. **Warm up.** The first call pays for allocation, kernel autotuning, and lazy
   CUDA context setup. Call the operation a couple of times untimed first.
2. **Repeat.** Take several samples and report the best and the median. A single
   sample tells you about one scheduling accident.
3. **Synchronize.** CUDA kernel launches are asynchronous. Without
   `torch.cuda.synchronize()` before you start the clock and again before you
   stop it, you are timing the launch queue, and a 2 ms matmul will look like
   20 microseconds. Fall back to CPU cleanly when no GPU is present and print
   which device you used.

### Expect the gap

Your measured numbers will land well below the vendor's peak. That is the
expected outcome, not a bug in your code and not a failure of your machine.

For a concrete example, one run on an RTX 2070 SUPER reported
`351.5 GB/s` achieved on the elementwise kernel against a 448 GB/s specified
peak, and `7430 GFLOP/s` on the matmul against roughly 9 TFLOP/s of specified
FP32 throughput. Its measured ridge point came out near `21 FLOP/byte`. Your
numbers will differ; that is the nature of the measurement.

The gap has ordinary causes: cache and DRAM page behaviour, imperfect access
patterns, a kernel that cannot keep every unit busy, launch and synchronization
overhead, clock and thermal limits, and — on CPU — the plain absence of a
high-bandwidth memory system. None of them are exotic. All of them are why the
roofline is stated as a **lower bound on time** rather than a prediction of it.

This is also the correct way to read the two parts together. Part 1 says a
batch-1 decode step on an H100 cannot take less than 41.79 ms. It does not say
it will take 41.79 ms. A real engine hitting 60 to 70 percent of peak bandwidth
lands meaningfully above the floor, and the floor is still the right first
question to ask, because no amount of engineering gets underneath it.

## Recap

A roofline is not a simulator and it is not a prediction. It is a floor, and now
you have both the floor and a measurement of how far above it real hardware
sits. If a serving plan claims a small-batch 70B decode step beats the time
needed to read the weights, the claim needs a specific explanation: batch reuse,
lower-bit weights, prefix caching, sparsity, or a different workload phase.

The batch-size sweep points at the next two modules. A 140 GB weight-read term
is what makes weight-only quantization worth the trouble, so module 3 surveys
the formats — INT8, INT4, NF4, FP8, FP4, and KV-cache quantization — and module
4 has you build a groupwise INT4 quantizer and measure what it costs in output
error.
