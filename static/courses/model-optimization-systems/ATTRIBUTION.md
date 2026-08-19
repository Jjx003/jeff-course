# Figure attribution

Two kinds of image appear in this course.

**Paper figures** (`*-figN-*.png`) are unmodified crops of figures from the
original research papers. Every one of them comes from a paper released under
Creative Commons Attribution 4.0 International (CC BY 4.0), which permits
redistribution with attribution. Each entry below records the paper, the figure
number, the authors, and the license.

Figures from papers released only under arXiv's non-exclusive distribution
license — including FlashAttention 1/2/3, AWQ, LoRA, and EAGLE — are **not**
reproduced here. Where a course module needs that kind of picture, it uses an
original diagram (`*.svg`, listed at the end) and links to the paper's own
figure instead.

**Original diagrams** (`*.svg`) were drawn for this course. They are not
reproductions of any paper figure, though several are informed by the
mechanisms those papers describe.

---

## `quant-smoothquant-fig4-activation-outliers.png`

- **Figure:** Figure 4 — "Magnitude of the input activations and weights of a
  linear layer in OPT-13B before and after SmoothQuant"
- **Paper:** *SmoothQuant: Accurate and Efficient Post-Training Quantization for
  Large Language Models*
- **Authors:** Guangxuan Xiao, Ji Lin, Mickael Seznec, Hao Wu, Julien Demouth,
  Song Han
- **Source:** https://arxiv.org/abs/2211.10438
- **License:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- **Modification:** Cropped from the published PDF at 300 dpi to remove
  surrounding page text. No changes to the figure content.
- **Used in:** module 03, *Quantization formats that matter*

## `lora-qlora-fig1-finetuning-memory.png`

- **Figure:** Figure 1 — "Different finetuning methods and their memory
  requirements"
- **Paper:** *QLoRA: Efficient Finetuning of Quantized LLMs*
- **Authors:** Tim Dettmers, Artidoro Pagnoni, Ari Holtzman, Luke Zettlemoyer
  (University of Washington)
- **Source:** https://arxiv.org/abs/2305.14314
- **License:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- **Modification:** Cropped from the published PDF at 300 dpi. No changes to the
  figure content.
- **Used in:** module 06, *LoRA, QLoRA, and adapter systems*

## `kv-vllm-fig3-memory-waste.png`

- **Figure:** Figure 3 — "KV cache memory management in existing systems",
  showing reserved slots, internal fragmentation, and external fragmentation
- **Paper:** *Efficient Memory Management for Large Language Model Serving with
  PagedAttention*
- **Authors:** Woosuk Kwon, Zhuohan Li, Siyuan Zhuang, Ying Sheng, Lianmin
  Zheng, Cody Hao Yu, Joseph E. Gonzalez, Hao Zhang, Ion Stoica (UC Berkeley,
  Stanford, UC San Diego)
- **Source:** https://arxiv.org/abs/2309.06180
- **License:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- **Modification:** Cropped from the published PDF at 300 dpi. No changes to the
  figure content.
- **Used in:** module 11, *KV-cache serving systems*

## `kv-vllm-fig6-block-table.png`

- **Figure:** Figure 6 — "Block table translation in vLLM"
- **Paper:** *Efficient Memory Management for Large Language Model Serving with
  PagedAttention* (same paper and authors as above)
- **Source:** https://arxiv.org/abs/2309.06180
- **License:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- **Modification:** Cropped from the published PDF at 300 dpi. No changes to the
  figure content.
- **Used in:** module 11, *KV-cache serving systems*

## `kv-gqa-fig2-mha-gqa-mqa.png`

- **Figure:** Figure 2 — "Overview of grouped-query method"
- **Paper:** *GQA: Training Generalized Multi-Query Transformer Models from
  Multi-Head Checkpoints*
- **Authors:** Joshua Ainslie, James Lee-Thorp, Michiel de Jong, Yury
  Zemlyanskiy, Federico Lebrón, Sumit Sanghai (Google Research)
- **Source:** https://arxiv.org/abs/2305.13245
- **License:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- **Modification:** Cropped from the published PDF at 300 dpi. No changes to the
  figure content.
