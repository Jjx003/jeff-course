# Hints

Work the graded part first. TODOs 1-6 plus 10 and 11 produce all of stdout;
TODOs 7-9 are the stderr measurement and can be left until the analytic table is
printing correctly.

Most failures here are unit failures, not Python failures. Keep the powers of ten
visible while you work.

## Units

For the weights:

- 70B parameters is `70 * 1e9`, not `70 * 1024 ** 3`.
- BF16 is 2 bytes per parameter, and TODO 1 makes you read that off a tensor
  rather than typing the 2.
- Decimal GB divides by `1e9`. Bandwidth is quoted in decimal GB/s, so weight
  traffic must be too.

For the work:

- Matmul FLOPs are `2 * PARAMS * batch`.
- `PEAK_TFLOP_S * 1e12` gives FLOP/s. If your compute floor is off by 1000, this
  is where it happened.

For time:

- Seconds are work divided by rate; multiply by `1e3` for milliseconds.
- The step floor is the larger of the two floors, and the bottleneck label names
  whichever one that is.

## Bytes from tensors

`dtype_bytes` needs no allocation of any size:

```python
torch.empty(0, dtype=dtype).element_size()
```

A zero-element tensor still carries its dtype, so `element_size()` is exact.

The KV slab is a real allocation, and it should be:

```python
slab = torch.empty(LAYERS, 2, kv_heads, HEAD_DIM, dtype=KV_DTYPE)
bytes_per_token = slab.numel() * slab.element_size()
```

For GQA that is `80 * 2 * 8 * 128 = 163840` values at 2 bytes, so `327680` bytes
per token. Capacity is reported in GiB, so divide the total by `1024 ** 3` — the
one place in this module where binary units are correct, because GPU memory
capacity is quoted that way.

If your GQA and MHA answers differ by exactly 8x, the only thing separating them
is `8` versus `64` KV heads, which is what you want.

## The intensity table

The subtle line is the intensity itself:

```python
intensity = decode_flops(batch) / weight_bytes
```

Note what is *not* in that expression: `weight_bytes` has no `batch` in it. One
pass over the weights serves the whole step. If you find yourself multiplying the
weight bytes by the batch size, you have written down a system that gets no
benefit from batching at all, and the intensity column will be constant — a
useful signal that something is wrong.

The regime test is `intensity < ridge`, and the step floor is
`max(memory_ms, batch_compute_ms)`. Only the compute floor moves with batch.

## The timing loop

Structure it exactly this way:

```python
for _ in range(MEASURE_WARMUP):
    fn()
if device.type == "cuda":
    torch.cuda.synchronize()

samples = []
for _ in range(MEASURE_REPS):
    if device.type == "cuda":
        torch.cuda.synchronize()
    started = time.perf_counter()
    fn()
    if device.type == "cuda":
        torch.cuda.synchronize()
    samples.append(time.perf_counter() - started)
```

The synchronize before `perf_counter()` drains work queued by the previous
iteration so it is not charged to this one. The synchronize after is what makes
the interval cover the kernel instead of the launch.

`sorted(samples)[0]` is the best sample and `sorted(samples)[len(samples) // 2]`
is the median. Report both. The best sample is the closest thing you have to the
machine's real capability; the median tells you how noisy the run was.

## Byte accounting for bandwidth

State the convention before you divide:

```python
elementwise_bytes = tensor_bytes(x) + tensor_bytes(y)   # one read + one write
```

`torch.add(x, 1.0, out=y)` reads all of `x` and writes all of `y`. The scalar
`1.0` is a kernel argument, not traffic. Using `out=y` on a preallocated tensor
keeps the allocator out of the measurement, which matters because a 128 MiB
allocation per iteration is not free.

For the matmul, `2 * n ** 3` FLOPs and `tensor_bytes(a) + tensor_bytes(b) +
tensor_bytes(c)` bytes. That byte count is optimistic — a real tiled GEMM reads
tiles more than once — which is fine, because it is the FLOP/s number you care
about there, not the bandwidth.

## Common mistakes

- **Double-counting bytes in the bandwidth calculation.** Counting a read of `y`
  as well as the write, or counting the write twice, inflates achieved bandwidth
  by 50 percent or more. Counting only the read of `x` halves it. Write the rule
  down next to the number.
- **Forgetting `torch.cuda.synchronize()`.** Launches return immediately, so an
  unsynchronized timer measures queue submission. The symptom is unmistakable: a
  matmul that "runs" in tens of microseconds, implying tens of TFLOP/s on
  hardware that cannot do it. If a measured number beats the vendor peak, you
  did not find free performance; you mistimed something.
- Multiplying weight bytes by batch size in the intensity column.
- Timing the first call, which includes CUDA context creation, allocator growth,
  and cuBLAS handle setup.
- Reporting a single sample instead of best or median.
- Mixing GB and GiB. Bandwidth in decimal, capacity in binary.
- Sizing the elementwise tensor small enough to fit in cache. You then measure
  cache bandwidth, which can be several times DRAM bandwidth, and conclude your
  memory system is better than it is.
- Putting a timing number on stdout. It will not reproduce and the module will
  fail on the next machine.

## Sanity checks

Graded stdout, which must match exactly:

