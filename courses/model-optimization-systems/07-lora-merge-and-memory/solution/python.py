"""
Reference solution for module 07.
"""

import math
import sys
import time

import torch

IN_FEATURES = 1024
OUT_FEATURES = 1024
RANK = 8
ALPHA = 16
BATCH = 32

ADAPTER_FILL_SEED = 1
ADAPTER_FILL_STD = 0.02

RANK_SWEEP = [1, 2, 4, 8, 16, 32, 64]
TARGET_SPECTRUM_RANK = 48
TARGET_DECAY = 0.85
TARGET_NOISE = 0.0002

BYTES_PER_ADAM_STATE = 2  # exp_avg and exp_avg_sq


class LoRALinear(torch.nn.Module):
    """A frozen nn.Linear plus a trainable rank-r adapter."""

    def __init__(self, in_features: int, out_features: int, rank: int, alpha: float):
        super().__init__()
        self.rank = rank
        self.alpha = alpha
        self.scaling = alpha / rank

        self.base = torch.nn.Linear(in_features, out_features, bias=False)
        self.base.weight.requires_grad_(False)

        self.lora_A = torch.nn.Parameter(torch.empty(rank, in_features))
        self.lora_B = torch.nn.Parameter(torch.zeros(out_features, rank))
        torch.nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        down = x @ self.lora_A.T
        up = down @ self.lora_B.T
        return self.base(x) + self.scaling * up

    def merged_weight(self) -> torch.Tensor:
        return self.base.weight + self.scaling * (self.lora_B @ self.lora_A)


def param_bytes(tensor: torch.Tensor) -> int:
    return tensor.numel() * tensor.element_size()


def training_bytes(trainable: list[torch.Tensor], frozen: list[torch.Tensor]) -> tuple[int, int, int]:
    """Return (frozen_weight_bytes, trainable_state_bytes, total_bytes) for Adam."""
    frozen_bytes = sum(param_bytes(p) for p in frozen)
    trainable_weight_bytes = sum(param_bytes(p) for p in trainable)
    # weights already counted once; add gradient plus two Adam moments.
    trainable_state_bytes = trainable_weight_bytes * (1 + BYTES_PER_ADAM_STATE)
    total = frozen_bytes + trainable_weight_bytes + trainable_state_bytes
    return frozen_bytes, trainable_state_bytes, total


def build_target_delta() -> torch.Tensor:
    """A weight delta with a decaying singular spectrum plus a small noise floor."""
    u = torch.randn(OUT_FEATURES, TARGET_SPECTRUM_RANK) / math.sqrt(OUT_FEATURES)
    v = torch.randn(IN_FEATURES, TARGET_SPECTRUM_RANK) / math.sqrt(IN_FEATURES)
    spectrum = TARGET_DECAY ** torch.arange(TARGET_SPECTRUM_RANK, dtype=torch.float32)
    signal = (u * spectrum) @ v.T
    noise = TARGET_NOISE * torch.randn(OUT_FEATURES, IN_FEATURES)
    return signal + noise


def truncation_errors(singular_values: torch.Tensor, ranks: list[int]) -> list[float]:
    """Relative Frobenius error of the optimal rank-r approximation, per Eckart-Young."""
    energy = singular_values.pow(2)
    total = energy.sum()
    tail = torch.flip(torch.cumsum(torch.flip(energy, dims=[0]), dim=0), dims=[0])
    errors = []
    for r in ranks:
        remaining = tail[r] if r < energy.numel() else torch.zeros((), dtype=energy.dtype)
        errors.append(float(torch.sqrt(remaining / total)))
    return errors


