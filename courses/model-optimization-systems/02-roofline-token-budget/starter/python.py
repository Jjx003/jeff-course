"""
Roofline lower bounds for one decode step, then a measurement of the machine.

Part 1 prints to stdout and is graded. It runs on CPU with a fixed seed and
contains no timings, so your numbers match the grader's exactly.

Part 2 prints to stderr and is not graded. It times real torch operations, so
its numbers depend on your hardware. See problem.md for why the split exists.
"""

import sys
import time

import torch

PARAMS = 70_000_000_000
WEIGHT_DTYPE = torch.bfloat16
KV_DTYPE = torch.bfloat16

LAYERS = 80
HEAD_DIM = 128
GQA_KV_HEADS = 8
MHA_KV_HEADS = 64
CONTEXT_TOKENS = 8192

PEAK_TFLOP_S = 989.0
BANDWIDTH_GB_S = 3350.0
BATCH_SWEEP = [1, 4, 16, 64, 256, 1024]

MEASURE_ELEMS = 32 * 1024 * 1024
MEASURE_MATMUL_N = 2048
MEASURE_WARMUP = 2
MEASURE_REPS = 7


def dtype_bytes(dtype: torch.dtype) -> int:
    """Bytes per element, read off a real tensor rather than assumed."""
    # TODO 1: Allocate an empty tensor of this dtype and return its
    # element_size(). torch.empty(0, dtype=dtype) costs nothing and keeps the
    # byte accounting honest about the dtype you actually named.
    raise NotImplementedError


def tensor_bytes(t: torch.Tensor) -> int:
    """Bytes occupied by a tensor's elements."""
    # TODO 2: return t.numel() * t.element_size().
    raise NotImplementedError


def kv_slab(kv_heads: int) -> torch.Tensor:
    """One token's keys and values for every layer, at real dtype and shape."""
    # TODO 3: Return an empty KV_DTYPE tensor of shape
    # (LAYERS, 2, kv_heads, HEAD_DIM). The 2 is keys and values. This is a real
    # allocation: 320 KiB for GQA, 2.5 MiB for MHA.
    raise NotImplementedError


def kv_cache_gib(slab: torch.Tensor, tokens: int) -> float:
    """Cache size in GiB for `tokens` positions of one request."""
    # TODO 4: Scale the slab's byte count by the token count and divide by
    # 1024 ** 3. Capacity is reported in binary units; bandwidth is decimal.
    raise NotImplementedError


def decode_flops(batch: int) -> int:
    """Approximate matmul FLOPs for one decode step: 2 FLOPs per weight per sequence."""
    # TODO 5: return 2 * PARAMS * batch.
    raise NotImplementedError


def ridge_point() -> float:
    """FLOPs per byte at which peak compute and peak bandwidth are balanced."""
    # TODO 6: Divide peak FLOP/s by peak bytes/s. Convert both constants out of
    # TFLOP/s and GB/s first; a factor of 1000 here moves the answer by 1000x.
    raise NotImplementedError


def time_op(fn, device: torch.device) -> tuple[float, float]:
    """Return (best, median) seconds over MEASURE_REPS timed calls."""
    # TODO 7: Write an honest timing loop.
    #   - call fn() MEASURE_WARMUP times first and do not time those calls;
    #   - if device.type == "cuda", call torch.cuda.synchronize() before
    #     starting the clock and again before stopping it, otherwise you are
    #     timing kernel launches rather than kernels;
    #   - collect MEASURE_REPS samples with time.perf_counter();
    #   - return the smallest and the median sample.
    raise NotImplementedError


def measure_machine(device: torch.device) -> None:
    """Measure the two ends of the roofline. Everything here goes to stderr."""
    if device.type == "cuda":
        print(f"[measured] device: cuda ({torch.cuda.get_device_name(0)})", file=sys.stderr)
    else:
        print("[measured] device: cpu", file=sys.stderr)
    print("[measured] float32; the peaks above are H100-class, these are this machine", file=sys.stderr)

    with torch.inference_mode():
        x = torch.ones(MEASURE_ELEMS, device=device, dtype=torch.float32)
        y = torch.empty_like(x)
        # TODO 8: Bytes moved by `torch.add(x, 1.0, out=y)`. The kernel reads
        # every element of x once and writes every element of y once, so count
        # both. Using only x's bytes overstates bandwidth by exactly 2x.
        elementwise_bytes = 1
        best, median = time_op(lambda: torch.add(x, 1.0, out=y), device)
        gb_s = elementwise_bytes / best / 1e9
        # One add per element, so intensity is elements / bytes moved.
        elementwise_intensity = x.numel() / elementwise_bytes

        print("[measured] --- memory-bound: y = x + 1 ---", file=sys.stderr)
        print(f"[measured]   elements: {x.numel()}  bytes moved: {elementwise_bytes}", file=sys.stderr)
        print(f"[measured]   best: {best * 1e3:.3f} ms  median: {median * 1e3:.3f} ms", file=sys.stderr)
        print(f"[measured]   achieved bandwidth: {gb_s:.1f} GB/s", file=sys.stderr)
        print(f"[measured]   intensity: {elementwise_intensity:.3f} FLOP/byte", file=sys.stderr)

        del x, y
        if device.type == "cuda":
            torch.cuda.empty_cache()

        n = MEASURE_MATMUL_N
        a = torch.ones(n, n, device=device, dtype=torch.float32)
        b = torch.ones(n, n, device=device, dtype=torch.float32)
        c = torch.empty(n, n, device=device, dtype=torch.float32)
        # TODO 9: A dense n x n by n x n matmul does 2 * n ** 3 FLOPs: one
        # multiply and one add per inner-product term. It moves the two inputs
        # and the output, which is 3 * n * n * 4 bytes in float32 — use
        # tensor_bytes on a, b, and c rather than writing that literal.
        matmul_flops = 1
        matmul_bytes = 1
        best, median = time_op(lambda: torch.matmul(a, b, out=c), device)
        gflop_s = matmul_flops / best / 1e9
        matmul_intensity = matmul_flops / matmul_bytes

        print(f"[measured] --- compute-bound: {n}x{n} matmul ---", file=sys.stderr)
        print(f"[measured]   FLOPs: {matmul_flops}  bytes moved: {matmul_bytes}", file=sys.stderr)
        print(f"[measured]   best: {best * 1e3:.3f} ms  median: {median * 1e3:.3f} ms", file=sys.stderr)
        print(f"[measured]   achieved compute: {gflop_s:.1f} GFLOP/s", file=sys.stderr)
        print(f"[measured]   intensity: {matmul_intensity:.1f} FLOP/byte", file=sys.stderr)

        measured_ridge = (gflop_s * 1e9) / (gb_s * 1e9)
        print(f"[measured] measured ridge point: {measured_ridge:.1f} FLOP/byte", file=sys.stderr)
        print(
            f"[measured] elementwise intensity {elementwise_intensity:.3f} is below it, "
            f"matmul intensity {matmul_intensity:.1f} is above it",
            file=sys.stderr,
        )


