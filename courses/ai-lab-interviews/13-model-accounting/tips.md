# The Numbers to Memorize

| Fact | Value |
|---|---|
| Parameters per layer | $12d^2$ |
| Training FLOPs | $6ND$ |
| Inference FLOPs per token | $2N$ |
| bf16 weights | 2 bytes/param |
| Adam training state | 16 bytes/param |
| H100 dense bf16 peak | ~990 TFLOP/s |
| H100 HBM bandwidth | ~3.35 TB/s |
| H100 memory | 80 GB (SXM) |
| Good MFU | 30–50% |
| $\ln V$ at 32k vocab | 10.4 |

# Worked Answers

**"Can I full-fine-tune a 7B on one 80 GB GPU?"**
> No. 16 bytes per parameter of training state is 112 GB before activations. Quantizing the Adam moments to 8 bits takes the optimizer state from 8 bytes per parameter to 2, so the total goes to 10 — 70 GB plus activations, which is tight but survivable with aggressive checkpointing and a small batch. LoRA is the real answer: the base stays frozen in bf16 at 14 GB, and adapter state is megabytes.

**"How many H100s to serve Llama-2-70B at 32k context, batch 16?"**
> Weights 140 GB in bf16. Cache is $2 \times 80 \times 8 \times 128 \times 2 = 0.33$ MB per token, times 32k times 16 sequences ≈ 172 GB. Total ~312 GB, so 4 GPUs minimum on capacity and realistically more for headroom. If that is too many, the levers are int8 weights and KV-cache quantization.

**"How long to train a 7B on 1T tokens with 256 H100s?"**
> $6 \times 7\times10^9 \times 10^{12} = 4.2\times10^{22}$ FLOPs. At 40% MFU, $256 \times 9.9\times10^{14} \times 0.4 = 1.0\times10^{17}$ FLOP/s. About $4.2\times10^5$ seconds — roughly five days.

# Traps

- **Quoting 16 bytes/param as if it were specific to fp32.** Standard bf16 mixed precision is also 16, because of the fp32 master copy and fp32 moments. Mixed precision buys throughput.
- **Forgetting attention FLOPs at long context.** $6ND$ excludes the $O(S^2)$ term. At 128k it dominates.
- **Assuming peak FLOPs.** Always apply an MFU factor and say what you assumed.
- **Mixing $10^9$ and $2^{30}$.** Pick decimal, say so, move on.
- **Forgetting the KV cache scales with batch.** The per-sequence number is the easy half.

# Further Reading

- [How to Scale Your Model](https://jax-ml.github.io/scaling-book/) — the best single reference for this material, with the systems reasoning attached.
- [Transformer Inference Arithmetic](https://kipp.ly/transformer-inference-arithmetic/) — a short, precise treatment of the inference side.
- [Reducing Activation Recomputation in Large Transformer Models](https://arxiv.org/abs/2205.05198) — where the activation-memory constants come from.
- The **Model Optimization Systems** track in this library goes considerably deeper on the serving side of all of this.