- `bytes per weight: 2` and `weight bytes: 140000000000`.
- `GQA slab bytes per token: 327680`, `MHA slab bytes per token: 2621440`.
- `weight read: 140.0 GB`, `matmul work: 140.0 GFLOP`.
- `memory lower bound: 41.79 ms`, `compute lower bound: 0.142 ms`,
  `bottleneck guess: memory`.
- `GQA KV cache: 2.50 GiB`, `MHA KV cache: 20.00 GiB`.
- `ridge point: 295.22 FLOP/byte`.
- In the sweep, intensity equals the batch size exactly: `1.00`, `4.00`, `16.00`,
  `64.00`, `256.00`, `1024.00`. The regime is `memory` through batch 256 and
  `compute` at 1024.
- `step_floor_ms` is `41.79` for every batch up to 256, then `144.95` at 1024.
- `per_token_floor_ms` runs `41.791`, `10.448`, `2.612`, `0.653`, `0.163`,
  `0.142`.

Measured stderr, which will not match anything but should be plausible:

- `intensity: 0.125 FLOP/byte` for the elementwise kernel and
  `intensity: 341.3 FLOP/byte` for the 2048-cube matmul. These two are pure
  arithmetic, so they are the same on every machine.
- `bytes moved: 268435456` for the elementwise kernel and
  `FLOPs: 17179869184` for the matmul.
- Achieved bandwidth somewhere between roughly 10 and 100 GB/s on a CPU, or a
  few hundred GB/s to a few TB/s on a GPU.
- Achieved FP32 compute from a few hundred GFLOP/s on a CPU up to tens of
  TFLOP/s on a datacentre GPU.
- Best and median within a few percent of each other. A median far above the
  best means something else was using the machine.

For calibration, one run on an RTX 2070 SUPER (448 GB/s and roughly 9 TFLOP/s
FP32 on paper) reported `351.5 GB/s`, `7430.1 GFLOP/s`, and a measured ridge
point of `21.1 FLOP/byte`. The same script forced onto that machine's CPU
reported `23.2 GB/s`, `836.3 GFLOP/s`, and a ridge point of `36.1 FLOP/byte`.
Treat those as one machine's numbers, not targets.

Two things are worth noticing. First, both GPU measurements land at 78 to 82
percent of that card's specified peaks, which is a good result and still visibly
short of peak. Second, the measured ridge points are an order of magnitude below the
H100-class `295.22` in the graded section — partly because FP32 has no tensor-core
path on either device, and partly because the ridge point is a property of a
specific pair of peaks, not a universal constant.

## Going deeper

- Change `MEASURE_ELEMS` to something small, such as `1024 * 128`, and watch
  achieved bandwidth climb. You are now measuring cache, not memory. This is the
  most common way benchmark numbers get accidentally inflated.
- Run the elementwise kernel in `torch.float16` or `torch.bfloat16`. Bytes moved
  halve, and if the kernel is genuinely bandwidth-bound the time should roughly
  halve too. If it does not, you have found a kernel that is limited by something
  else.
- Sweep the matmul size from 256 to 4096 and plot achieved GFLOP/s. Small sizes
  cannot fill the machine, so throughput climbs with $n$ before flattening. The
  knee is where the problem finally becomes large enough to be compute-bound in
  practice rather than only on paper.
- Recompute the batch table with INT4 weights, at 0.5 bytes per weight. Intensity
  becomes $4b$, the memory floor drops by 4x, and the crossover moves down to
  about batch 74. That is the module 4 result previewed as arithmetic.
- Add the KV-cache traffic term to the sweep, `2.68 GB` per sequence per step,
  and confirm the claim in the theory notes that with 8192-token contexts the
  step never becomes compute-bound at any batch size.
- Try `torch.utils.benchmark.Timer` instead of a hand-rolled loop. It handles
  warmup, repetition, and synchronization for you, and comparing its numbers with
  yours is a good check on your harness.

## References

- Williams, Waterman, and Patterson, *Roofline: An Insightful Visual Performance
  Model for Multicore Architectures*, Communications of the ACM 52(4), April
  2009, pages 65-76. The original paper; the ridge point and the intensity axis
  come from here.
- Pope et al., *Efficiently Scaling Transformer Inference* (2023),
  https://arxiv.org/abs/2211.05102 — applies exactly this arithmetic to
  transformer decode, including batch size and the memory/compute crossover.
- Shazeer, *Fast Transformer Decoding: One Write-Head is All You Need* (2019),
  https://arxiv.org/abs/1911.02150 — multi-query attention, motivated explicitly
  by decode-time memory bandwidth.
- Ainslie et al., *GQA: Training Generalized Multi-Query Transformer Models from
  Multi-Head Checkpoints* (2023), https://arxiv.org/abs/2305.13245 — the
  grouped-query attention used in this exercise's KV-cache numbers.
- Kwon et al., *Efficient Memory Management for Large Language Model Serving with
  PagedAttention* (2023), https://arxiv.org/abs/2309.06180 — what happens when
  KV-cache capacity, rather than bandwidth or compute, is the binding constraint.
- NVIDIA, *GPU Performance Background User's Guide*,
  https://docs.nvidia.com/deeplearning/performance/dl-performance-gpu-background/
  — vendor-side treatment of arithmetic intensity and math-bound versus
  memory-bound kernels.
