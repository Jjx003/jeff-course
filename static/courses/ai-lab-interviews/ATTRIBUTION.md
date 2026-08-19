# Figure attribution

Every image in this directory is an **original figure** generated for this
course by `tools/course-figures/ai_lab_interview_figures.py`. None of them is a
reproduction, trace, or redraw of a figure from any paper.

Where a course module would benefit from a specific published figure — the
Chinchilla isoFLOP curves, the GQA architecture diagram, the FlashAttention
tiling picture — the module **links to the paper** rather than redistributing
the image. Most of the papers this course cites are released only under arXiv's
non-exclusive distribution license, which does not permit redistribution. (The
sibling *Model Optimization Systems* track does include a handful of paper
figures; every one of those comes from a CC BY 4.0 paper and is attributed in
that track's own `ATTRIBUTION.md`.)

## How to regenerate

```bash
uv run tools/course-figures/ai_lab_interview_figures.py
```

Set `FIG_PREVIEW_DIR` to also emit PNGs somewhere scratch, which makes text
overlap easier to spot than in SVG.

## What each figure computes

| File | Module | What is plotted |
|---|---|---|
| `attn-softmax-scaling.svg` | 06, 07 | Simulated logit variance, softmax saturation, and softmax-Jacobian magnitude versus head dimension, with and without the $1/\sqrt{d_k}$ factor. 4000 trials per point. |
| `attn-causal-mask.svg` | 06, 07 | The `tril` mask, the resulting attention weights, and the row sums produced by masking *after* the softmax instead of before. |
| `rope-frequencies.svg` | 06, 08 | RoPE's geometric frequency ladder, its per-pair wavelengths, and a direct demonstration that $q_m \cdot k_n$ depends only on $m-n$. |
| `params-breakdown.svg` | 06, 13 | Parameter split into attention, FFN, and embeddings for four real configurations, from $12Ld^2 + Vd$. |
| `kv-cache-growth.svg` | 07, 26 | KV cache size against context length and batch size for MHA, GQA, and MQA, using Llama-2-70B geometry. |
| `training-memory.svg` | 13, 16 | Training memory for a 7B model under five strategies, split into weights, gradients, optimizer state, and activations. |
| `lr-schedules.svg` | 16 | Warmup + cosine, warmup-stable-decay, and constant schedules, plus a zoom on the warmup phase. |
| `scaling-laws.svg` | 22 | IsoFLOP loss curves from the Hoffmann et al. parametric fit, and compute-optimal tokens-per-parameter against budget. |
| `roofline-decode.svg` | 26 | A roofline for an H100, with prefill and several decode batch sizes placed on it by arithmetic intensity. |
| `sampling-strategies.svg` | 26, 27 | One next-token distribution under temperature, top-k, and top-p. |
| `precision-formats.svg` | 18 | Bit layouts and range/precision trade-offs for fp32, tf32, bf16, fp16, and both fp8 formats. |
| `speculative-decoding.svg` | 26 | Expected accepted tokens per verification step against draft length and acceptance rate, and the resulting wall-clock optimum. |
| `posttraining-map.svg` | 30 | The RLHF pipeline and what DPO and GRPO each remove from it. |
| `tokenizer-tradeoff.svg` | 33 | Compression against vocabulary size, and the embedding-parameter cost that buys it. |
| `kv-cache-schemes.svg` | 06, 48 | Cached elements per token per layer for MHA, GQA, MQA, and MLA on DeepSeek-V3 geometry, and total cache against context at batch 32. |
| `attention-patterns.svg` | 06, 48 | Causal, sliding-window, and window-plus-sinks masks, and the cache saved by a 5:1 local/global stack. |
| `fp8-scaling-granularity.svg` | 17 | Measured quantization error against scaling block size for int8 and e4m3, showing that outlier sensitivity is an integer-format problem. The e4m3 rounding is verified element-for-element against torch's `float8_e4m3fn` cast. |
| `muon-orthogonalization.svg` | 15 | Singular-value spectrum of a synthetic momentum buffer before and after five Newton–Schulz steps, and the resulting spread of update energy across directions. |
| `prefill-decode-disaggregation.svg` | 25 | A scheduling timeline showing decode stalling behind a colocated prefill, against separate prefill and decode pools. |
| `grpo-advantage.svg` | 29, 30 | GRPO's std-normalized advantage against a mean-only baseline over a group of 8 binary rewards, and the implied per-prompt gradient weight. |
| `moe-anatomy.svg` | 46 | Published total against active parameters for four sparse models, and simulated expert load under balanced versus collapsed routing. |
| `test-time-compute.svg` | 47 | Closed-form models (explicitly not measurements) of pass@k against the majority-vote ceiling, and accuracy against reasoning tokens. |
| `sparse-attention.svg` | 48 | Dense against block-sparse attention masks, and the attention share of the $6ND$ term with and without a fixed key budget. |
| `agent-horizon.svg` | 49 | Compounding step reliability against task length, and the per-step error budget a given horizon demands. |