def main() -> None:
    torch.manual_seed(0)

    weight_bytes_per_param = dtype_bytes(WEIGHT_DTYPE)
    weight_bytes = PARAMS * weight_bytes_per_param
    gqa_slab = kv_slab(GQA_KV_HEADS)
    mha_slab = kv_slab(MHA_KV_HEADS)

    print("=== 70B decode roofline ===")
    print(f"params: {PARAMS}")
    print(f"weight dtype: {WEIGHT_DTYPE}")
    print(f"bytes per weight: {weight_bytes_per_param}")
    print(f"weight bytes: {weight_bytes}")
    print(f"layers: {LAYERS}")
    print(f"context tokens: {CONTEXT_TOKENS}")
    print(f"KV dtype: {KV_DTYPE}")
    print(f"GQA slab shape: {tuple(gqa_slab.shape)}")
    print(f"GQA slab bytes per token: {tensor_bytes(gqa_slab)}")
    print(f"MHA slab shape: {tuple(mha_slab.shape)}")
    print(f"MHA slab bytes per token: {tensor_bytes(mha_slab)}")
    print()

    flops = decode_flops(1)
    # TODO 10: Compute the two lower bounds in milliseconds, then label the
    # larger one.
    #   memory_ms  -> weight_bytes / (BANDWIDTH_GB_S * 1e9), in ms
    #   compute_ms -> flops / (PEAK_TFLOP_S * 1e12), in ms
    #   bottleneck -> "memory" or "compute", whichever floor is larger
    memory_ms = 0.0
    compute_ms = 0.0
    bottleneck = "unknown"

    print("--- one decode step at batch 1 ---")
    print(f"weight read: {weight_bytes / 1e9:.1f} GB")
    print(f"matmul work: {flops / 1e9:.1f} GFLOP")
    print(f"memory lower bound: {memory_ms:.2f} ms")
    print(f"compute lower bound: {compute_ms:.3f} ms")
    print(f"bottleneck guess: {bottleneck}")
    print(f"GQA KV cache: {kv_cache_gib(gqa_slab, CONTEXT_TOKENS):.2f} GiB")
    print(f"MHA KV cache: {kv_cache_gib(mha_slab, CONTEXT_TOKENS):.2f} GiB")
    print()

    ridge = ridge_point()
    print("--- machine ridge point ---")
    print(f"peak compute: {PEAK_TFLOP_S:.1f} TFLOP/s")
    print(f"peak bandwidth: {BANDWIDTH_GB_S:.1f} GB/s")
    print(f"ridge point: {ridge:.2f} FLOP/byte")
    print()

    print("--- arithmetic intensity vs batch size ---")
    for batch in BATCH_SWEEP:
        # TODO 11: Replace the four placeholders below.
        #   batch_flops -> decode_flops(batch)
        #   intensity   -> batch_flops / weight_bytes. Weight bytes do not grow
        #                  with batch: one read of the weights serves every
        #                  sequence in the step. That is why batching works.
        #   step_ms     -> the larger of memory_ms and this batch's compute floor
        #   regime      -> "memory" below the ridge point, "compute" above it
        batch_flops = 0
        intensity = 0.0
        step_ms = 0.0
        regime = "unknown"

        print(
            f"  batch={batch:<5d} "
            f"GFLOP={batch_flops / 1e9:<9.1f} "
            f"intensity={intensity:<8.2f} "
            f"regime={regime:<8s} "
            f"step_floor_ms={step_ms:<9.2f} "
            f"per_token_floor_ms={step_ms / batch:.3f}"
        )
    print()

    # Flush so the graded stdout block stays ahead of the stderr measurements in
    # the session log even when stdout is redirected to a pipe.
    sys.stdout.flush()

    use_cuda = torch.cuda.is_available() and torch.cuda.device_count() > 0
    measure_machine(torch.device("cuda" if use_cuda else "cpu"))


if __name__ == "__main__":
    main()
