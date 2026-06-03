# Practical hints

Start with BF16 as the baseline. Then ask what pressure you are trying to
relieve:

| Problem | First quantization idea |
|---|---|
| model does not fit | weight quantization |
| decode is bandwidth-bound | weight-only INT4 or INT8 |
| matmuls are compute-bound on supported hardware | FP8 or FP4 kernels |
| long-context serving runs out of memory | KV-cache quantization |
| fine-tuning needs too much memory | QLoRA or other PEFT methods |

Do not mix these up. A method that shrinks weights does not automatically shrink
the KV cache. A method that accelerates FP8 matmuls does not automatically make
adapter routing cheap. A method that preserves perplexity may still damage a
domain-specific metric.

## Questions to ask before choosing a format

1. Which tensor is quantized: weights, activations, KV cache, optimizer state,
   or adapters?
2. Is the method post-training, quantization-aware training, or
   adapter-based?
3. Is the target capacity, bandwidth, throughput, latency, or fine-tuning cost?
4. Does the hardware have native kernels for the format?
5. What metadata is stored, and how expensive is dequantization?
6. What quality metric would catch failure for this workload?

## Common traps

- Treating all 4-bit methods as equivalent.
- Forgetting scale metadata when estimating memory.
- Calibrating on data that does not match deployment prompts.
- Reporting only average latency while ignoring tail latency.
- Testing protein models on random splits that share close homologs.
- Assuming a vendor-optimized path exists in your open-source serving stack.

## Going deeper

- QLoRA: https://arxiv.org/abs/2305.14314
- TensorRT-LLM quantization: https://nvidia.github.io/TensorRT-LLM/latest/features/quantization.html
- Hugging Face quantization guide: https://huggingface.co/docs/transformers/quantization/bitsandbytes
- FlashAttention-3 for FP8 attention context: https://arxiv.org/abs/2407.08608
- SmoothQuant: https://arxiv.org/abs/2211.10438

As you read, keep a small table with columns for tensor, bit width, calibration
data, hardware target, and quality metric. That table usually reveals whether a
paper's claim transfers to your system.