- **Used in:** module 11, *KV-cache serving systems*

## `kv-streamingllm-fig2-attention-sinks.png`

- **Figure:** Figure 2 — "Visualization of the average attention logits in
  Llama-2-7B over 256 sentences"
- **Paper:** *Efficient Streaming Language Models with Attention Sinks*
- **Authors:** Guangxuan Xiao, Yuandong Tian, Beidi Chen, Song Han, Mike Lewis
  (MIT, Meta AI, Carnegie Mellon, NVIDIA)
- **Source:** https://arxiv.org/abs/2309.17453
- **License:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- **Modification:** Cropped from the published PDF at 300 dpi. No changes to the
  figure content.
- **Used in:** module 11, *KV-cache serving systems*

## `specdec-fig1-accept-reject-trace.png`

- **Figure:** Figure 1 — per-iteration trace of accepted (green), rejected
  (red), and corrected (blue) draft tokens
- **Paper:** *Fast Inference from Transformers via Speculative Decoding*
- **Authors:** Yaniv Leviathan, Matan Kalman, Yossi Matias (Google Research)
- **Source:** https://arxiv.org/abs/2211.17192
- **License:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- **Modification:** Cropped from the published PDF at 300 dpi. No changes to the
  figure content.
- **Used in:** module 13, *Speculative decoding and inference tricks*

## `specdec-fig2-expected-tokens.png`

- **Figure:** Figure 2 — "The expected number of tokens generated by Algorithm 1
  as a function of α for various values of γ"
- **Paper:** *Fast Inference from Transformers via Speculative Decoding* (same
  paper and authors as above)
- **Source:** https://arxiv.org/abs/2211.17192
- **License:** CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/)
- **Modification:** Cropped from the published PDF at 300 dpi. No changes to the
  figure content.
- **Used in:** module 13, *Speculative decoding and inference tricks*

---

## Original diagrams

Drawn for this course; no external license applies.

Hand-authored SVG:

| File | Module | Subject |
|---|---|---|
| `stack-roofline.svg` | 01 | Roofline with ridge point, decode and prefill operating points |
| `quant-int4-vs-nf4.svg` | 03 | Uniform INT4 vs NF4 level placement against a Gaussian weight density |
| `lora-merge-vs-dynamic.svg` | 06 | Merged versus dynamically applied adapter paths through one projection |
| `attn-flash-tiling.svg` | 09 | GPU memory hierarchy and the FlashAttention tiling loop |
| `attn-io-complexity.svg` | 09 | Attention intermediate footprint, materialized versus tiled |
| `dist-tensor-parallel.svg` | 15 | Megatron-style column/row-parallel MLP with the single all-reduce |
| `protein-cost-profile.svg` | 18 | Which cost term each folding-pipeline stage pays as chain length grows |

Generated by `tools/course-figures/model_optimization_figures.py`. Re-run it
with `uv run tools/course-figures/model_optimization_figures.py` after changing
any number quoted alongside these figures in the module text — the script is the
source of truth for them.

| File | Module | Subject |
|---|---|---|
| `quant-group-size-error.svg` | 03 | Simulated INT4 error vs group size, clean weights vs outlier channels |
| `kv-cache-vs-weights.svg` | 11 | KV cache size vs context and batch against BF16/INT4 weight footprints |
| `specdec-optimal-k.svg` | 13 | Expected speedup vs draft length, and how the optimal length moves with acceptance |
| `dist-tp-decode-scaling.svg` | 15 | Decode step floor and effective speedup vs tensor-parallel degree |
| `moe-decode-intensity.svg` | 15 | Expected distinct experts touched, and MoE vs dense decode arithmetic intensity |
| `bench-latency-vs-load.svg` | 17 | TTFT percentiles vs load against Pollaczek-Khinchine, and coordinated omission |

The FlashAttention diagrams are original work. They depict the algorithm as
described in *FlashAttention: Fast and Memory-Efficient Exact Attention with
IO-Awareness* (Dao, Fu, Ermon, Rudra, Ré, https://arxiv.org/abs/2205.14135),
whose own figures are not redistributable under arXiv's non-exclusive license.
