# Practical hints

The fastest sanity check on any distributed plan: write down bytes per GPU
(weights plus peak cache), then collectives per token and their payloads. If
either number is missing from a proposal, the proposal is not finished.

## Debugging questions

- What TP degree is the engine actually using, and does it divide both the
  query-head and KV-head counts?
- Are collectives running over NVLink or falling back to PCIe/host memory?
  A single misplaced GPU can silently 10× the all-reduce cost.
- Is decode communication latency-bound (it usually is) — and if so, did the
  "faster interconnect" upgrade change latency or only bandwidth?
- For PP: what concurrency does the scheduler actually sustain? Compare it to
  the stage count before trusting any throughput projection.
- For MoE: what is the measured tokens-per-expert distribution under real
  traffic, not under a uniform-routing assumption?

## Rules of thumb worth checking, not trusting

- TP inside the node, PP across nodes — true until the batch is too small to
  fill the pipeline, then fewer bigger stages win.
- "MoE is cheap" — per token at batch 1, yes; at serving batch sizes the union
  of routed experts is the traffic, and $m(B) = E(1-(1-k/E)^B)$ says how fast
  the cheapness dilutes.
- Effective TP speedup of 6× on 8 GPUs is healthy, not broken. If a vendor
  claims 8×, ask what happened to the 160 collectives.

## Evaluation traps

- Comparing TP 8 against TP 1 for a model that does not fit at TP 1 measures
  nothing; the baseline must be a deployable configuration.
- Prefill benchmarks hide collective latency (payloads are large, the
  bandwidth term amortizes); decode benchmarks expose it. Report both.
- MoE throughput measured with synthetic uniform routing overstates production
  throughput; hot experts are a property of real traffic.

## Going deeper

- Megatron-LM tensor parallelism: https://arxiv.org/abs/1909.08053
- Sequence parallelism and selective recomputation: https://arxiv.org/abs/2205.05198
- GPipe and the bubble: https://arxiv.org/abs/1811.06965
- Switch Transformer (capacity factor, routing): https://arxiv.org/abs/2101.03961
- DeepSeek-V3 technical report (EP at scale): https://arxiv.org/abs/2412.19437
- NCCL collective algorithms: https://docs.nvidia.com/deeplearning/nccl/user-guide/docs/usage/collectives.html
