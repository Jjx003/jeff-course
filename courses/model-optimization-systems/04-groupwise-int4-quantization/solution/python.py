"""
Reference solution for module 04.
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
    out_features, in_features = weight.shape
    n_groups = in_features // group_size
    grouped = weight.reshape(out_features, n_groups, group_size)

    max_abs = grouped.abs().amax(dim=-1, keepdim=True)
    scales = torch.where(max_abs > 0, max_abs / QMAX, torch.ones_like(max_abs))

    codes = torch.clamp(torch.round(grouped / scales), -QMAX, QMAX).to(torch.int8)
    return codes.reshape(out_features, in_features), scales.squeeze(-1)


def dequantize_groupwise(codes: torch.Tensor, scales: torch.Tensor, group_size: int) -> torch.Tensor:
    out_features, in_features = codes.shape
    n_groups = in_features // group_size
    grouped = codes.reshape(out_features, n_groups, group_size).to(torch.float32)
    restored = grouped * scales.unsqueeze(-1)
    return restored.reshape(out_features, in_features)


def pack_int4(codes: torch.Tensor) -> torch.Tensor:
    # Shift the signed range [-7, 7] into the unsigned nibble range [1, 15].
    nibbles = (codes.to(torch.int16) + 8).to(torch.uint8)
    low = nibbles[:, 0::2]
    high = nibbles[:, 1::2]
    return torch.bitwise_or(low, torch.bitwise_left_shift(high, 4))


def unpack_int4(packed: torch.Tensor) -> torch.Tensor:
    low = torch.bitwise_and(packed, 0x0F).to(torch.int16) - 8
    high = torch.bitwise_and(torch.bitwise_right_shift(packed, 4), 0x0F).to(torch.int16) - 8
    interleaved = torch.stack([low, high], dim=-1)
    return interleaved.reshape(packed.shape[0], -1).to(torch.int8)


def int4_bytes(out_features: int, in_features: int, group_size: int) -> tuple[int, int, int]:
    payload = out_features * in_features // 2
    scale_bytes = out_features * (in_features // group_size) * 2
    return payload, scale_bytes, payload + scale_bytes


def inject_outliers(weight: torch.Tensor, stride: int, magnitude: float) -> torch.Tensor:
    spiked = weight.clone()
    spiked[:, ::stride] *= magnitude
    return spiked


def sweep_table(weight: torch.Tensor, x: torch.Tensor, label: str) -> None:
    reference = x @ weight.T
    n_weights = weight.numel()
    out_features, in_features = weight.shape

    print(f"--- group size sweep: {label} ---")
    for group_size in SWEEP:
        codes, scales = quantize_groupwise(weight, group_size)
        restored = dequantize_groupwise(codes, scales, group_size)
        _, _, total = int4_bytes(out_features, in_features, group_size)

        weight_mae = (weight - restored).abs().mean().item()
        out_rel_err = ((x @ restored.T - reference).norm() / reference.norm()).item()

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
