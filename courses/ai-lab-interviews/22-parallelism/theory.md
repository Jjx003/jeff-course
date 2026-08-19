# Collective Operations

| Operation | Effect | Volume moved per device |
|---|---|---|
| **broadcast** | one device's tensor to all | $N$ |
| **reduce** | sum all devices' tensors onto one | $N$ |
| **all-reduce** | sum, result on every device | $2N(P-1)/P$ |
| **all-gather** | concatenate every shard onto every device | $N(P-1)/P$ |
| **reduce-scatter** | sum, each device keeps one shard | $N(P-1)/P$ |
| **all-to-all** | every device sends a distinct piece to every other | $N(P-1)/P$ |

Ring all-reduce achieves the bandwidth-optimal $2N(P-1)/P$ by decomposing into a reduce-scatter followed by an all-gather. Each device sends and receives $N/P$ bytes in each of $2(P-1)$ steps.

**The identity to state out loud:** all-reduce = reduce-scatter + all-gather. It is why ZeRO stage 2 is nearly free.

# Data Parallelism

Replicate the model, split the batch, all-reduce the gradients before the optimizer step.

Simple, and the first thing to reach for. Its limit is memory: every device holds the full model plus full optimizer state. A 7B model at 16 bytes per parameter needs 112 GB, so plain data parallelism does not fit on an 80 GB card at all.

## ZeRO

ZeRO removes the redundancy in that replication, stage by stage.

**Stage 1 — shard optimizer state.** Each device keeps $1/P$ of the moments and updates $1/P$ of the parameters, then all-gathers the updated weights. Memory per device drops from $16\Psi$ to $4\Psi + 12\Psi/P$. **This is the big win for the least cost** — the sharded part is the fp32 master copy plus both moments, 12 of the 16 bytes per parameter, leaving only the bf16 weights and gradients replicated — and communication is essentially unchanged.

**Stage 2 — also shard gradients.** Replace the gradient all-reduce with a reduce-scatter, so each device only ever holds the gradient shard it needs. Memory drops to $2\Psi + 14\Psi/P$. Communication volume is *identical* to stage 1, because all-reduce was already reduce-scatter + all-gather.

**Stage 3 — also shard parameters.** Each device holds $1/P$ of the weights and all-gathers a layer's parameters just before using it, then frees them. Memory becomes $16\Psi/P$. Communication rises by about 50%, since parameters are gathered in both the forward and backward passes.

**FSDP** is PyTorch's implementation of the stage-3 idea, organized around wrapping modules rather than a separate optimizer. Same principle, different ergonomics — and the right answer to "ZeRO-3 versus FSDP" is that they are the same algorithm from different lineages, with FSDP being the native PyTorch path.

# Tensor Parallelism

Split individual weight matrices across devices, so a single layer's computation is distributed.

## The FFN, done right

For $Y = \mathrm{GeLU}(XA)B$:

- Split $A$ **column-wise**: $A = [A_1, A_2]$. Each device computes $\mathrm{GeLU}(XA_i)$ independently — no communication, because GeLU is elementwise and each column block is self-contained.
- Split $B$ **row-wise** to match: $B = [B_1; B_2]$. Each device computes $\mathrm{GeLU}(XA_i)B_i$, and one all-reduce sums the partial results.

**One all-reduce per FFN.** Splitting $A$ row-wise instead would force a communication *before* the nonlinearity, doubling the collectives. The column-then-row pairing is the whole trick, and being able to explain why is a strong signal.

## Attention

Natural: give each device a subset of heads. $W_Q, W_K, W_V$ split column-wise, $W_O$ row-wise, one all-reduce at the end. Same pattern.

## The constraint

Two all-reduces per layer, on every forward and every backward pass. At 80 layers that is hundreds of collectives per step, each on the critical path.

