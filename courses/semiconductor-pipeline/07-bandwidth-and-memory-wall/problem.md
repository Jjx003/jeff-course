## Goal

Implement four small functions that connect model workloads to accelerator
value:

1. `arithmetic_intensity(flops, bytes_moved)`
2. `roofline_tflops(peak_tflops, bandwidth_tb_s, intensity_flops_per_byte)`
3. `hbm_capacity_for_model(parameter_count_b, bytes_per_parameter, overhead_pct)`
4. `token_kv_cache_gb(layers, hidden_size, sequence_length, bytes_per_value)`

Then use those functions to print a deterministic summary for three toy
workloads.

## Why this matters

AI chips are often marketed by peak TFLOP/s, but many real workloads are limited
by memory movement. A processor with enormous matrix units can still stall if it
cannot feed them from HBM.

The simplest way to reason about this is the **roofline model**:

$$
\text{attainable FLOP/s} =
\min(\text{peak FLOP/s},\ \text{bandwidth} \times \text{arithmetic intensity})
$$

Arithmetic intensity is:

$$
I = \frac{\text{FLOPs}}{\text{bytes moved}}
$$

High-intensity operations reuse data many times and can approach compute peak.
Low-intensity operations stream data once or twice and are bandwidth-bound.

## Required functions

### `arithmetic_intensity(flops, bytes_moved)`

Return `flops / bytes_moved` as FLOPs per byte. If `bytes_moved <= 0`, raise
`ValueError`.

### `roofline_tflops(peak_tflops, bandwidth_tb_s, intensity_flops_per_byte)`

Return the attainable throughput in TFLOP/s:

```text
min(peak_tflops, bandwidth_tb_s * intensity_flops_per_byte)
```

This works because `1 TB/s * 1 FLOP/byte = 1 TFLOP/s` when using decimal units.

### `hbm_capacity_for_model(parameter_count_b, bytes_per_parameter, overhead_pct)`

Return the HBM capacity in GB needed to store model weights plus overhead:

```text
parameter_count_b * 1e9 * bytes_per_parameter * (1 + overhead_pct / 100) / 1e9
```

The `parameter_count_b` argument is in billions of parameters. The result is
decimal GB.

### `token_kv_cache_gb(layers, hidden_size, sequence_length, bytes_per_value)`

Return approximate KV-cache memory in GB for **one token stream**:

```text
layers * 2 * hidden_size * sequence_length * bytes_per_value / 1e9
```

The factor of `2` is for keys and values. This intentionally ignores grouped
query attention, tensor parallel sharding, metadata, and allocator padding so
you can see the base scaling law.

## Expected output

Your script should print exactly:

```text
Roofline scenarios:
  attention_scores: intensity=16.00 FLOP/byte -> 53.6 TFLOP/s (bandwidth-bound)
  dense_matmul: intensity=280.00 FLOP/byte -> 800.0 TFLOP/s (compute-bound)
  layer_norm: intensity=0.75 FLOP/byte -> 2.5 TFLOP/s (bandwidth-bound)

HBM sizing:
  70B weights at 2 bytes + 20% overhead: 168.0 GB
  8B weights at 2 bytes + 15% overhead: 18.4 GB
  KV cache, 80 layers, hidden 8192, seq 32768, fp16: 85.9 GB

Takeaway:
  Bandwidth decides low-intensity throughput; capacity decides which models and context lengths fit.
```
