# Quantization checkpoint

This quiz checks whether you can separate the major quantization use cases
without collapsing them into one vague "make it smaller" idea.

Before starting, review the five questions that matter in practice:

1. Which tensor is being quantized?
2. Is the method post-training, training-aware, or adapter-based?
3. Is the goal memory capacity, bandwidth, throughput, latency, or
   fine-tuning cost?
4. Does the hardware and serving stack accelerate the chosen format?
5. What quality metric would reveal a bad tradeoff?

You should be comfortable distinguishing:

- fitting model weights into memory;
- reducing weight bandwidth during decode;
- training adapters on a quantized base model;
- compressing KV cache for long-context serving;
- using FP8 or FP4 only when kernels and hardware support them well;
- choosing groupwise scales to reduce local outlier damage.

## How to take this quiz

Read each question as a systems question, not a vocabulary question. If a
question mentions context length, think about tensors that grow with tokens. If
it mentions QLoRA, think about which weights are frozen and which weights are
trained. If it mentions groupwise INT4, think about local scales and metadata.

The quiz is short, but it sits at an important transition. The next module
moves from compression to adaptation: LoRA and QLoRA. QLoRA only makes sense if
you already understand what is quantized, what remains trainable, and why that
changes memory cost.
