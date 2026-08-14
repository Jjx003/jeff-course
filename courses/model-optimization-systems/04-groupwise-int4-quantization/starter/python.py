"""
Groupwise symmetric INT4 quantization of a real torch weight matrix.

Everything here runs on CPU in float32 so that your numbers match the
grader exactly. See problem.md for the required output format.
"""

import torch

QMAX = 7
IN_FEATURES = 512
OUT_FEATURES = 256
GROUP_SIZE = 64
BATCH = 32
SWEEP = [32, 64, 128, 512]
OUTLIER_STRIDE = 137
OUTLIER_MAGNITUDE = 25.0


def quantize_groupwise(weight: torch.Tensor, group_size: int):
    """Return (codes, scales) for a (out_features, in_features) weight.

    codes:  int8, same shape as weight, values in [-QMAX, QMAX]
    scales: float32, shape (out_features, in_features // group_size)
    """
    # TODO 1: Reshape the weight to (out_features, n_groups, group_size) so
    # every group is contiguous along the last dimension.
    #
    # TODO 2: Compute one scale per group from the group's largest magnitude:
    #   max_abs = grouped.abs().amax(dim=-1, keepdim=True)
    #   scale   = max_abs / QMAX, but 1.0 wherever max_abs == 0
    # torch.where is the clean way to handle the all-zero group.
    #
    # TODO 3: Quantize with round-then-clamp, cast to torch.int8, and reshape
    # the codes back to the weight's original shape. Return the scales with
    # the trailing singleton dimension squeezed out.
    raise NotImplementedError


def dequantize_groupwise(codes: torch.Tensor, scales: torch.Tensor, group_size: int) -> torch.Tensor:
    """Reconstruct an approximate float32 weight from codes and scales."""
    # TODO 4: Reshape codes into groups, cast to float32, multiply by the
    # matching scale (unsqueeze the scales so they broadcast over the group
    # dimension), then reshape back.
    raise NotImplementedError


def pack_int4(codes: torch.Tensor) -> torch.Tensor:
    """Pack two int4 codes into each uint8 byte.

    Codes are in [-7, 7]. Shift them by +8 into the nibble range [1, 15],
    then place even columns in the low nibble and odd columns in the high
    nibble. Returns shape (out_features, in_features // 2).
    """
    # TODO 5: Build the unsigned nibbles, slice codes[:, 0::2] and
    # codes[:, 1::2], and combine them with torch.bitwise_or and
    # torch.bitwise_left_shift(high, 4).
    raise NotImplementedError


def unpack_int4(packed: torch.Tensor) -> torch.Tensor:
    """Invert pack_int4 exactly, returning int8 codes."""
    # TODO 6: Mask the low nibble with 0x0F and shift the high nibble down by
    # 4, subtract the +8 bias from each, then interleave them back into
    # column order. torch.stack([low, high], dim=-1) followed by a reshape
    # restores the original column ordering.
    raise NotImplementedError


def int4_bytes(out_features: int, in_features: int, group_size: int) -> tuple[int, int, int]:
    """Return (payload_bytes, scale_bytes, total_bytes) for the packed format."""
    # TODO 7: The payload holds two weights per byte. Scales are fp16, one
    # per group. Return the payload, the scale bytes, and their sum.
    raise NotImplementedError


def inject_outliers(weight: torch.Tensor, stride: int, magnitude: float) -> torch.Tensor:
    """Scale up every `stride`-th column to imitate outlier channels."""
    spiked = weight.clone()
    spiked[:, ::stride] *= magnitude
    return spiked


def sweep_table(weight: torch.Tensor, x: torch.Tensor, label: str) -> None:
    reference = x @ weight.T
    n_weights = weight.numel()
    out_features, in_features = weight.shape

    print(f"--- group size sweep: {label} ---")
    for group_size in SWEEP:
        # TODO 8: Quantize, dequantize, and measure, then replace the three
        # placeholders below.
        #   total        -> total_bytes from int4_bytes for this group size
        #   weight_mae   -> mean absolute error of the reconstructed weight
        #   out_rel_err  -> ||x @ restored.T - reference|| / ||reference||
        # using the Frobenius norm. The output error is what actually matters
        # here, not the weight error.
        total = 0
        weight_mae = 0.0
        out_rel_err = 0.0

        print(
            f"  G={group_size:<4d} "
            f"bits/weight={total * 8 / n_weights:.3f} "
            f"weight_mae={weight_mae:.5f} "
            f"out_rel_err={out_rel_err:.5f}"
        )
    print()


def main() -> None:
    torch.manual_seed(0)

    layer = torch.nn.Linear(IN_FEATURES, OUT_FEATURES, bias=False)
    weight = layer.weight.detach().to(torch.float32)
    x = torch.randn(BATCH, IN_FEATURES)
    n_weights = weight.numel()

    print("=== INT4 groupwise quantization of a real nn.Linear ===")
    print(f"weight shape: {tuple(weight.shape)}")
    print(f"weight dtype: {weight.dtype}")
    print(f"weights: {n_weights}")
    print()

    codes, scales = quantize_groupwise(weight, GROUP_SIZE)
    packed = pack_int4(codes)
    restored_codes = unpack_int4(packed)

    print(f"--- group size {GROUP_SIZE} ---")
    print(f"codes dtype: {codes.dtype}")
    print(f"codes min/max: {int(codes.min())} {int(codes.max())}")
    print(f"scales shape: {tuple(scales.shape)}")
    print(f"packed dtype: {packed.dtype}")
    print(f"packed shape: {tuple(packed.shape)}")
    print(f"unpack round-trip exact: {torch.equal(restored_codes, codes)}")
    print()

    payload, scale_bytes, total = int4_bytes(OUT_FEATURES, IN_FEATURES, GROUP_SIZE)
    fp16_bytes = n_weights * 2

    print(f"--- byte accounting (group size {GROUP_SIZE}) ---")
    print(f"fp16 baseline: {fp16_bytes} bytes")
    print(f"int4 payload: {payload} bytes")
    print(f"fp16 scales: {scale_bytes} bytes")
    print(f"int4 total: {total} bytes")
    print(f"compression: {fp16_bytes / total:.2f}x")
    print(f"effective bits/weight: {total * 8 / n_weights:.3f}")
    print()

    sweep_table(weight, x, "gaussian weights")
    sweep_table(inject_outliers(weight, OUTLIER_STRIDE, OUTLIER_MAGNITUDE), x, "with outliers")


if __name__ == "__main__":
    main()
