# Hints

Start with units. Most mistakes in this exercise are not Python mistakes; they
are unit mistakes.

For weights:

- 70B parameters means `70 * 1e9` parameters.
- BF16 is 2 bytes per parameter.
- Decimal GB divides by `1e9`.

For matmul work:

- approximate FLOPs are `2 * parameter_count`;
- GFLOP divides by `1e9`;
- TFLOP/s to GFLOP/s multiplies by `1000`.

For time:

- seconds are work divided by rate;
- milliseconds multiply seconds by `1000`;
- compare memory and compute lower bounds to choose the bottleneck label.

## KV-cache hint

The KV-cache helper should compute bytes first, then convert to GiB:

$$
\text{GiB} = \frac{\text{bytes}}{1024^3}
$$

Remember the full formula:

$$
\text{layers} \times \text{tokens} \times \text{KV heads}
\times \text{head dim} \times 2 \times \text{bytes per value}
$$

If the GQA and MHA answers differ by exactly 8x, you are on the right track:
the only difference between those two cases is 8 KV heads versus 64 KV heads.

## Debugging checklist

If your output is close but not exact:

- check decimal GB versus GiB;
- check whether you used billions as `1e9`, not `1024**3`;
- check whether peak compute is `989_000` GFLOP/s;
- check whether the KV cache includes both keys and values;
- check whether printed values use the formatting already in the starter.

## Going deeper

After you finish, change constants privately and ask what should happen:

- What if weights are INT4 rather than BF16?
- What if context length doubles?
- What if KV heads go from 8 to 4?
- What if batch size increases enough that weights are reused?

You do not need to submit those experiments. They are the mental bridge from
this tiny estimator to real serving design.
