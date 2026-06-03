"""Estimate simple decode-time memory and compute budgets."""


def kv_cache_gib(layers, kv_heads, head_dim, tokens, bytes_per_value):
    # TODO: return KV cache capacity in GiB for one request.
    return ...


def main():
    params_b = 70
    weight_bytes = 2
    bandwidth_gb_s = 3350
    peak_tflop_s = 989

    layers = 80
    head_dim = 128
    tokens = 8192
    kv_bytes = 2

    # TODO: compute weight_gb, flops_gflop, memory_ms, and compute_ms.

    print("=== 70B decode roofline ===")
    print(f"weight read: {weight_gb:.1f} GB")
    print(f"matmul work: {flops_gflop:.1f} GFLOP")
    print(f"memory lower bound: {memory_ms:.2f} ms")
    print(f"compute lower bound: {compute_ms:.3f} ms")
    print(f"bottleneck guess: {bottleneck}")
    print(f"GQA KV cache: {gqa_cache:.2f} GiB")
    print(f"MHA KV cache: {mha_cache:.2f} GiB")


if __name__ == "__main__":
    main()