This is why **tensor parallelism stays inside the NVLink domain**, where NVLink offers ~900 GB/s per GPU, rather than crossing to InfiniBand at ~50–100 GB/s. TP degree 8 on an 8-GPU node is the standard configuration, and "why not TP across nodes?" is a common follow-up whose answer is exactly this bandwidth ratio. The 2026 wrinkle worth knowing: rack-scale systems like GB200 NVL72 put 72 GPUs in a single NVLink domain, so "inside a node" is becoming "inside the NVLink domain" — the principle is unchanged, but the domain got bigger.

**Sequence parallelism** is the usual companion: the parts of a layer that TP leaves replicated — the norms and dropout — are split along the sequence axis instead, converting some all-reduces into reduce-scatter/all-gather pairs and cutting activation memory.

# Pipeline Parallelism

Assign consecutive layers to different devices; activations flow forward stage to stage, gradients flow back.

Communication is tiny — point-to-point activations at stage boundaries, not collectives — which makes it the right axis for crossing slow interconnects.

## The bubble

With $P$ stages and $M$ microbatches, the naive schedule idles for a fraction

$$\text{bubble} = \frac{P-1}{M+P-1}$$

At $P=4$, $M=4$: 43% of the time wasted. At $M=32$: 8.6%.

**Fixes, in the order they were invented:**

- **More microbatches.** Simple, and limited by activation memory.
- **1F1B (one-forward-one-backward).** Same bubble fraction, but each device holds far fewer in-flight activations, so you can afford more microbatches.
- **Interleaved stages.** Give each device several non-contiguous layer chunks. The bubble shrinks by the interleaving factor at the cost of more communication.
- **Zero-bubble schedules.** Split the backward pass into its input-gradient and weight-gradient halves and reorder them, since the weight gradient is not on the critical path.

# Context and Expert Parallelism

**Context (sequence) parallelism** splits the sequence across devices. Every operation except attention is local; attention needs each query to see all keys, so K and V are gathered — Ring Attention overlaps that transfer with computation, passing KV blocks around a ring. This is how million-token context windows are trained.

**Expert parallelism** places different MoE experts on different devices. Routing becomes an all-to-all: every device sends each token to whichever device holds its chosen expert, and receives the results back. All-to-all is the most bandwidth-hungry collective, and load imbalance directly becomes stragglers, which is why MoE load-balancing losses matter for systems reasons as well as quality ones. At frontier scale the all-to-all is hidden rather than eliminated: DeepSeek-V3's training system is the public example, overlapping dispatch and combine with computation (and limiting each token to experts on a few nodes) so that cross-node routing stays off the critical path.

# Putting It Together

The standard recipe for a large training run:

```
tensor parallel   = 8      within a node, over NVLink
pipeline parallel = 4..16  across nodes
data parallel     = the rest, with ZeRO-1
sequence parallel = on, alongside TP
```

The reasoning to state:

1. **Data parallel + ZeRO-1 first.** Cheapest, and shards three quarters of the training state.
2. **Tensor parallel next, capped at the node.** Use it when a layer will not fit, and never across nodes.
3. **Pipeline parallel across nodes.** Cheap communication, but you pay in bubble and in scheduling complexity.
4. **Context parallel only if the sequence demands it.**
5. **Expert parallel only if the model is an MoE.**

For an interview, that ordering plus the reason for each step is a complete answer.

## Worked: 70B on 8x80 GB

Training state at 16 bytes per parameter: 1.12 TB. Available: 640 GB. It does not fit.

- **TP 8 alone:** parameters and optimizer state split 8 ways gives 140 GB per device. Still over.
- **TP 8 + ZeRO-1:** the optimizer state is already sharded by TP; ZeRO adds little on top of a pure-TP group.
- **LoRA instead:** frozen base at 140 GB in bf16, split 2 ways by TP, plus tiny adapter state. Fits comfortably, and is what almost everyone actually does on a single node.
- **Full fine-tuning realistically needs multiple nodes**, with pipeline parallelism across them.

For **inference**, the same 70B is 140 GB in bf16 — two GPUs on capacity, four in practice once the KV cache is accounted for.
