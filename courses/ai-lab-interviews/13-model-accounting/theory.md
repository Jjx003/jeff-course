# Parameters

$$N \approx 12Ld^2 + Vd$$

Per layer: $4d^2$ for $W_Q, W_K, W_V, W_O$, and $8d^2$ for the FFN. Plus $Vd$ for the embedding, doubled if the output head is untied.

Corrections, in the order they matter:

- **GQA** shrinks $W_K$ and $W_V$ by $G/H$, so attention becomes $2d^2(1 + G/H)$ rather than $4d^2$. At $G/H = 1/8$ that takes attention from $4d^2$ to $2.25d^2$ — a 15% cut to the whole layer.
- **Norm parameters** are $2d$ per layer. Negligible, but mention them and stop.
- **MoE** multiplies the FFN term by the number of experts while leaving per-token FLOPs at top-$k$.

## Practice estimates

| Model | $L$ | $d$ | $V$ | $12Ld^2$ | $+Vd$ | Estimate | Actual |
|---|---|---|---|---|---|---|---|
| GPT-2 small | 12 | 768 | 50257 | 85M | 39M | 124M | 124M |
| Llama-2 7B | 32 | 4096 | 32000 | 6.44B | 0.13B | 6.6B | 6.7B |
| Llama-2 70B | 80 | 8192 | 32000 | 64.4B | 0.26B | 64.7B | 69B |

The 70B gap is GQA (which subtracts) and a larger-than-$8d^2$ FFN (which adds more). Landing within 10% while narrating the structure is the goal, not exactness.

# FLOPs

## The 6N rule

$$C \approx 6ND$$

for $N$ parameters and $D$ training tokens. The 6 decomposes as:

- **2 for the forward pass.** Every parameter participates in one multiply and one add per token.
- **4 for the backward pass.** Two matmuls per layer — one for the input gradient, one for the parameter gradient — each costing the same as the forward matmul.

Inference is the forward pass alone: $2N$ FLOPs per token.

**What 6N excludes:** attention score computation, which is $O(S^2)$ rather than $O(N)$. With causal masking the attention term is roughly $6LSd$ per token — a fraction $S/(12d)$ of the $6N$ estimate. Negligible for most pretraining ($S = 4096$, $d = 8192$ gives 4%), and very much not negligible at long context: at 128k and $d = 8192$ the ratio is $131072/98304 \approx 1.3$, so the attention FLOPs *exceed* the parameter FLOPs. The correct interview answer names the rule *and* its exclusion.

(Without a causal mask the same count is $12LSd$, since you would compute the full $S\times S$ score matrix rather than half of it. Both conventions appear in the literature; say which you are using.)

## Worked: how long does a pretraining run take?

Llama-2-70B: $N = 7\times10^{10}$, $D = 2\times10^{12}$ tokens.

$$C = 6 \times 7\times10^{10} \times 2\times10^{12} = 8.4\times10^{23}\ \text{FLOPs}$$

On 1024 H100s at ~990 TFLOP/s dense bf16 peak, with 40% model FLOPs utilization:

$$\text{effective} = 1024 \times 9.9\times10^{14} \times 0.4 = 4.1\times10^{17}\ \text{FLOP/s}$$

$$t = \frac{8.4\times10^{23}}{4.1\times10^{17}} \approx 2.0\times10^{6}\ \text{s} \approx 24\ \text{days}$$

**MFU is the number to have opinions about.** 30–50% is a well-tuned large-scale run. Below 20% something is wrong — usually communication, a small batch, or a bad parallelism configuration. Above 60% is exceptional. Quoting an MFU range unprompted signals you have looked at a real training dashboard.

# Memory

![Stacked bars showing training memory for a 7B model under five strategies, split into weights, gradients, optimizer state and activations, against an 80 GB line.](/courses/ai-lab-interviews/training-memory.svg)

## Training

Per parameter, in the standard bf16 mixed-precision setup:

| Item | Bytes |
|---|---|
| fp32 master weights | 4 |
| bf16 working weights | 2 |
| bf16 gradients | 2 |
| Adam first moment (fp32) | 4 |
| Adam second moment (fp32) | 4 |
| **Total** | **16** |

So **16 bytes per parameter**, plus activations. A 7B model needs 112 GB of state before a single activation — which is why full fine-tuning a 7B on one 80 GB GPU does not work, and why that question is asked so often.

The pure-fp32 setup is also 16 bytes (4+4+4+4). Mixed precision buys throughput, not memory. That surprises people and is a good thing to say.

## Activation memory

$$M_{act} \approx s \cdot b \cdot S \cdot d \cdot L$$

with $s$ between roughly 10 and 30 bytes per element-position depending on what the implementation stores and whether attention is fused.

The exact constant is not worth memorizing. What is worth knowing:

- Activation memory scales with **batch × sequence**, unlike everything else, which is why it is the term you attack first when you run out.
- **Gradient checkpointing** cuts it to $O(\sqrt{L})$ for roughly 33% more compute.
- The **logit tensor** — $b \times S \times V$ in fp32 — is often the single largest activation. At $b=8$, $S=4096$, $V=128000$ that is 16 GB for one tensor, which is why chunked and fused cross-entropy implementations exist.

## Inference

$$M = N \times \text{bytes/param} + \text{KV cache} + \text{activations}$$

Activations are small at inference — one layer's worth at a time, not the whole forward pass — so it is weights plus cache.

$$\text{KV bytes} = 2 \cdot L \cdot G \cdot d_h \cdot b \cdot S \cdot \text{bytes per element}$$

## Worked: serving Llama-2-70B at 128k context

Weights in bf16: 140 GB. Already two 80 GB GPUs.

Cache per token: $2 \times 80 \times 8 \times 128 \times 2 = 327{,}680$ bytes ≈ 0.33 MB.

At 128k context: $0.33 \times 131072 \approx 43$ GB **per sequence**.

So: 2 GPUs hold the weights with 20 GB spare, which serves *zero* full-context sequences. Realistically 4 GPUs — and even then 180 GB of headroom at 43 GB per sequence is about four concurrent requests at full context. This is why long-context serving is hard, and why KV quantization and paged attention exist.

(For an MLA model the $2 \cdot G \cdot d_h$ term is replaced by the cached latent width — DeepSeek-V3 stores 576 elements per layer per token instead of 2048 for a GQA-8 model at head dim 128 — which is exactly the arithmetic that motivated MLA.)

![Two panels showing KV cache size against context length and against batch size, for MHA, GQA and MQA, with an HBM headroom line.](/courses/ai-lab-interviews/kv-cache-growth.svg)

# Arithmetic Intensity

The concept that ties compute and memory together: FLOPs performed per byte moved.

$$I = \frac{\text{FLOPs}}{\text{bytes read}}$$

Compare it to the hardware's ratio of peak FLOP/s to memory bandwidth — the **ridge point**. For an H100, roughly $990/3.35 \approx 295$ FLOP/byte. Below that you are memory-bound; above it, compute-bound.

- **Prefill** processes many tokens against each weight read, so intensity is high and it is compute-bound.
- **Decode** reads every weight to produce one token per sequence, so intensity is roughly the batch size — deeply memory-bound at any realistic batch.

This single fact explains continuous batching, GQA, weight-only quantization, and speculative decoding all at once. It is the highest-leverage concept in inference systems and worth being able to derive on a whiteboard.

![A roofline plot for an H100 with prefill and several decode batch sizes placed on it by arithmetic intensity.](/courses/ai-lab-interviews/roofline-decode.svg)
