# The Sparsity Trade

A dense transformer spends every parameter on every token. That is a strange thing to do: most tokens are easy, and most of what a model knows is irrelevant to any particular token. Mixture-of-Experts breaks the tie between *capacity* and *cost per token*.

![Two panels. Left: horizontal bars for Mixtral 8x7B, GPT-OSS-120B, Qwen3-235B-A22B and DeepSeek-V3, each showing total parameters as a light bar with active parameters as a filled overlay, annotated with sparsity ratios from 4x to 23x. Right: tokens routed per expert relative to an even share, sorted by load, comparing a flat balanced-routing line against a collapsed router where the busiest expert takes 6.7 times its share.](/courses/ai-lab-interviews/moe-anatomy.svg)

The left panel is the pitch. The right panel is the bill.

## The arithmetic

For an MoE layer with $N$ experts, top-$k$ routing, and FFN hidden size $d_{ff}$:

| Quantity | Dense | MoE |
|---|---|---|
| FFN parameters per layer | $2dd_{ff}$ | $N \cdot 2dd_{ff}$ |
| FFN FLOPs per token | $4dd_{ff}$ | $k \cdot 4dd_{ff}$ |
| Memory to hold the model | $\propto$ params | $\propto$ params |
| Memory to *serve* one token | all of it | all of it |

That last row is the one people get wrong. Sparsity saves arithmetic, not memory. Every expert has to be resident somewhere, because you cannot know in advance which tokens will want it.

**Estimate live, the way you did in module 13.** DeepSeek-V3: 671B total, 37B active — 18× sparsity. Its training compute is $6 \times 37\text{B} \times D$, not $6 \times 671\text{B} \times D$. Getting that distinction right in an interview is worth more than remembering the number.

## Routing

The router is $W_r \in \mathbb{R}^{d \times N}$ followed by a top-$k$. Two details matter.

**Gate before or after top-k.** You softmax the router logits and keep the top $k$ gate values, or you take the top $k$ logits and softmax only those. The second renormalizes, so the gates sum to 1 over the selected experts. Both appear in real models; the difference shows up in how the gradient flows back to unselected experts (it does not, in either case — the router learns only from experts it actually chose, which is why exploration and balance need explicit help).

**Shared experts.** DeepSeek's design keeps one or two experts always active alongside the routed ones. The reasoning: some computation is genuinely useful for every token, and forcing it to be rediscovered inside every expert wastes capacity on redundancy. It also gives the residual stream a stable path while the router is still noisy early in training.

## Load balancing, and why it is a real problem

Nothing in the loss wants balanced experts. A router that sends 90% of tokens to expert 3 gets a perfectly good loss — right up until you try to run it.

Under **expert parallelism** each expert lives on its own device. A step finishes when the slowest device finishes. If one expert takes 6.7× its share, as in the figure, every other GPU idles waiting for it: your 64-GPU job runs at the speed of a badly balanced 10-GPU job. This is a throughput catastrophe that the loss curve never shows.

**The classical fix** is an auxiliary loss that penalizes the product of the fraction of tokens routed to each expert and the mean router probability for it. It works. It also fights the main objective: you are explicitly pushing the router away from what it thinks is best, and at large scale that costs quality.

**The modern fix** is DeepSeek-V3's aux-loss-free approach: keep a per-expert bias added to the router logits *for the top-k selection only*, and adjust it up or down between steps based on how loaded that expert was. The bias steers selection without appearing in the gradient at all, so balance stops trading against the loss. If you can explain why that is different from an auxiliary loss — it changes *which* experts are chosen without changing *what* the chosen ones are worth — you have understood the design.

**Capacity factor** is the third piece. Implementations fix a per-expert token buffer of `capacity_factor * tokens / N`. Tokens beyond it are dropped and pass through the residual only. A capacity factor of 1.0 is efficient and drops tokens; 2.0 wastes half the buffer and rarely drops. Dropping in training is survivable and sometimes even acts as regularization; dropping at inference is a correctness bug, which is why serving usually runs dropless.

## Why serving is the hard part

The training story is comfortable: batches are huge, so every expert gets plenty of tokens and the all-to-all is amortized.

Decoding is the opposite. You have one token per sequence per step. With a batch of 8 sequences and top-2 routing you have at most 16 expert activations spread over 256 experts — so almost every expert is invoked with a handful of tokens, giving you tiny, bandwidth-bound matmuls, and you still paid to read those weights from HBM. **An MoE's arithmetic intensity at decode is far worse than a dense model of the same active size.** That gap is precisely why MoE serving wants very large batches, and why expert-parallel deployments care so much about overlapping the all-to-all with computation.

The two all-to-alls per layer — dispatch tokens to experts, combine results back — are the other half. DeepSeek-V3's node-limited routing caps how many nodes a token's experts may span, which bounds the cross-node traffic that the interconnect actually has to carry.

## When not to use one

- **You are memory-bound, not compute-bound.** An MoE makes that worse.
- **You serve at small batch.** You will pay full memory traffic for a fraction of the arithmetic.
- **You need to fine-tune cheaply on one node.** All the parameters have to fit.
- **Your evaluation is dominated by reasoning depth rather than knowledge.** Sparsity buys knowledge capacity most clearly; it does not add layers.

The honest summary: MoE converts an abundance of memory and interconnect into effective capacity. If those are what you are short of, it is the wrong trade.
