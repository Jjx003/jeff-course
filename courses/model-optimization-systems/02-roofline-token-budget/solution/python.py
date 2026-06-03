"""Estimate simple decode-time memory and compute budgets."""


def kv_cache_gib(layers, kv_heads, head_dim, tokens, bytes_per_value):
    values = layers * kv_heads * head_dim * 2 * tokens
    return values * bytes_per_value / (1024 ** 3)


def main():
    params_b = 70
    weight_bytes = 2
    bandwidth_gb_s = 3350
    peak_tflop_s = 989

    layers = 80
    head_dim = 128
    tokens = 8192
    kv_bytes = 2

    weight_gb = params_b * weight_bytes
    flops_gflop = 2 * params_b
    memory_ms = weight_gb / bandwidth_gb_s * 1000
    compute_ms = flops_gflop / (peak_tflop_s * 1000) * 1000
    bottleneck = "memory" if memory_ms > compute_ms else "compute"

    gqa_cache = kv_cache_gib(layers, 8, head_dim, tokens, kv_bytes)
    mha_cache = kv_cache_gib(layers, 64, head_dim, tokens, kv_bytes)

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

