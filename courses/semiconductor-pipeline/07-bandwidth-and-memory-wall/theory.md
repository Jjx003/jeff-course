## The roofline picture

The roofline model separates two limits:

- **Compute roof:** the maximum math throughput of the chip.
- **Bandwidth roof:** the maximum rate at which operands can be supplied from
  memory.

For a workload with arithmetic intensity $I$, the bandwidth-limited throughput
is:

$$
P_\text{bandwidth} = B \times I
$$

The actual throughput is the lower of the compute roof and the bandwidth roof:

$$
P = \min(P_\text{peak}, B I)
$$

This explains why peak TFLOP/s can be a misleading headline number. A chip can
have excellent compute units and still lose on workloads with poor data reuse.

## Why HBM bandwidth creates value

HBM is expensive, physically constrained, and package-limited, but it gives AI
accelerators the short, wide memory interface they need. More bandwidth helps:

- Attention patterns that stream large matrices.
- Normalization and elementwise kernels.
- Inference decode workloads with small batch sizes.
- Mixture-of-experts routing and parameter movement.

More compute helps only when the workload has enough reuse to feed the units.

## Why HBM capacity creates value

Capacity determines what fits:

- Model weights.
- KV cache for long context.
- Activations for training.
- Optimizer states during training.
- Temporary buffers, communication workspaces, and fragmentation overhead.

For inference, KV cache often becomes the practical limit. It scales linearly
with layers, hidden size, context length, and bytes per stored value:

$$
\text{KV bytes} \approx L \times 2H \times S \times b
$$

where $L$ is layer count, $H$ is hidden size, $S$ is sequence length, and $b$ is
bytes per value.

## Interpreting the exercise

The toy scenarios in this module are deliberately simplified. Real chips have
on-chip SRAM, caches, tensor cores with specific tile shapes, sparsity modes,
interconnect bottlenecks, and software scheduling constraints.

Even so, these formulas are useful because they force the right first question:
is this workload short on math, short on bandwidth, or short on memory capacity?
