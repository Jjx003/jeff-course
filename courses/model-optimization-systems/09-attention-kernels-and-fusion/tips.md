# Practical hints

When reading a benchmark or debugging a slow model, separate the math from the implementation path.

## Questions to ask

- Is the benchmark measuring prefill, decode, or an average that hides both?
- What sequence lengths and batch sizes were used?
- Does the model use MHA, GQA, or MQA?
- Are Q, K, and V stored in the layout expected by the fast kernel?
- Is the attention mask supported without falling back?
- Are there casts or transposes immediately before or after attention?
- Is the kernel exact attention, approximate attention, or a vendor-specific fused path?

## Mental checks

If sequence length doubles, naive attention intermediates grow by roughly four times because of the $L^2$ matrix. KV cache grows linearly with context length because it stores one key and one value per token per layer.

That contrast matters:

| Object | Growth with context | Main phase |
|---|---:|---|
| Full attention matrix | $O(L^2)$ | Prefill/training |
| KV cache | $O(L)$ per request | Decode/serving |
| MLP activations | $O(L)$ | Both |

## Reading kernel docs

Kernel documentation often lists supported dtypes, head dimensions, masks, and GPU architectures. Treat those lists as part of the model design space. A small architecture choice can make a model easier or harder to serve.

For example, grouped-query attention reduces KV-cache pressure. Head dimensions that align with tensor-core-friendly paths can matter. A custom attention mask may be mathematically convenient but operationally expensive.

## Transition

The next lab strips away the GPU machinery and keeps only the recurrence. If you can make the one-row online softmax match naive softmax, you understand the mathematical heart of tiled exact attention.
