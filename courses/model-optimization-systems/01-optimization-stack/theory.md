# A map of bottlenecks

Optimization work is easier when you can name the limiting resource. The
surface symptom may be "tokens are slow" or "the GPU is full", but those
phrases hide several different mechanisms. A server can be slow because it is
reading weights too often, because it cannot fit enough KV cache, because it is
launching many small kernels, because requests arrive in awkward shapes, or
because the quality-preserving optimization has not been calibrated for the
task.

The clean mental model is a budget table:

| Budget | Unit | Grows with | Typical fixes |
|---|---|---|---|
| Weight storage | bytes | parameter count and dtype | quantization, sharding, pruning |
| Weight bandwidth | bytes/s | decode tokens and active replicas | batching, quantization, caching |
| FLOPs | operations | layers, hidden size, sequence length | faster kernels, lower precision |
| Activation memory | bytes | batch, sequence, hidden size | checkpointing, recomputation, fusion |
| KV cache | bytes | batch, context, layers, KV heads | GQA, paging, compression |
| Scheduler overhead | time | request churn and fragmentation | continuous batching, routing |

No single row is "the" optimization problem. Production work is the art of
moving pressure from a scarce resource to a less scarce one without damaging
model quality too much.

## Memory-bound versus compute-bound

The two lower bounds from the first module are deliberately simple:

$$
t_\text{memory} \ge \frac{B}{\beta}
$$

where $B$ is bytes moved and $\beta$ is memory bandwidth, and:

$$
t_\text{compute} \ge \frac{F}{\phi}
$$

where $F$ is FLOPs and $\phi$ is peak compute throughput.

The ratio

$$
I = \frac{F}{B}
$$

is called **arithmetic intensity**. It measures work per byte. If a kernel has
low arithmetic intensity, it is likely memory-bound because each byte does not
produce enough math to hide memory traffic. If it has high arithmetic intensity,
it has a chance to be compute-bound, assuming the implementation maps well to
the hardware.

Attention prefill and attention decode have different intensity. In prefill,
the model can process many prompt positions together. In decode, each new token
queries cached keys and values and then passes through MLP blocks. The MLP
weights may be read again and again for each generated token, so weight
bandwidth becomes central.

## The hidden cost of "just batch it"

Batching increases reuse. If multiple requests generate a token at the same
time, the server can apply the same weights to a larger matrix instead of many
tiny vectors. That increases arithmetic intensity and often improves hardware
utilization.

But batching has costs:

| Benefit | Cost |
|---|---|
| better Tensor Core utilization | more KV cache resident at once |
| fewer tiny kernels | more complex scheduling |
| higher throughput | possible latency increase |
| better weight reuse | padding or shape fragmentation |

Interactive systems care about both throughput and latency. A server that
maximizes tokens per second by waiting too long to form a giant batch may feel
bad to a user. A server that always responds immediately with batch size one
may waste the GPU. Continuous batching exists because static batches do not
match real request arrivals.

## KV cache as a first-class object

The KV cache stores attention keys and values for previous tokens. A useful
shape formula for one request is:

$$
\text{KV bytes} =
L_\text{layers}
\times T
\times H_\text{kv}
\times D_\text{head}
\times 2
\times b
$$

where $T$ is context length, $H_\text{kv}$ is the number of key/value heads,
the factor of 2 accounts for keys and values, and $b$ is bytes per stored
number.

Grouped-query attention (GQA) reduces $H_\text{kv}$ while keeping more query
heads. That is an architectural choice with serving consequences. A model with
64 query heads and 8 KV heads stores one eighth as many KV heads as full
multi-head attention would. For long context and many active users, that is not
a small detail; it is the difference between serving comfortably and running
out of memory.

## Kernel fusion and layout

Some optimizations do not change the model at all. They change how operations
are scheduled. A transformer block contains many pieces that are mathematically
small compared with matmuls: RMSNorm, rotary embedding, bias additions,
activation functions, reshapes, transposes, and residual adds. If each piece
becomes a separate kernel that reads and writes global memory, the overhead can
be significant.

Fusion keeps intermediate values close to the compute units. FlashAttention is
the canonical example in attention: rather than materializing the full
$T \times T$ attention matrix, it tiles the computation and maintains a
streaming softmax. Fused MLP kernels, fused normalization, and fused rotary
embedding follow the same spirit. The optimization is not "change the
equation"; it is "do the same equation with less traffic and fewer launches."

## Production engines

The ideas in this course show up in real systems:

- vLLM popularized PagedAttention for KV-cache memory management and
  high-throughput serving.
- TensorRT-LLM exposes optimized attention kernels, in-flight batching,
  quantization recipes, paged KV cache, and speculative decoding.
- FlashAttention-3 targets Hopper GPUs with asynchronous data movement,
  Tensor Cores, TMA, FP8 support, and better overlap of matmul and softmax.
- Hugging Face, PEFT, bitsandbytes, AutoGPTQ-style tooling, and vendor model
  optimizers make low-bit deployment accessible, with different quality and
  hardware tradeoffs.
- Protein language model work borrows the LLM toolbox but must also handle
  sequence packing, pair tensors, structure heads, and domain-specific
  evaluation.

## How to read optimization claims

Every optimization paper or vendor benchmark should trigger the same checklist:

1. What was the baseline?
2. What hardware was used?
3. Was the workload prefill, decode, training, fine-tuning, or batch offline
   inference?
4. What quality metric was preserved?
5. Did the method reduce bytes, reduce FLOPs, improve utilization, or improve
   scheduling?
6. What new metadata, calibration, kernel dependency, or operational complexity
   did it introduce?

The last question matters. Low-bit weights may require scale metadata.
Speculative decoding may need a second model. Adapter serving may complicate
batching. KV paging may reduce fragmentation but add bookkeeping. There are no
free optimizations, only trades that are favorable in a particular setting.

## Protein models are not just LLMs

The same budget table applies to protein models, but the growth terms differ.
A protein language model that only embeds sequences is close to an LLM in
shape: token sequence in, hidden states out. A folding model is more complex.
Pair representations can scale like $L^2$, structure modules may recycle
several times, and diffusion-style systems may run repeated denoising steps.

This is why the course returns to protein workloads near the end. The lesson is
not that every LLM optimization transfers perfectly. The lesson is that a good
systems engineer can re-derive the bottleneck from tensor shapes, memory
traffic, and workload constraints.

## References and reading strategy

Use these as anchors while taking the course:

- FlashAttention-3 paper: https://arxiv.org/abs/2407.08608
- vLLM / PagedAttention paper: https://arxiv.org/abs/2309.06180
- NVIDIA TensorRT-LLM overview: https://developer.nvidia.com/tensorrt-llm
- TensorRT-LLM quantization docs: https://nvidia.github.io/TensorRT-LLM/latest/features/quantization.html
- Hugging Face bitsandbytes quantization docs: https://huggingface.co/docs/transformers/quantization/bitsandbytes
- QLoRA paper: https://arxiv.org/abs/2305.14314
- AlphaFold 3 paper: https://www.nature.com/articles/s41586-024-07487-w
- Chai-1 technical report: https://chaiassets.com/chai-1/paper/technical_report_v1.pdf
- Boltz-2 paper: https://pmc.ncbi.nlm.nih.gov/articles/PMC12262699/
- Efficient inference, training, and fine-tuning of protein language models: https://www.sciencedirect.com/science/article/pii/S2589004225017560
