# Rapid-Fire Answers

**"What is 5D parallelism?"**
> Data, tensor, pipeline, context, and expert. Data splits the batch and all-reduces gradients. Tensor splits matrices within a layer, two all-reduces per layer, so it stays inside a node. Pipeline splits layers across devices with cheap point-to-point communication but a bubble. Context splits the sequence, needing KV gathering in attention. Expert splits MoE experts, needing all-to-all routing.

**"Why does tensor parallelism stay inside a node?"**
> Two all-reduces per layer on both forward and backward, all on the critical path. NVLink is around 900 GB/s; inter-node InfiniBand is 50–100. An order of magnitude of bandwidth on the most communication-heavy axis.

**"Why column-then-row for the FFN split?"**
> Column-splitting the up projection lets each device apply the elementwise nonlinearity to its own complete columns with no communication. Row-splitting the down projection then matches, so a single all-reduce at the end sums the partials. Row-splitting first would force a collective before the nonlinearity, doubling the count.

**"ZeRO stages?"**
> 1 shards optimizer state — the fp32 master and both moments, 12 of 16 bytes per parameter, essentially free. 2 adds gradients, replacing the all-reduce with a reduce-scatter, at identical communication volume because all-reduce already decomposes that way. 3 adds parameters, gathered just in time per layer, costing about 50% more communication.

**"What is the pipeline bubble?"**
> $(P-1)/(M+P-1)$ idle fraction with $P$ stages and $M$ microbatches. Shrink it with more microbatches, 1F1B scheduling to reduce in-flight activation memory, interleaved stages, or zero-bubble schedules that split the backward pass in two.

**"How would you shard a 70B model for training on one 8-GPU node?"**
> You would not, for full fine-tuning — 1.12 TB of training state against 640 GB. TP 8 plus ZeRO gets you to roughly 140 GB per device, still over. On one node the answer is LoRA on a frozen bf16 base. Full fine-tuning needs multiple nodes with pipeline parallelism between them.

# Traps

- **Listing the five axes without their communication costs.** The costs are the content.
- **Saying pipeline parallelism has no communication.** It has little, and it has a bubble instead.
- **Treating ZeRO-3 and FSDP as different algorithms.** Same idea, different lineage; FSDP is the native PyTorch path.
- **Forgetting that TP shards activations too**, which is a large part of why it helps.
- **Ignoring that all-to-all in MoE makes load imbalance a systems problem**, not just a quality one.

# Further Reading

- [How to Scale Your Model](https://jax-ml.github.io/scaling-book/) — the best treatment of this material anywhere, with the arithmetic worked through.
- [Megatron-LM](https://arxiv.org/abs/1909.08053) — the tensor-parallel FFN and attention splits.
- [ZeRO](https://arxiv.org/abs/1910.02054) — the memory arithmetic for all three stages.
- [GPipe](https://arxiv.org/abs/1811.06965) and [PipeDream](https://arxiv.org/abs/1806.03377) — pipeline schedules and the bubble.
- [Ring Attention](https://arxiv.org/abs/2310.01889) — context parallelism.
- The **Model Optimization Systems** track has a coding module that builds a tensor-parallel block and verifies it against its unsharded twin.
