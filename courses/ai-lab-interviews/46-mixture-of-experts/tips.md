# Rapid-Fire: MoE

**"Why does an MoE have more parameters but the same training FLOPs?"**
> Only $k$ of $N$ experts run per token. Parameters scale with $N$, FLOPs with $k$. DeepSeek-V3 is 671B parameters and 37B active, so its training compute is $6 \times 37\text{B} \times D$.

**"So it is free capacity?"**
> No. You still store every expert and still read its weights from HBM when it fires. It trades memory and interconnect for compute. If you are memory-bound it makes things worse.

**"What is the router?"**
> One $d \times N$ linear layer, then top-$k$. The smallest matrix in the model and the one that decides its FLOPs, its load balance, and its failure modes.

**"What happens if routing collapses?"**
> A few experts take most tokens. The loss looks fine. Under expert parallelism the step waits for the busiest device, so a 64-GPU job runs at the speed of a poorly balanced 10-GPU one, and the unused experts are dead capacity you are still paying to store.

**"How do you fix it?"**
> Classically, an auxiliary balance loss. The problem is that it fights the main objective — you are pushing the router away from its own preference. DeepSeek-V3's aux-loss-free scheme instead keeps a per-expert bias used *only* for top-$k$ selection, nudged between steps by observed load. It changes which experts are picked without entering the gradient.

**"What is a capacity factor?"**
> The per-expert token buffer, as a multiple of the even share. Overflow tokens are dropped and skip the layer. Fine in training, a correctness bug at inference — serving runs dropless.

**"What is a shared expert?"**
> An expert every token uses, alongside the routed ones. It absorbs the computation that is useful universally, so routed experts do not each have to relearn it, and it gives a stable path early in training.

**"Why is expert parallelism harder than tensor parallelism?"**
> TP's communication is a fixed all-reduce of known size on every step. EP's is an all-to-all whose *volume depends on the data* — routing decides who talks to whom, so it is imbalanced, hard to overlap, and gets worse across nodes. Node-limited routing caps how many nodes a token may span.

**"Why is MoE decoding inefficient?"**
> One token per sequence per step means each expert gets a handful of tokens, so you do tiny bandwidth-bound matmuls after paying full price to read the weights. Arithmetic intensity is much worse than a dense model of the same active size, which is why MoE serving needs large batches.

**"When would you not use one?"**
> Small-batch serving, memory-constrained deployment, single-node fine-tuning, or when what you need is reasoning depth rather than knowledge capacity.

## Going deeper

- [Switch Transformer](https://arxiv.org/abs/2101.03961) — the paper that made top-1 routing and capacity factors standard vocabulary.
- [ST-MoE](https://arxiv.org/abs/2202.08906) — the practical stability writeup: router z-loss, fine-tuning behaviour, what actually breaks.
- [Mixtral of Experts](https://arxiv.org/abs/2401.04088) — the first widely-used open sparse model; clean description of top-2 routing.
- [DeepSeek-V3 technical report](https://arxiv.org/abs/2412.19437) — fine-grained experts, shared experts, aux-loss-free balancing, node-limited routing, and the fp8 recipe, in one place. If you read one thing here, read this.
