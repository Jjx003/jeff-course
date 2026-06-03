# Hints

Start with shapes before numbers. In this lab:

- `W` is 2 by 3,
- `A` is 2 by 3,
- `B` is 2 by 2,
- `B @ A` is 2 by 3.

That last shape matches `W`, which is why the update can be added elementwise.

## Implementation hints

- Matrix multiply can be written with three loops: output row, output column, shared inner dimension.
- The scale is `ALPHA / rank`.
- For this toy example, `rank` is the number of rows in `A`.
- `dense_params` is the number of entries in `W`.
- `adapter_params` is the number of entries in `A` plus the number of entries in `B`.
- Round printed matrices to 3 decimals using the provided `rounded()` helper.

## A hand-check

The first entry of $BA$ is the dot product of row 0 of $B$ and column 0 of $A$:

$$
1.0 \cdot 0.2 + (-0.5) \cdot 0.0 = 0.2
$$

After scaling by 2, the first delta entry is:

$$
0.4
$$

So the first merged entry is:

$$
1.0 + 0.4 = 1.4
$$

If your first printed delta row begins with `0.4`, your multiplication order is probably right.

## Going deeper

- LoRA paper: https://arxiv.org/abs/2106.09685
- QLoRA paper: https://arxiv.org/abs/2305.14314
- PEFT library documentation: https://huggingface.co/docs/peft
