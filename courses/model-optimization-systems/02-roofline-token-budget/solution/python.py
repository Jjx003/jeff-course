"""
Reference solution for module 02.
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
    return torch.empty(0, dtype=dtype).element_size()


def tensor_bytes(t: torch.Tensor) -> int:
    return t.numel() * t.element_size()


def kv_slab(kv_heads: int) -> torch.Tensor:
    """One token's keys and values for every layer, at real dtype and shape."""
    return torch.empty(LAYERS, 2, kv_heads, HEAD_DIM, dtype=KV_DTYPE)


def kv_cache_gib(slab: torch.Tensor, tokens: int) -> float:
    return tensor_bytes(slab) * tokens / 1024**3


def decode_flops(batch: int) -> int:
    """Approximate matmul FLOPs for one decode step: 2 FLOPs per weight per sequence."""
    return 2 * PARAMS * batch


def ridge_point() -> float:
    """FLOPs per byte at which peak compute and peak bandwidth are balanced."""
    return (PEAK_TFLOP_S * 1e12) / (BANDWIDTH_GB_S * 1e9)


def time_op(fn, device: torch.device) -> tuple[float, float]:
    """Return (best, median) seconds over MEASURE_REPS timed calls."""
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

    samples.sort()
    return samples[0], samples[len(samples) // 2]


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
        # Bytes moved = one full read of x plus one full write of y.
        elementwise_bytes = tensor_bytes(x) + tensor_bytes(y)
        best, median = time_op(lambda: torch.add(x, 1.0, out=y), device)
        gb_s = elementwise_bytes / best / 1e9
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
        matmul_flops = 2 * n**3
        matmul_bytes = tensor_bytes(a) + tensor_bytes(b) + tensor_bytes(c)
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
    memory_ms = weight_bytes / (BANDWIDTH_GB_S * 1e9) * 1e3
    compute_ms = flops / (PEAK_TFLOP_S * 1e12) * 1e3
    bottleneck = "memory" if memory_ms > compute_ms else "compute"

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
        batch_flops = decode_flops(batch)
        intensity = batch_flops / weight_bytes
        batch_compute_ms = batch_flops / (PEAK_TFLOP_S * 1e12) * 1e3
        step_ms = max(memory_ms, batch_compute_ms)
        regime = "memory" if intensity < ridge else "compute"
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
