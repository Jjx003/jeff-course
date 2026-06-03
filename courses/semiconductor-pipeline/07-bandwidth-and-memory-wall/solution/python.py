"""
Reference solution for bandwidth and memory-wall sizing.
"""


def arithmetic_intensity(flops: float, bytes_moved: float) -> float:
    """Return FLOPs per byte moved."""
    if bytes_moved <= 0:
        raise ValueError("bytes_moved must be positive")
    return flops / bytes_moved


def roofline_tflops(
    peak_tflops: float,
    bandwidth_tb_s: float,
    intensity_flops_per_byte: float,
) -> float:
    """Return attainable TFLOP/s under a simple roofline model."""
    bandwidth_limited = bandwidth_tb_s * intensity_flops_per_byte
    return min(peak_tflops, bandwidth_limited)


def hbm_capacity_for_model(
    parameter_count_b: float,
    bytes_per_parameter: float,
    overhead_pct: float,
) -> float:
    """Return model weight memory plus overhead in decimal GB."""
    raw_bytes = parameter_count_b * 1e9 * bytes_per_parameter
    total_bytes = raw_bytes * (1 + overhead_pct / 100)
    return total_bytes / 1e9


def token_kv_cache_gb(
    layers: int,
    hidden_size: int,
    sequence_length: int,
    bytes_per_value: float,
) -> float:
    """Return approximate KV-cache memory for one token stream in decimal GB."""
    total_bytes = layers * 2 * hidden_size * sequence_length * bytes_per_value
    return total_bytes / 1e9


def main() -> None:
    peak_tflops = 800.0
    bandwidth_tb_s = 3.35
    scenarios = [
        ("attention_scores", 1.6e12, 1.0e11),
        ("dense_matmul", 2.8e14, 1.0e12),
        ("layer_norm", 7.5e10, 1.0e11),
    ]

    print("Roofline scenarios:")
    for name, flops, bytes_moved in scenarios:
        intensity = arithmetic_intensity(flops, bytes_moved)
        achieved = roofline_tflops(peak_tflops, bandwidth_tb_s, intensity)
        regime = "compute-bound" if achieved == peak_tflops else "bandwidth-bound"
        print(f"  {name}: intensity={intensity:.2f} FLOP/byte -> {achieved:.1f} TFLOP/s ({regime})")

    print()
    print("HBM sizing:")
    model_70b = hbm_capacity_for_model(70, 2, 20)
    model_8b = hbm_capacity_for_model(8, 2, 15)
    kv_cache = token_kv_cache_gb(80, 8192, 32768, 2)
    print(f"  70B weights at 2 bytes + 20% overhead: {model_70b:.1f} GB")
    print(f"  8B weights at 2 bytes + 15% overhead: {model_8b:.1f} GB")
    print(f"  KV cache, 80 layers, hidden 8192, seq 32768, fp16: {kv_cache:.1f} GB")

    print()
    print("Takeaway:")
    print("  Bandwidth decides low-intensity throughput; capacity decides which models and context lengths fit.")


if __name__ == "__main__":
    main()
