# Quiz strategy

For each question, silently fill in this sentence:

> The tensor being changed is _____, and the bottleneck being targeted is _____.

That one sentence usually reveals the answer.

## Quick review

- **Weights** are fixed model parameters. Quantizing them helps model fit and
  weight bandwidth.
- **Activations** are produced by the current input. Quantizing them can speed
  matmuls on supported hardware but needs careful scaling.
- **KV cache** grows with context length and active requests. It is separate
  from model-weight storage.
- **Groupwise quantization** uses local scales. Smaller groups usually reduce
  error but increase metadata.
- **QLoRA** keeps the large base model quantized and trains small adapter
  updates.
- **FP8/FP4** are compelling when hardware and kernels support them directly.

## Going deeper

After the quiz, read:

- QLoRA paper: https://arxiv.org/abs/2305.14314
- TensorRT-LLM quantization docs: https://nvidia.github.io/TensorRT-LLM/latest/features/quantization.html
- Hugging Face PEFT LoRA guide: https://huggingface.co/docs/peft/developer_guides/lora

The next module connects these ideas to adapter systems: one base model, many
small task-specific updates, and a new set of serving tradeoffs.
