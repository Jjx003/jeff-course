## Walkthrough

### Arithmetic intensity

```python
return flops / bytes_moved
```

Arithmetic intensity says how much math you get per byte fetched or stored. A
matrix multiply can reuse each loaded tile many times, so its intensity can be
high. A normalization kernel may touch each value only a few times, so its
intensity is low.

The validation matters because `bytes_moved = 0` would make the model
meaningless.

### Roofline throughput

```python
bandwidth_limited = bandwidth_tb_s * intensity_flops_per_byte
return min(peak_tflops, bandwidth_limited)
```

With decimal units, `TB/s * FLOP/byte` lands in `TFLOP/s`. The minimum chooses
the active bottleneck. If the bandwidth-limited number is below peak, memory is
the limiter. If it is above peak, compute is the limiter.

### Model capacity

```python
raw_bytes = parameter_count_b * 1e9 * bytes_per_parameter
total_bytes = raw_bytes * (1 + overhead_pct / 100)
return total_bytes / 1e9
```

The overhead is a placeholder for reality: metadata, padding, runtime buffers,
extra copies, communication workspaces, and fragmentation. Production systems
usually need more memory than the raw parameter file suggests.

### KV cache

```python
total_bytes = layers * 2 * hidden_size * sequence_length * bytes_per_value
```

Each layer stores keys and values for previous tokens. During decode, the model
adds one new token at a time but attends back over the cached context. Longer
context therefore consumes HBM even when the model weights are unchanged.

## What the numbers say

The `dense_matmul` scenario reaches the 800 TFLOP/s compute roof because its
intensity is high enough. The `attention_scores` and `layer_norm` examples are
bandwidth-bound on this toy chip. More tensor cores would not fix those cases;
more bandwidth, better locality, or a different algorithm would.

The sizing outputs show the other half of HBM value. A 70B fp16 model with
modest overhead already wants 168 GB before KV cache. Long-context serving can
add tens of GB more per stream. This is why HBM stack count, capacity per stack,
and packaging capacity are central to AI accelerator competition.