def main() -> None:
    torch.manual_seed(0)

    layer = LoRALinear(IN_FEATURES, OUT_FEATURES, RANK, ALPHA)
    x = torch.randn(BATCH, IN_FEATURES)

    print("=== LoRA on a real nn.Linear ===")
    print(f"in_features: {IN_FEATURES}")
    print(f"out_features: {OUT_FEATURES}")
    print(f"rank: {RANK}")
    print(f"alpha: {ALPHA}")
    print(f"scaling alpha/r: {layer.scaling:.3f}")
    print(f"batch: {BATCH}")
    print(f"base weight dtype: {layer.base.weight.dtype}")
    print()

    print("--- part 1: initialization is an exact no-op ---")
    with torch.inference_mode():
        base_out = layer.base(x)
        adapted_out = layer(x)
        init_diff = (adapted_out - base_out).abs().max().item()
        init_equal = torch.allclose(adapted_out, base_out, rtol=0.0, atol=0.0)
    print(f"A shape: {tuple(layer.lora_A.shape)}")
    print(f"B shape: {tuple(layer.lora_B.shape)}")
    print(f"B is all zeros: {bool(torch.all(layer.lora_B == 0))}")
    print(f"adapted output shape: {tuple(adapted_out.shape)}")
    print(f"max abs diff vs frozen base: {init_diff:.5f}")
    print(f"adapter is a no-op at step 0: {init_equal}")
    print()

    generator = torch.Generator().manual_seed(ADAPTER_FILL_SEED)
    with torch.no_grad():
        layer.lora_B.normal_(mean=0.0, std=ADAPTER_FILL_STD, generator=generator)

    print("--- part 2: the merged weight equals the adapter path ---")
    started = time.perf_counter()
    with torch.inference_mode():
        merged = layer.merged_weight()
        merged_out = x @ merged.T
        adapter_out = layer(x)
        merge_diff = (merged_out - adapter_out).abs().max().item()
        merge_equal = torch.allclose(merged_out, adapter_out, rtol=1e-4, atol=1e-4)
    print(f"[measured] merge check: {(time.perf_counter() - started) * 1e3:.3f} ms", file=sys.stderr)
    print(f"B is all zeros: {bool(torch.all(layer.lora_B == 0))}")
    print(f"merged weight shape: {tuple(merged.shape)}")
    print(f"delta rank upper bound: {RANK}")
    print(f"max abs diff merged vs adapter path: {merge_diff:.5f}")
    print(f"merge is equivalent: {merge_equal}")
    print()

    print("--- part 3: gradient discipline ---")
    output = layer(x)
    loss = output.pow(2).mean()
    loss.backward()
    print(f"base.weight requires_grad: {layer.base.weight.requires_grad}")
    print(f"base.weight grad is None: {layer.base.weight.grad is None}")
    print(f"lora_A requires_grad: {layer.lora_A.requires_grad}")
    print(f"lora_B requires_grad: {layer.lora_B.requires_grad}")
    print(f"lora_A grad shape: {tuple(layer.lora_A.grad.shape)}")
    print(f"lora_B grad shape: {tuple(layer.lora_B.grad.shape)}")
    print(f"lora_A grad is nonzero: {bool(layer.lora_A.grad.abs().max() > 0)}")
    print(f"lora_B grad is nonzero: {bool(layer.lora_B.grad.abs().max() > 0)}")

    trainable = [p for p in layer.parameters() if p.requires_grad]
    frozen = [p for p in layer.parameters() if not p.requires_grad]
    n_trainable = sum(p.numel() for p in trainable)
    n_frozen = sum(p.numel() for p in frozen)
    n_total = n_trainable + n_frozen
    print(f"frozen params: {n_frozen}")
    print(f"trainable params: {n_trainable}")
    print(f"total params: {n_total}")
    print(f"trainable percent: {100.0 * n_trainable / n_total:.3f}")
    print()

    print("--- part 4: Adam memory accounting ---")
    all_params = [layer.base.weight, layer.lora_A, layer.lora_B]
    full_frozen, full_state, full_total = training_bytes(all_params, [])
    lora_frozen, lora_state, lora_total = training_bytes(trainable, frozen)
    print(f"element size: {layer.base.weight.element_size()}")
    print(f"base weight bytes: {param_bytes(layer.base.weight)}")
    print(f"adapter weight bytes: {param_bytes(layer.lora_A) + param_bytes(layer.lora_B)}")
    print(f"full fine-tune resident weight bytes: {full_total - full_state}")
    print(f"full fine-tune grad + Adam state bytes: {full_state}")
    print(f"full fine-tune total bytes: {full_total}")
    print(f"LoRA frozen weight bytes: {lora_frozen}")
    print(f"LoRA grad + Adam state bytes: {lora_state}")
    print(f"LoRA total bytes: {lora_total}")
    print(f"trainable-state ratio: {full_state / lora_state:.2f}")
    print(f"total training memory ratio: {full_total / lora_total:.2f}")
    print()

    print("--- part 5: rank sweep against a fixed target delta ---")
    target = build_target_delta()
    started = time.perf_counter()
    singular_values = torch.linalg.svdvals(target)
    print(f"[measured] svdvals: {(time.perf_counter() - started) * 1e3:.3f} ms", file=sys.stderr)
    normalized = singular_values / singular_values[0]
    head = " ".join(f"{v:.4f}" for v in normalized[:5].tolist())
    print(f"target delta shape: {tuple(target.shape)}")
    print(f"top 5 normalized singular values: {head}")
    errors = truncation_errors(singular_values, RANK_SWEEP)
    for r, err in zip(RANK_SWEEP, errors):
        params = r * (IN_FEATURES + OUT_FEATURES)
        percent = 100.0 * params / (params + IN_FEATURES * OUT_FEATURES)
        print(f"  r={r:<3d} trainable={params:<7d} trainable%={percent:<7.3f} svd_rel_err={err:.4f}")
    print()


if __name__ == "__main__":
    main()
