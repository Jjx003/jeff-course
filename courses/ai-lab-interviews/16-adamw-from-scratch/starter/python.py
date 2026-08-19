"""
AdamW, a warmup-plus-cosine schedule, and global gradient clipping — written
from scratch and checked against torch's own implementations.

Graded output goes to stdout in float64 with seed 0 so the numbers match on any
machine. Exact floating-point differences go to stderr, which is not graded.

Fill in the three TODO blocks. Fifteen minutes for the optimizer is the bar.
"""

import math
import sys

import torch
import torch.nn as nn

SEED = 0
DIM_IN, DIM_HIDDEN, DIM_OUT = 8, 16, 4
BATCH = 32
STEPS = 25
LR = 1e-2
BETAS = (0.9, 0.95)
EPS = 1e-8
WEIGHT_DECAY = 0.1
CLIP_NORM = 1.0

WARMUP_STEPS = 100
TOTAL_STEPS = 1000
MIN_LR_FRAC = 0.1

MATCH_ATOL = 1e-10


class AdamW(torch.optim.Optimizer):
    """Decoupled-weight-decay Adam, written out longhand."""

    def __init__(self, params, lr=1e-3, betas=(0.9, 0.95), eps=1e-8, weight_decay=0.0):
        if lr < 0:
            raise ValueError(f"invalid learning rate: {lr}")
        if not 0 <= betas[0] < 1 or not 0 <= betas[1] < 1:
            raise ValueError(f"invalid betas: {betas}")
        defaults = {"lr": lr, "betas": betas, "eps": eps, "weight_decay": weight_decay}
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self):
        """TODO 1: the AdamW update.

        For every parameter with a gradient, keeping per-parameter state
        (t, m, v) in self.state[p]:

            t <- t + 1                       starts at 1, not 0
            m <- beta1 * m + (1 - beta1) * g
            v <- beta2 * v + (1 - beta2) * g * g       element-wise square
            m_hat = m / (1 - beta1 ** t)
            v_hat = v / (1 - beta2 ** t)
            p <- p - lr * weight_decay * p             decoupled: touches p
            p <- p - lr * m_hat / (sqrt(v_hat) + eps)  eps INSIDE the sqrt sum

        Three things that go wrong under pressure: t starting at 0, the decay
        applied to g instead of p, and eps added to v_hat rather than to
        sqrt(v_hat).
        """
        raise NotImplementedError


def lr_at_step(step, peak=LR, warmup=WARMUP_STEPS, total=TOTAL_STEPS, min_frac=MIN_LR_FRAC):
    """Linear warmup then cosine decay to min_frac * peak.

    TODO 2:
      step < warmup   ->  peak * step / warmup
      step >= total   ->  peak * min_frac
      otherwise       ->  progress = (step - warmup) / (total - warmup)
                          peak * (min_frac + (1 - min_frac) * 0.5 * (1 + cos(pi * progress)))

    Clamp past total, or a run that overshoots gets a RISING learning rate
    as the cosine comes back up. That has shipped.
    """
    raise NotImplementedError


def clip_grad_norm(params, max_norm=CLIP_NORM):
    """Global-norm clipping. Returns the pre-clip total norm.

    TODO 3: compute ONE norm across every gradient — sqrt of the sum of all
    squared entries — and if it exceeds max_norm, scale every gradient by the
    same factor max_norm / (total + 1e-6). Return the pre-clip norm.

    The same factor everywhere is the point: that preserves the update's
    direction and only bounds its magnitude. Clipping each tensor against its
    own threshold would rotate the update.
    """
    raise NotImplementedError


def build_model():
    torch.manual_seed(SEED)
    return nn.Sequential(
        nn.Linear(DIM_IN, DIM_HIDDEN),
        nn.Tanh(),
        nn.Linear(DIM_HIDDEN, DIM_OUT),
    ).double()


def run(optimizer_factory, steps=STEPS):
    """Train a fixed problem and return the loss trace and final parameters."""
    torch.manual_seed(SEED)
    model = build_model()
    opt = optimizer_factory(model.parameters())

    torch.manual_seed(SEED + 1)
    x = torch.randn(BATCH, DIM_IN, dtype=torch.float64)
    y = torch.randn(BATCH, DIM_OUT, dtype=torch.float64)

    losses = []
    for _ in range(steps):
        loss = ((model(x) - y) ** 2).mean()
        opt.zero_grad()
        loss.backward()
        opt.step()
        losses.append(float(loss.detach()))
    return losses, [p.detach().clone() for p in model.parameters()]


