# Drill: Inference Arithmetic

The serving numbers, under a clock.

These are the estimates that come up in a systems-flavoured technical discussion, and the ones a candidate is most often asked to produce live: *how many GPUs, how many tokens per second, what batch size fits, how much does speculation buy.*

## Conventions

- **Decimal units.** 1 GB is $10^9$ bytes.
- **KV cache** $= 2 \cdot L \cdot G \cdot d_h \cdot \text{bytes} \cdot S$ per sequence.
- **Decode is bandwidth-bound**, so tokens per second per sequence ≈ bandwidth ÷ bytes read per token, and bytes read ≈ model size in bytes.
- **H100**: 3.35 TB/s HBM, 80 GB, ~990 TFLOP/s dense bf16.
- **Speculative yield**: $(1-\alpha^{\gamma+1})/(1-\alpha)$ expected tokens per verification step.

## Target

85% at 20 prompts in 150 seconds.

The last three item types — token rate, batch capacity, and speculative yield — are the ones worth the most, because they are the ones that turn "it depends" into an answer.
