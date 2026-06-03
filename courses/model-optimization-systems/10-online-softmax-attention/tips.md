# Hints

Use `math.exp` and keep the vector dimension generic. The starter value vectors happen to be length 2, but your weighted-sum code should work for any consistent value length.

## Naive path

1. `m = max(scores)`
2. `weights = [math.exp(s - m) for s in scores]`
3. `denom = sum(weights)`
4. For each value dimension, sum `weight * value_component / denom`.

## Online path

Initialize:

```python
running_m = float("-inf")
running_l = 0.0
running_n = [0.0 for _ in values[0]]
```

For each block:

1. Compute `block_m`.
2. Compute shifted exponentials using `block_m`.
3. Compute `block_l`.
4. Compute `block_n`.
5. Set `new_m = max(running_m, block_m)`.
6. Rescale old and block accumulators into `new_m`.

The rescale factors are:

$$
\text{old_scale} = e^{m_\text{old}-m_\text{new}}
$$

and:

$$
\text{block_scale} = e^{m_b-m_\text{new}}
$$

## Debugging checks

- With `block_size` equal to the full score length, online attention should look almost identical to the naive implementation.
- With `block_size=1`, every score arrives alone; this is a good stress test for rescaling.
- If your output is close for the first block but wrong after a larger later score, you probably forgot to rescale the old numerator.
- If probabilities seem right but the vector is wrong, inspect the weighted sum dimension loop.

## Going deeper

- FlashAttention paper: https://arxiv.org/abs/2205.14135
- FlashAttention-3 paper: https://arxiv.org/abs/2407.08608
- Online normalizer intuition: https://arxiv.org/abs/1805.02867