def main():
    torch.manual_seed(SEED)

    print("=== AdamW, schedules, and clipping ===")
    print(f"betas: {BETAS}  eps: {EPS:g}  weight_decay: {WEIGHT_DECAY}  lr: {LR:g}")
    print(f"dtype: torch.float64  steps: {STEPS}")

    print()
    print("--- 1. AdamW matches torch.optim.AdamW ---")
    mine_losses, mine_params = run(
        lambda ps: AdamW(ps, lr=LR, betas=BETAS, eps=EPS, weight_decay=WEIGHT_DECAY)
    )
    torch_losses, torch_params = run(
        lambda ps: torch.optim.AdamW(ps, lr=LR, betas=BETAS, eps=EPS, weight_decay=WEIGHT_DECAY)
    )
    loss_gap = max(abs(a - b) for a, b in zip(mine_losses, torch_losses))
    param_gap = max(float((a - b).abs().max()) for a, b in zip(mine_params, torch_params))
    print(f"loss trace matches over all {STEPS} steps: {loss_gap < MATCH_ATOL}")
    print(f"final parameters match: {param_gap < MATCH_ATOL}")
    print(f"loss {mine_losses[0]:.6f} -> {mine_losses[-1]:.6f}")
    print(f"  max loss gap {loss_gap:.3e}  max param gap {param_gap:.3e}", file=sys.stderr)

    print()
    print("--- 2. decoupled decay is not L2 on the gradient ---")
    plain_losses, plain_params = run(
        lambda ps: torch.optim.Adam(ps, lr=LR, betas=BETAS, eps=EPS, weight_decay=WEIGHT_DECAY)
    )
    coupled_gap = max(float((a - b).abs().max()) for a, b in zip(mine_params, plain_params))
    print(f"Adam(weight_decay=) differs from AdamW: {coupled_gap > 1e-6}")
    print(f"  max param gap vs coupled L2: {coupled_gap:.3e}", file=sys.stderr)

    print()
    print("--- 3. bias correction ---")
    p = torch.zeros(1, dtype=torch.float64, requires_grad=True)
    opt = AdamW([p], lr=LR, betas=BETAS, eps=0.0, weight_decay=0.0)
    p.grad = torch.tensor([3.0], dtype=torch.float64)
    opt.step()
    first_step = float(-p.detach())
    print(f"first update size with bias correction: {first_step:.8f}")
    print(f"equals the learning rate: {abs(first_step - LR) < 1e-9}")
    print("(m_hat / sqrt(v_hat) = g / |g| = 1 on step one, whatever the gradient is)")

    uncorrected_m = (1 - BETAS[0]) * 3.0
    uncorrected_v = (1 - BETAS[1]) * 9.0
    uncorrected = LR * uncorrected_m / math.sqrt(uncorrected_v)
    print(f"without bias correction the first step would be: {uncorrected:.8f}")
    print(f"that is smaller than the corrected step: {uncorrected < first_step}")

    print()
    print("--- 4. warmup + cosine schedule ---")
    checkpoints = [0, 1, 50, WARMUP_STEPS, 300, 550, 999, 1200]
    for step in checkpoints:
        print(f"  step {step:>4}: lr {lr_at_step(step):.6e}")
    print(f"lr is 0 at step 0: {lr_at_step(0) == 0.0}")
    print(f"lr peaks exactly at the end of warmup: {abs(lr_at_step(WARMUP_STEPS) - LR) < 1e-15}")
    mid = lr_at_step(WARMUP_STEPS + (TOTAL_STEPS - WARMUP_STEPS) // 2)
    print(f"lr at the halfway point is ~55% of peak: {abs(mid / LR - 0.55) < 0.01}")
    print(f"lr floors at {MIN_LR_FRAC:g} of peak: {abs(lr_at_step(1200) - LR * MIN_LR_FRAC) < 1e-15}")
    print(f"schedule is monotone after warmup: "
          f"{all(lr_at_step(s) >= lr_at_step(s + 1) - 1e-15 for s in range(WARMUP_STEPS, TOTAL_STEPS))}")

    print()
    print("--- 5. global gradient clipping ---")
    torch.manual_seed(SEED + 2)
    model = build_model()
    for p in model.parameters():
        p.grad = torch.randn_like(p) * 5.0
    before = [p.grad.clone() for p in model.parameters()]
    total_before = clip_grad_norm(model.parameters(), CLIP_NORM)
    after = [p.grad.clone() for p in model.parameters()]
    total_after = math.sqrt(sum(float((g**2).sum()) for g in after))

    print(f"norm before clipping exceeds {CLIP_NORM}: {total_before > CLIP_NORM}")
    print(f"norm after clipping is {CLIP_NORM}: {abs(total_after - CLIP_NORM) < 1e-5}")
    cosines = [
        float((a.flatten() @ b.flatten()) / (a.norm() * b.norm()))
        for a, b in zip(before, after)
    ]
    print(f"direction is unchanged for every tensor: {all(abs(c - 1.0) < 1e-9 for c in cosines)}")
    print("(global clipping rescales; per-tensor clipping would rotate the update)")

    small = torch.ones(4, dtype=torch.float64) * 0.1
    holder = torch.zeros(4, dtype=torch.float64, requires_grad=True)
    holder.grad = small.clone()
    returned = clip_grad_norm([holder], CLIP_NORM)
    print(f"a below-threshold gradient is left alone: {torch.equal(holder.grad, small)}")
    print(f"  returned norm {returned:.6f}", file=sys.stderr)

    print()
    all_ok = (
        loss_gap < MATCH_ATOL
        and param_gap < MATCH_ATOL
        and coupled_gap > 1e-6
        and abs(first_step - LR) < 1e-9
        and abs(total_after - CLIP_NORM) < 1e-5
        and all(abs(c - 1.0) < 1e-9 for c in cosines)
        and torch.equal(holder.grad, small)
    )
    print(f"ALL CHECKS PASS: {all_ok}")


if __name__ == "__main__":
    main()
