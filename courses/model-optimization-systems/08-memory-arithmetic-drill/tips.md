# Hints

Do not try to memorize every possible model size. Memorize the multipliers.

- BF16 is 2 bytes per value.
- INT8 is 1 byte per value.
- INT4 is 0.5 bytes per value before metadata.
- KV cache has both K and V, so remember the factor of 2.
- Padding waste is easiest if you compute padded tokens first.

## Fast paths

For BF16 weights, double the parameter count in billions:

$$
34B \rightarrow 68\ \text{GB}
$$

For raw INT4 weights, halve it:

$$
72B \rightarrow 36\ \text{GB}
$$

For a square LoRA matrix, use:

$$
2rd
$$

then divide by 1000 if the prompt asks for thousands.

For KV cache, multiply in a stable order:

1. layers times KV heads,
2. times head dimension,
3. times 2 for K and V,
4. times tokens,
5. times bytes per value,
6. divide by 1,000,000 for MB.

## Common mistakes

- Counting query heads instead of KV heads for GQA models.
- Forgetting that a generated token is added to the cache after decode.
- Treating INT4 as exactly free aside from weights; real systems still need scales and sometimes higher-precision outlier paths.
- Computing padding waste as wasted divided by real tokens. The drill asks for wasted divided by padded tokens.

## Going deeper

- vLLM PagedAttention paper: https://arxiv.org/abs/2309.06180
- TensorRT-LLM KV cache documentation: https://nvidia.github.io/TensorRT-LLM/features/kvcache.html
- QLoRA paper: https://arxiv.org/abs/2305.14314
