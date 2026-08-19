#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.9", "numpy>=1.26"]
# ///
"""Generate the computed figures for the Getting Hired at an AI Lab course.

Run with:

    uv run tools/course-figures/ai_lab_interview_figures.py

Figures are written as SVG into `static/courses/ai-lab-interviews/`.

Every number plotted below is computed here from the same closed-form model the
corresponding course module states in prose, so a figure and its module text
cannot drift apart. Nothing is traced from a paper; where a course module wants
a picture from a paper whose license does not permit redistribution, it links to
the paper instead. See ATTRIBUTION.md in the output directory.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parents[2] / "static" / "courses" / "ai-lab-interviews"

BG = "#f8fafc"
INK = "#0f172a"
MUTED = "#475569"
GRID = "#e2e8f0"
RED = "#dc2626"
ORANGE = "#ea580c"
AMBER = "#d97706"
GREEN = "#16a34a"
BLUE = "#2563eb"
VIOLET = "#7c3aed"
TEAL = "#0d9488"
PINK = "#db2777"

plt.rcParams.update(
    {
        "font.family": ["Segoe UI", "DejaVu Sans"],
        "font.size": 11,
        "axes.edgecolor": MUTED,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 1.0,
        "axes.axisbelow": True,
        "figure.facecolor": BG,
        "axes.facecolor": BG,
        "savefig.facecolor": BG,
        "svg.fonttype": "none",
    }
)


def _finish(fig, name: str, caption: str) -> None:
    """Lay the axes out above a reserved caption band, then write the SVG."""
    lines = caption.count("\n") + 1
    band = 0.05 + 0.045 * lines
    fig.tight_layout(rect=(0.0, band, 1.0, 1.0))
    fig.text(0.012, 0.012, caption, fontsize=9.5, color=MUTED, va="bottom", linespacing=1.5)
    path = OUT / name
    fig.savefig(path, format="svg")
    preview = os.environ.get("FIG_PREVIEW_DIR")
    if preview:
        fig.savefig(Path(preview) / name.replace(".svg", ".png"), dpi=110)
    plt.close(fig)
    print(f"wrote {path.relative_to(OUT.parents[2])}")


# --------------------------------------------------------------------------
# 1. Why scaled dot-product attention divides by sqrt(d_k)
# --------------------------------------------------------------------------


def fig_softmax_scaling() -> None:
    rng = np.random.default_rng(0)
    head_dims = np.array([8, 16, 32, 64, 128, 256])
    trials = 4000

    unscaled_std, scaled_std = [], []
    unscaled_maxp, scaled_maxp = [], []
    unscaled_grad, scaled_grad = [], []

    for d in head_dims:
        q = rng.standard_normal((trials, d))
        k = rng.standard_normal((trials, 64, d))
        logits = np.einsum("td,tkd->tk", q, k)

        for scale, std_acc, maxp_acc, grad_acc in (
            (1.0, unscaled_std, unscaled_maxp, unscaled_grad),
            (1.0 / np.sqrt(d), scaled_std, scaled_maxp, scaled_grad),
        ):
            z = logits * scale
            std_acc.append(z.std())
            z = z - z.max(axis=1, keepdims=True)
            p = np.exp(z)
            p /= p.sum(axis=1, keepdims=True)
            maxp_acc.append(p.max(axis=1).mean())
            # Softmax Jacobian diagonal p(1-p): the gradient signal that
            # vanishes once one entry dominates.
            grad_acc.append((p * (1.0 - p)).sum(axis=1).mean())

    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.1))

    axes[0].plot(head_dims, unscaled_std, "o-", color=RED, label="no scaling")
    axes[0].plot(head_dims, scaled_std, "o-", color=BLUE, label="divide by $\\sqrt{d_k}$")
    axes[0].plot(head_dims, np.sqrt(head_dims), ":", color=MUTED, label="$\\sqrt{d_k}$")
    axes[0].set_xscale("log", base=2)
    axes[0].set_yscale("log", base=2)
    axes[0].set_xlabel("head dimension $d_k$")
    axes[0].set_ylabel("std. dev. of attention logits")
    axes[0].set_title("Logit scale grows as $\\sqrt{d_k}$")
    axes[0].legend(frameon=False, fontsize=9)

    axes[1].plot(head_dims, unscaled_maxp, "o-", color=RED, label="no scaling")
    axes[1].plot(head_dims, scaled_maxp, "o-", color=BLUE, label="divide by $\\sqrt{d_k}$")
    axes[1].set_xscale("log", base=2)
    axes[1].set_ylim(0, 1.02)
    axes[1].set_xlabel("head dimension $d_k$")
    axes[1].set_ylabel("mean max softmax probability")
    axes[1].set_title("Unscaled softmax saturates")
    axes[1].legend(frameon=False, fontsize=9)

    axes[2].plot(head_dims, unscaled_grad, "o-", color=RED, label="no scaling")
    axes[2].plot(head_dims, scaled_grad, "o-", color=BLUE, label="divide by $\\sqrt{d_k}$")
    axes[2].set_xscale("log", base=2)
    axes[2].set_xlabel("head dimension $d_k$")
    axes[2].set_ylabel("$\\sum_j p_j(1-p_j)$")
    axes[2].set_title("...and its gradient vanishes")
    axes[2].legend(frameon=False, fontsize=9)

    _finish(
        fig,
        "attn-softmax-scaling.svg",
        "Simulated, 4000 trials per point, 64 keys, i.i.d. standard-normal queries and keys.\n"
        "The dot product of two unit-variance vectors of length $d_k$ has standard deviation $\\sqrt{d_k}$, so\n"
        "without the $1/\\sqrt{d_k}$ factor a larger head dimension pushes softmax into saturation and kills the gradient.",
    )


# --------------------------------------------------------------------------
# 2. The causal mask, and why it goes before the softmax
# --------------------------------------------------------------------------


def fig_causal_mask() -> None:
    rng = np.random.default_rng(1)
    seq = 12
    scores = rng.standard_normal((seq, seq)) * 1.2
    allowed = np.tril(np.ones((seq, seq), dtype=bool))

    def softmax(z):
        z = z - z.max(axis=-1, keepdims=True)
        e = np.exp(z)
        return e / e.sum(axis=-1, keepdims=True)

    correct = softmax(np.where(allowed, scores, -np.inf))
    wrong = softmax(scores) * allowed  # masked AFTER the softmax

    fig, axes = plt.subplots(1, 3, figsize=(12.4, 4.2))

    axes[0].imshow(allowed, cmap="Blues", vmin=0, vmax=1.4, interpolation="nearest")
    axes[0].set_title("Causal mask: `tril`, diagonal included")
    axes[0].set_xlabel("key position $j$")
    axes[0].set_ylabel("query position $i$")
    axes[0].grid(False)

    axes[1].imshow(correct, cmap="Blues", interpolation="nearest")
    axes[1].set_title("Mask before softmax (correct)")
    axes[1].set_xlabel("key position $j$")
    axes[1].grid(False)

    axes[2].plot(np.arange(seq), correct.sum(axis=1), "o-", color=BLUE, label="mask before softmax")
    axes[2].plot(np.arange(seq), wrong.sum(axis=1), "o-", color=RED, label="mask after softmax")
    axes[2].axhline(1.0, color=MUTED, ls=":", lw=1)
    axes[2].set_ylim(0, 1.15)
    axes[2].set_xlabel("query position $i$")
    axes[2].set_ylabel("row sum of attention weights")
    axes[2].set_title("Masking after softmax breaks normalization")
    axes[2].legend(frameon=False, fontsize=9, loc="lower right")

    _finish(
        fig,
        "attn-causal-mask.svg",
        "Random scores, seq 12. Masking before the softmax lets it normalize over exactly the allowed keys, so every row sums to 1.\n"
        "Zeroing probabilities afterwards leaves early rows summing to far less than 1, shrinking the output by an amount that\n"
        "depends on position — a bug that trains, but badly.",
    )


# --------------------------------------------------------------------------
# 3. RoPE: the frequency ladder and the relative-position property
# --------------------------------------------------------------------------


def fig_rope() -> None:
    head_dim = 64
    base = 10000.0
    positions = np.arange(0, 96)
    inv_freq = 1.0 / (base ** (np.arange(0, head_dim, 2) / head_dim))

    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.1))

    for idx, colour in zip([0, 3, 8, 16, 28], [RED, ORANGE, GREEN, BLUE, VIOLET]):
        wavelength = 2 * np.pi / inv_freq[idx]
        angle = positions * inv_freq[idx]
        axes[0].plot(positions, np.cos(angle), color=colour, lw=1.5,
                     label=f"pair {idx} ($\\lambda$ = {wavelength:.0f})")
    axes[0].set_ylim(-1.08, 2.05)
    axes[0].set_xlabel("token position $m$")
    axes[0].set_ylabel("$\\cos(m\\theta_i)$")
    axes[0].set_title("A geometric ladder of rotation speeds")
    axes[0].legend(frameon=False, fontsize=8, ncol=2, loc="upper center")

    axes[1].plot(np.arange(len(inv_freq)), 2 * np.pi / inv_freq, "o-", color=BLUE)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("channel pair index $i$")
    axes[1].set_ylabel("wavelength (tokens)")
    axes[1].set_title("Low pairs encode local, high pairs global")

    rng = np.random.default_rng(2)
    q = rng.standard_normal(head_dim)
    k = rng.standard_normal(head_dim)

    def rotate(x, pos):
        angle = pos * inv_freq
        x1, x2 = x[0::2], x[1::2]
        out = np.empty_like(x)
        out[0::2] = x1 * np.cos(angle) - x2 * np.sin(angle)
        out[1::2] = x1 * np.sin(angle) + x2 * np.cos(angle)
        return out

    offsets = np.arange(0, 64)
    for m0, colour, marker in ((0, BLUE, "o"), (37, GREEN, "s"), (128, VIOLET, "^")):
        scores = [rotate(q, m0 + d) @ rotate(k, m0) for d in offsets]
        axes[2].plot(offsets, scores, marker, color=colour, ms=3.2, label=f"$n = {m0}$")
    axes[2].set_xlabel("relative offset $m - n$")
    axes[2].set_ylabel("$q_m \\cdot k_n$")
    axes[2].set_title("The score depends only on $m-n$")
    axes[2].legend(frameon=False, fontsize=9)

    _finish(
        fig,
        "rope-frequencies.svg",
        "head_dim 64, base 10000. Right: the same query and key vectors placed at three different absolute positions,\n"
        "swept over relative offset. All three curves coincide exactly, because a rotation by $m$ against a rotation by $n$\n"
        "leaves a rotation by $m-n$. Absolute position enters the computation; only relative position survives into the score.",
    )


# --------------------------------------------------------------------------
# 4. Where the parameters live
# --------------------------------------------------------------------------


def fig_param_breakdown() -> None:
    configs = [
        ("GPT-2 small\n124M", 12, 768, 50257, True),
        ("GPT-2 XL\n1.5B", 48, 1600, 50257, True),
        ("Llama-2 7B", 32, 4096, 32000, False),
        ("Llama-2 70B", 80, 8192, 32000, False),
    ]

    labels, attn, ffn, embed = [], [], [], []
    for name, layers, d, vocab, tied in configs:
        labels.append(name)
        attn.append(4 * layers * d * d)
        ffn.append(8 * layers * d * d)
        embed.append(vocab * d * (1 if tied else 2))

    attn = np.array(attn, dtype=float)
    ffn = np.array(ffn, dtype=float)
    embed = np.array(embed, dtype=float)
    total = attn + ffn + embed

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.3))

    x = np.arange(len(labels))
    axes[0].bar(x, attn / 1e9, color=BLUE, label="attention  $4Ld^2$")
    axes[0].bar(x, ffn / 1e9, bottom=attn / 1e9, color=VIOLET, label="FFN  $8Ld^2$")
    axes[0].bar(x, embed / 1e9, bottom=(attn + ffn) / 1e9, color=AMBER, label="embeddings  $Vd$")
    axes[0].set_xticks(x, labels, fontsize=9)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("parameters (billions, log scale)")
    axes[0].set_title("$N \\approx 12Ld^2 + Vd$")
    axes[0].legend(frameon=False, fontsize=9)

    axes[1].bar(x, 100 * embed / total, color=AMBER)
    for xi, frac in zip(x, 100 * embed / total):
        axes[1].text(xi, frac + 1.2, f"{frac:.0f}%", ha="center", fontsize=9, color=INK)
    axes[1].set_xticks(x, labels, fontsize=9)
    axes[1].set_ylabel("embeddings as % of parameters")
    axes[1].set_ylim(0, 45)
    axes[1].set_title("Why weight tying matters at small scale only")

    _finish(
        fig,
        "params-breakdown.svg",
        "Computed from $12Ld^2 + Vd$ using each model's published layer count, model dimension and vocabulary. GPT-2 ties its\n"
        "output head to the embedding, so its embedding term is counted once. The estimate lands within a few percent of the\n"
        "published totals; the gap is GQA, the exact SwiGLU hidden size, and norm parameters.",
    )


# --------------------------------------------------------------------------
# 5. KV cache: the reason GQA exists
# --------------------------------------------------------------------------


def fig_kv_cache() -> None:
    layers, head_dim, q_heads, dtype_bytes = 80, 128, 64, 2
    tp_degree = 2  # 140 GB of bf16 weights does not fit on one 80 GB card
    weights_per_gpu_gb = 70 * 2 / tp_degree
    hbm_gb = 80
    headroom_gb = hbm_gb - weights_per_gpu_gb  # 10 GB

    contexts = np.array([2048, 4096, 8192, 16384, 32768, 65536, 131072])
    variants = (("MHA (64 KV heads)", 64, RED), ("GQA (8 KV heads)", 8, BLUE), ("MQA (1 KV head)", 1, GREEN))

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.3))

    for label, kv_heads, colour in variants:
        gb = 2 * kv_heads * head_dim * dtype_bytes * layers * contexts / 1e9
        axes[0].plot(contexts, gb, "o-", color=colour, label=label)
    axes[0].axhline(headroom_gb, color=MUTED, ls="--", lw=1.2)
    axes[0].text(2300, headroom_gb * 1.15, "HBM left per GPU after weights (2-way TP)", fontsize=8.5, color=MUTED)
    axes[0].set_xscale("log", base=2)
    axes[0].set_yscale("log")
    axes[0].set_xlabel("context length (tokens)")
    axes[0].set_ylabel("KV cache per sequence (GB)")
    axes[0].set_title("Cache grows linearly in context")
    axes[0].legend(frameon=False, fontsize=9)

    batches = np.array([1, 2, 4, 8, 16, 32, 64, 128])
    ctx = 4096
    for label, kv_heads, colour in variants:
        gb = 2 * kv_heads * head_dim * dtype_bytes * layers * ctx * batches / 1e9
        axes[1].plot(batches, gb, "o-", color=colour, label=label)
    axes[1].axhline(headroom_gb, color=MUTED, ls="--", lw=1.2)
    axes[1].text(1.2, headroom_gb * 1.15, "HBM left per GPU after weights (2-way TP)", fontsize=8.5, color=MUTED)
    axes[1].set_xscale("log", base=2)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("concurrent sequences")
    axes[1].set_ylabel("total KV cache (GB)")
    axes[1].set_title("...and linearly in batch, at 4k context")
    axes[1].legend(frameon=False, fontsize=9)

    _finish(
        fig,
        "kv-cache-growth.svg",
        "Llama-2-70B geometry: 80 layers, head_dim 128, 64 query heads, bf16. Cache bytes = 2 (K and V) x kv_heads x head_dim x\n"
        "dtype_bytes x layers x tokens. The 140 GB of weights do not fit on one 80 GB card at all, so the dashed line is the per-GPU\n"
        "headroom in a two-way tensor-parallel deployment: 80 GB minus 70 GB of weights, leaving 10 GB for cache. GQA is what makes\n"
        "the batch sizes serving needs affordable.",
    )


# --------------------------------------------------------------------------
# 6. Training memory: where the bytes actually go
# --------------------------------------------------------------------------


def fig_training_memory() -> None:
    params_b = 7.0
    strategies = [
        ("fp32 + Adam", 4, 4, 8, 1.0),
        ("bf16 mixed +\nfp32 master", 6, 2, 8, 1.0),
        ("+ 8-bit Adam", 6, 2, 2, 1.0),
        ("+ activation\ncheckpointing", 6, 2, 2, 0.25),
        ("LoRA (r=16)\nfrozen base", 2, 0.001, 0.004, 0.4),
    ]

    labels = [s[0] for s in strategies]
    weights = np.array([s[1] * params_b for s in strategies])
    grads = np.array([s[2] * params_b for s in strategies])
    optim = np.array([s[3] * params_b for s in strategies])
    acts = np.array([s[4] * 24.0 for s in strategies])

    fig, ax = plt.subplots(figsize=(10.4, 4.6))
    x = np.arange(len(labels))
    ax.bar(x, weights, color=BLUE, label="weights (+ master copy)")
    ax.bar(x, grads, bottom=weights, color=TEAL, label="gradients")
    ax.bar(x, optim, bottom=weights + grads, color=VIOLET, label="optimizer state")
    ax.bar(x, acts, bottom=weights + grads + optim, color=AMBER, label="activations")
    ax.axhline(80, color=RED, ls="--", lw=1.3)
    ax.text(len(labels) - 0.45, 83, "one 80 GB GPU", fontsize=9, color=RED, ha="right")

    totals = weights + grads + optim + acts
    for xi, total in zip(x, totals):
        ax.text(xi, total + 3, f"{total:.0f} GB", ha="center", fontsize=9.5, color=INK)

    ax.set_xticks(x, labels, fontsize=9)
    ax.set_ylabel("memory (GB)")
    ax.set_ylim(0, max(totals) * 1.22)
    ax.set_title("Training a 7B model: what each trick buys")
    ax.legend(frameon=False, fontsize=9)

    _finish(
        fig,
        "training-memory.svg",
        "7B parameters. Weights, gradients and optimizer state are exact bytes-per-parameter arithmetic; the activation term is a\n"
        "24 GB reference figure for a moderate batch and sequence length, scaled by each strategy. Note that bf16 mixed precision\n"
        "does not reduce total memory much on its own — it buys throughput. The optimizer state is the first thing worth attacking.",
    )


# --------------------------------------------------------------------------
# 7. Learning-rate schedules
# --------------------------------------------------------------------------


def fig_lr_schedules() -> None:
    steps = np.arange(0, 100_000)
    peak, warmup, final_frac = 3e-4, 2000, 0.1

    def cosine(t):
        lr = np.where(t < warmup, peak * t / warmup, 0.0)
        prog = np.clip((t - warmup) / (steps[-1] - warmup), 0, 1)
        decayed = peak * (final_frac + (1 - final_frac) * 0.5 * (1 + np.cos(np.pi * prog)))
        return np.where(t < warmup, lr, decayed)

    def wsd(t, decay_frac=0.2):
        decay_start = steps[-1] * (1 - decay_frac)
        out = np.where(t < warmup, peak * t / warmup, peak)
        tail = np.clip((t - decay_start) / (steps[-1] - decay_start), 0, 1)
        return np.where(t >= decay_start, peak * (1 - tail) + peak * final_frac * tail, out)

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.2))

    axes[0].plot(steps, cosine(steps) * 1e4, color=BLUE, label="warmup + cosine")
    axes[0].plot(steps, wsd(steps) * 1e4, color=GREEN, label="warmup-stable-decay")
    axes[0].plot(steps, np.full_like(steps, peak, dtype=float) * 1e4, ls=":", color=MUTED, label="constant")
    axes[0].set_xlabel("step")
    axes[0].set_ylabel("learning rate ($\\times 10^{-4}$)")
    axes[0].set_title("Schedules in use today")
    axes[0].legend(frameon=False, fontsize=9)

    zoom = steps[:6000]
    axes[1].plot(zoom, cosine(zoom) * 1e4, color=BLUE)
    axes[1].axvline(warmup, color=RED, ls="--", lw=1.2)
    axes[1].text(warmup * 1.15, peak * 1e4 * 0.35, "warmup ends", fontsize=9, color=RED)
    axes[1].set_xlabel("step")
    axes[1].set_ylabel("learning rate ($\\times 10^{-4}$)")
    axes[1].set_title("Warmup: the first 2k steps")

    _finish(
        fig,
        "lr-schedules.svg",
        "Peak $3\\times10^{-4}$, 2000 warmup steps, cosine decay to 10% of peak. Warmup exists because Adam's second-moment estimate is\n"
        "unreliable early — a full-size step on a near-zero $v$ produces an enormous update. Warmup-stable-decay holds the peak and\n"
        "collapses only at the end, which lets you branch a run at any point without having committed to a total step count.",
    )


# --------------------------------------------------------------------------
# 8. Scaling laws: the compute-optimal frontier
# --------------------------------------------------------------------------


def fig_scaling_laws() -> None:
    # Hoffmann et al. parametric form: L(N, D) = E + A/N^alpha + B/D^beta
    E, A, B, alpha, beta = 1.69, 406.4, 410.7, 0.34, 0.28

    def loss(n, d):
        return E + A / n**alpha + B / d**beta

    budgets = np.logspace(19, 24, 40)
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.3))

    ns = np.logspace(8, 12, 300)
    for budget, colour in zip([1e20, 1e21, 1e22, 1e23], [AMBER, ORANGE, BLUE, VIOLET]):
        ds = budget / (6 * ns)
        ls = loss(ns, ds)
        axes[0].plot(ns, ls, color=colour, lw=1.5, label=f"C = {budget:.0e} FLOPs")
        best = np.argmin(ls)
        axes[0].plot(ns[best], ls[best], "o", color=colour, ms=7)
    axes[0].set_xscale("log")
    axes[0].set_xlabel("parameters $N$")
    axes[0].set_ylabel("loss")
    axes[0].set_ylim(1.6, 4.0)
    axes[0].set_title("At a fixed budget, loss is U-shaped in model size")
    axes[0].legend(frameon=False, fontsize=8.5)

    opt_n, opt_d = [], []
    for budget in budgets:
        ds = budget / (6 * ns)
        best = np.argmin(loss(ns, ds))
        opt_n.append(ns[best])
        opt_d.append(ds[best])
    opt_n = np.array(opt_n)
    opt_d = np.array(opt_d)

    axes[1].plot(budgets, opt_d / opt_n, color=BLUE, lw=1.8,
                 label="optimum of the published parametric fit")
    axes[1].axhline(20, color=GREEN, ls="--", lw=1.5,
                    label="the paper's own headline: 20 tokens/param")
    # Real deployed models, computed from published token counts.
    deployed = [
        ("Llama-2-70B", 2.0e12 / 70e9),
        ("Llama-3-70B", 15e12 / 70e9),
        ("Llama-2-7B", 2.0e12 / 7e9),
        ("Llama-3-8B", 15e12 / 8e9),
    ]
    for i, (name, ratio) in enumerate(deployed):
        axes[1].plot(6e23, ratio, "o", color=ORANGE, ms=7)
        axes[1].annotate(name, (6e23, ratio), textcoords="offset points",
                         xytext=(-6, 4 if i % 2 == 0 else -12), fontsize=7.5,
                         color=ORANGE, ha="right")
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_ylim(5, 3000)
    axes[1].set_xlabel("training compute $C$ (FLOPs)")
    axes[1].set_ylabel("tokens per parameter $D/N$")
    axes[1].set_title("Deployed models train far past any optimum")
    axes[1].legend(frameon=False, fontsize=8, loc="upper left")

    _finish(
        fig,
        "scaling-laws.svg",
        "Loss curves from the Hoffmann et al. (2022) parametric fit $L = 1.69 + 406.4/N^{0.34} + 410.7/D^{0.28}$, with $C = 6ND$.\n"
        "Left: the experiment that produced Chinchilla — sweep model size at fixed compute and read off the minimum. Right: note that the\n"
        "published fit's own optimum (blue) runs from about 30 to 95 tokens per parameter and never meets the paper's 20:1 headline (green).\n"
        "That inconsistency in the published Approach-3 constants is real and documented; the 20:1 rule comes from the paper's other two\n"
        "methods. Either way, deployed models (orange) sit far above both, because the cost that matters to them is inference, not training.",
    )


# --------------------------------------------------------------------------
# 9. Prefill vs decode: why generation is memory-bound
# --------------------------------------------------------------------------


def fig_arithmetic_intensity() -> None:
    # H100 SXM: ~990 TFLOP/s bf16 dense, ~3.35 TB/s HBM.
    peak_flops = 990e12
    bandwidth = 3.35e12
    ridge = peak_flops / bandwidth

    intensity = np.logspace(-1, 4, 400)
    attainable = np.minimum(peak_flops, bandwidth * intensity) / 1e12

    fig, ax = plt.subplots(figsize=(9.8, 4.8))
    ax.plot(intensity, attainable, color=INK, lw=2)
    ax.axvline(ridge, color=MUTED, ls=":", lw=1.2)
    ax.text(ridge * 1.15, 4, f"ridge point\n{ridge:.0f} FLOP/byte", fontsize=9, color=MUTED)

    points = [
        ("decode, batch 1", 1.0, GREEN),
        ("decode, batch 8", 8.0, TEAL),
        ("decode, batch 64", 64.0, BLUE),
        ("decode, batch 256", 256.0, VIOLET),
        ("prefill (2k tokens)", 2048.0, RED),
    ]
    for label, oi, colour in points:
        y = min(peak_flops, bandwidth * oi) / 1e12
        ax.plot(oi, y, "o", color=colour, ms=9)
        ax.annotate(
            f"{label}\n{100 * y / (peak_flops / 1e12):.3g}% of peak",
            (oi, y),
            textcoords="offset points",
            xytext=(8, -22),
            fontsize=8.5,
            color=colour,
        )

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("arithmetic intensity (FLOP per byte read)")
    ax.set_ylabel("attainable throughput (TFLOP/s)")
    ax.set_title("Roofline: decoding lives on the memory-bound slope")
    ax.set_ylim(1, 2000)

    _finish(
        fig,
        "roofline-decode.svg",
        "H100 SXM figures: ~990 TFLOP/s dense bf16, ~3.35 TB/s HBM, giving a ridge point near 295 FLOP/byte. During decoding you read\n"
        "every weight to produce one token per sequence, so arithmetic intensity is roughly the batch size. This single plot is the\n"
        "argument for continuous batching, for GQA, for weight-only quantization, and for speculative decoding all at once.",
    )


# --------------------------------------------------------------------------
# 10. Sampling: what temperature, top-k and top-p actually do
# --------------------------------------------------------------------------


def fig_sampling() -> None:
    rng = np.random.default_rng(7)
    vocab = 40
    logits = np.sort(rng.standard_normal(vocab) * 2.2)[::-1]

    def softmax(z):
        z = z - z.max()
        e = np.exp(z)
        return e / e.sum()

    base = softmax(logits)
    idx = np.arange(vocab)

    fig, axes = plt.subplots(1, 3, figsize=(12.6, 4.1))

    for temp, colour in ((0.5, BLUE), (1.0, INK), (1.5, ORANGE)):
        axes[0].plot(idx, softmax(logits / temp), "o-", ms=3, color=colour, label=f"T = {temp}")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("token rank")
    axes[0].set_ylabel("probability")
    axes[0].set_title("Temperature rescales the logits")
    axes[0].legend(frameon=False, fontsize=9)

    for k, colour in ((5, GREEN), (20, BLUE)):
        p = base.copy()
        p[k:] = 0
        p = p / p.sum()
        axes[1].plot(idx, np.where(p > 0, p, np.nan), "o-", ms=3, color=colour, label=f"top-k, k = {k}")
    axes[1].plot(idx, base, ":", color=MUTED, label="unmodified")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("token rank")
    axes[1].set_title("Top-k truncates at a fixed count")
    axes[1].legend(frameon=False, fontsize=9)

    cum = np.cumsum(base)
    for top_p, colour in ((0.9, VIOLET), (0.95, PINK)):
        keep = int(np.searchsorted(cum, top_p) + 1)
        p = base.copy()
        p[keep:] = 0
        p = p / p.sum()
        axes[2].plot(idx, np.where(p > 0, p, np.nan), "o-", ms=3, color=colour, label=f"top-p = {top_p} ({keep} tokens)")
    axes[2].plot(idx, base, ":", color=MUTED, label="unmodified")
    axes[2].set_yscale("log")
    axes[2].set_xlabel("token rank")
    axes[2].set_title("Top-p truncates at a fixed mass")
    axes[2].legend(frameon=False, fontsize=9)

    _finish(
        fig,
        "sampling-strategies.svg",
        "One synthetic next-token distribution over 40 tokens, log scale. Temperature reshapes the whole distribution; top-k and top-p\n"
        "truncate it. The reason top-p is usually preferred: a fixed k is too permissive when the model is confident and too restrictive\n"
        "when it is not, whereas nucleus sampling adapts its cutoff to the shape of each distribution.",
    )


# --------------------------------------------------------------------------
# 11. Floating-point formats
# --------------------------------------------------------------------------


def fig_precision_formats() -> None:
    formats = [
        ("fp32", 1, 8, 23, 3.4e38, 1.2e-7),
        ("tf32", 1, 8, 10, 3.4e38, 9.8e-4),
        ("bf16", 1, 8, 7, 3.4e38, 7.8e-3),
        ("fp16", 1, 5, 10, 6.5e4, 9.8e-4),
        ("fp8 E4M3", 1, 4, 3, 4.48e2, 1.25e-1),
        ("fp8 E5M2", 1, 5, 2, 5.7344e4, 2.5e-1),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.4))

    ax = axes[0]
    for row, (name, sign, exp, mant, _, _) in enumerate(formats):
        y = len(formats) - row - 1
        ax.add_patch(mpatches.Rectangle((0, y - 0.32), sign, 0.64, facecolor=MUTED, edgecolor=BG))
        ax.add_patch(mpatches.Rectangle((sign, y - 0.32), exp, 0.64, facecolor=RED, edgecolor=BG))
        ax.add_patch(mpatches.Rectangle((sign + exp, y - 0.32), mant, 0.64, facecolor=BLUE, edgecolor=BG))
        ax.text(-0.8, y, name, ha="right", va="center", fontsize=10, color=INK)
        ax.text(sign + exp / 2, y, f"{exp}", ha="center", va="center", fontsize=9, color="white")
        if mant >= 2:
            ax.text(sign + exp + mant / 2, y, f"{mant}", ha="center", va="center", fontsize=9, color="white")
    ax.set_xlim(-7, 33)
    ax.set_ylim(-0.8, len(formats) - 0.2)
    ax.set_yticks([])
    ax.set_xlabel("bits")
    ax.set_title("Exponent bits set range; mantissa bits set precision")
    ax.grid(False)
    ax.legend(
        handles=[
            mpatches.Patch(color=MUTED, label="sign"),
            mpatches.Patch(color=RED, label="exponent"),
            mpatches.Patch(color=BLUE, label="mantissa"),
        ],
        frameon=False,
        fontsize=9,
        loc="lower right",
    )

    ax = axes[1]
    names = [f[0] for f in formats]
    maxes = np.array([f[4] for f in formats])
    eps = np.array([f[5] for f in formats])
    y = np.arange(len(names))[::-1]
    ax.barh(y + 0.18, np.log10(maxes), height=0.34, color=RED, label="$\\log_{10}$ max value")
    ax.barh(y - 0.18, -np.log10(eps), height=0.34, color=BLUE, label="decimal digits of precision")
    ax.set_yticks(y, names, fontsize=10)
    ax.set_xlabel("orders of magnitude")
    ax.set_title("bf16 trades precision for fp32's range")
    ax.legend(frameon=False, fontsize=9, loc="lower right")

    _finish(
        fig,
        "precision-formats.svg",
        "bf16 and fp32 share an 8-bit exponent, so a bf16 cast never overflows where fp32 would not — which is exactly why bf16 replaced\n"
        "fp16 for training and why loss scaling became unnecessary. fp16's 5-bit exponent tops out at 65504, and gradients underflow long\n"
        "before that. The price of bf16 is 7 mantissa bits, which is why norms and reductions are still computed in fp32.",
    )


# --------------------------------------------------------------------------
# 12. Speculative decoding: expected speedup
# --------------------------------------------------------------------------


def fig_speculative() -> None:
    gammas = np.array([1, 2, 3, 4, 5, 6, 7, 8])
    alphas = [0.6, 0.7, 0.8, 0.9]

    fig, axes = plt.subplots(1, 2, figsize=(11.6, 4.2))

    for alpha, colour in zip(alphas, [AMBER, ORANGE, BLUE, VIOLET]):
        expected = (1 - alpha ** (gammas + 1)) / (1 - alpha)
        axes[0].plot(gammas, expected, "o-", color=colour, label=f"acceptance $\\alpha$ = {alpha}")
    axes[0].plot(gammas, gammas + 1, ":", color=MUTED, label="perfect drafting")
    axes[0].set_xlabel("draft length $\\gamma$")
    axes[0].set_ylabel("expected tokens per verify step")
    axes[0].set_title("Diminishing returns from longer drafts")
    axes[0].legend(frameon=False, fontsize=9)

    # Wall-clock speedup with a draft model costing c times the target step.
    for cost, colour in zip([0.05, 0.1, 0.2, 0.3], [GREEN, TEAL, BLUE, RED]):
        alpha = 0.8
        expected = (1 - alpha ** (gammas + 1)) / (1 - alpha)
        speedup = expected / (1 + cost * gammas)
        axes[1].plot(gammas, speedup, "o-", color=colour, label=f"draft cost = {cost:.0%} of target")
        best = int(np.argmax(speedup))
        axes[1].plot(gammas[best], speedup[best], "*", color=colour, ms=14)
    axes[1].axhline(1.0, color=MUTED, ls=":", lw=1)
    axes[1].set_xlabel("draft length $\\gamma$")
    axes[1].set_ylabel("wall-clock speedup")
    axes[1].set_title("Optimal $\\gamma$ at $\\alpha = 0.8$ (stars)")
    axes[1].legend(frameon=False, fontsize=8.5)

    _finish(
        fig,
        "speculative-decoding.svg",
        "Left: with per-token acceptance probability $\\alpha$, a draft of length $\\gamma$ yields $(1-\\alpha^{\\gamma+1})/(1-\\alpha)$ tokens per verification\n"
        "step in expectation — one rejection ends the run, so the tail is geometric. Right: dividing by the draft's own cost gives the\n"
        "wall-clock picture, and an optimal draft length that is short. Speculative decoding leaves the output distribution exactly unchanged.",
    )


# --------------------------------------------------------------------------
# 13. Post-training: the family tree of preference methods
# --------------------------------------------------------------------------


def fig_posttraining_map() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 4.3))
    ax.set_xlim(0, 12)
    ax.set_ylim(0.75, 6.15)
    ax.axis("off")

    def box(x, y, w, h, text, colour, fontsize=9.5, text_colour="white"):
        ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.06", facecolor=colour, edgecolor="none"))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fontsize, color=text_colour, linespacing=1.35)

    def arrow(x1, y1, x2, y2):
        ax.annotate("", (x2, y2), (x1, y1), arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.4))

    box(0.2, 4.7, 2.3, 1.0, "Pretrained\nbase model", INK)
    box(3.1, 4.7, 2.3, 1.0, "SFT\ninstruction data", BLUE)
    arrow(2.5, 5.2, 3.05, 5.2)

    box(6.0, 4.7, 2.3, 1.0, "Reward model\npairwise preferences", VIOLET)
    arrow(5.4, 5.2, 5.95, 5.2)

    box(9.0, 4.7, 2.6, 1.0, "PPO\nactor + critic + RM\n+ KL to reference", RED, fontsize=8.8)
    arrow(8.3, 5.2, 8.95, 5.2)

    box(6.0, 2.7, 2.3, 1.1, "DPO\nno reward model,\nno sampling", GREEN, fontsize=8.8)
    arrow(4.25, 4.65, 6.6, 3.85)

    box(9.0, 2.7, 2.6, 1.1, "GRPO\ngroup baseline,\nno critic", ORANGE, fontsize=8.8)
    arrow(4.4, 4.62, 9.6, 3.85)

    box(0.2, 1.0, 5.0, 1.2,
        "What each removes\n"
        "DPO: the reward model and the sampling loop\n"
        "GRPO: the value network, replaced by a group mean",
        BG, fontsize=9, text_colour=INK)
    ax.add_patch(mpatches.FancyBboxPatch((0.2, 1.0), 5.0, 1.2, boxstyle="round,pad=0.06",
                                         facecolor="none", edgecolor=MUTED, lw=1.1))

    box(6.0, 1.0, 5.6, 1.2,
        "Where each is used\n"
        "DPO: cheap alignment when you have preference pairs\n"
        "GRPO: verifiable-reward RL — maths, code, reasoning",
        BG, fontsize=9, text_colour=INK)
    ax.add_patch(mpatches.FancyBboxPatch((6.0, 1.0), 5.6, 1.2, boxstyle="round,pad=0.06",
                                         facecolor="none", edgecolor=MUTED, lw=1.1))

    ax.set_title("Post-training: what each method drops from the one before", fontsize=12, color=INK, pad=14)

    _finish(
        fig,
        "posttraining-map.svg",
        "The classic RLHF pipeline is the top row. DPO reparameterizes the RLHF objective so the optimal policy can be trained directly on\n"
        "preference pairs, deleting both the reward model and the sampling loop. GRPO keeps online RL but replaces the learned value network\n"
        "with the mean reward of a sampled group, which is what makes large-scale verifiable-reward training affordable.",
    )


# --------------------------------------------------------------------------
# 14. Tokenization: what a vocabulary size buys
# --------------------------------------------------------------------------


def fig_tokenizer_tradeoff() -> None:
    vocabs = np.array([1_000, 4_000, 8_000, 16_000, 32_000, 64_000, 128_000, 256_000])
    # Heaps/Zipf-flavoured model: compression improves sublinearly in vocab size.
    bytes_per_token = 1.6 + 2.9 * (1 - np.exp(-np.log(vocabs / 500) / 3.1))

    d_models = [(768, "small, d=768"), (4096, "7B, d=4096"), (8192, "70B, d=8192")]

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.3))

    axes[0].plot(vocabs, bytes_per_token, "o-", color=BLUE)
    axes[0].set_xscale("log", base=2)
    axes[0].set_xlabel("vocabulary size")
    axes[0].set_ylabel("bytes per token (compression)")
    axes[0].set_title("Compression improves with sharply diminishing returns")
    axes[0].annotate("most models sit here", (32_000, bytes_per_token[4]), textcoords="offset points",
                     xytext=(-30, -34), fontsize=9, color=MUTED,
                     arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.1))

    for d, label in d_models:
        embed_params = vocabs * d * 2 / 1e6
        axes[1].plot(vocabs, embed_params, "o-", label=label)
    axes[1].set_xscale("log", base=2)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("vocabulary size")
    axes[1].set_ylabel("embedding + output head (M params)")
    axes[1].set_title("...and the cost is paid in embedding parameters")
    axes[1].legend(frameon=False, fontsize=9)

    _finish(
        fig,
        "tokenizer-tradeoff.svg",
        "Left: an illustrative compression curve with the sublinear shape BPE actually exhibits — doubling the vocabulary buys steadily less.\n"
        "Right: exact parameter arithmetic for an untied embedding and output head. A bigger vocabulary means fewer tokens per document\n"
        "(cheaper training and inference per character) but more embedding parameters and a larger, slower softmax.",
    )



# --------------------------------------------------------------------------
# 15. KV cache schemes: how MLA differs from head-sharing
# --------------------------------------------------------------------------


def fig_kv_cache_schemes() -> None:
    """MHA/GQA/MQA all shrink the cache by sharing heads; MLA compresses instead."""
    n_heads, head_dim, layers = 128, 128, 61  # DeepSeek-V3 geometry
    kv_lora_rank, rope_dim = 512, 64

    schemes = [
        ("MHA\n128 KV heads", 2 * n_heads * head_dim, RED),
        ("GQA-8\n8 KV heads", 2 * 8 * head_dim, BLUE),
        ("MQA\n1 KV head", 2 * 1 * head_dim, GREEN),
        ("MLA\n512 latent + 64 RoPE", kv_lora_rank + rope_dim, VIOLET),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.5))

    labels = [s[0] for s in schemes]
    elems = np.array([s[1] for s in schemes], dtype=float)
    colours = [s[2] for s in schemes]
    bars = axes[0].bar(labels, elems, color=colours, width=0.62)
    axes[0].set_yscale("log")
    axes[0].set_ylabel("cached elements / token / layer")
    axes[0].set_title("What one token costs the cache")
    axes[0].grid(axis="x", visible=False)
    for bar, value in zip(bars, elems):
        axes[0].text(
            bar.get_x() + bar.get_width() / 2,
            value * 1.18,
            f"{int(value):,}\n{elems[0] / value:.0f}x smaller" if value != elems[0] else f"{int(value):,}\nbaseline",
            ha="center",
            fontsize=8.5,
            color=MUTED,
        )
    axes[0].set_ylim(top=elems.max() * 4)

    contexts = np.array([4096, 8192, 16384, 32768, 65536, 131072])
    batch, dtype_bytes = 32, 2
    for label, per_token, colour in schemes:
        gb = per_token * dtype_bytes * layers * contexts * batch / 1e9
        axes[1].plot(contexts, gb, "o-", color=colour, label=label.replace("\n", " "))
    axes[1].axhline(8 * 80, color=MUTED, ls="--", lw=1.2)
    axes[1].text(4400, 8 * 80 * 1.15, "aggregate HBM, 8x H100", fontsize=8.5, color=MUTED)
    axes[1].set_xscale("log", base=2)
    axes[1].set_yscale("log")
    axes[1].set_xlabel("context length (tokens)")
    axes[1].set_ylabel("total KV cache at batch 32 (GB)")
    axes[1].set_title("Whether 32 concurrent users fit on a node")
    axes[1].legend(frameon=False, fontsize=8.5)

    _finish(
        fig,
        "kv-cache-schemes.svg",
        "DeepSeek-V3 geometry: 61 layers, 128 query heads, head_dim 128, bf16. GQA and MQA shrink the cache by giving several query\n"
        "heads one KV head, trading a little quality for it; MLA instead caches a 512-dim latent plus a 64-dim shared RoPE key and\n"
        "reconstructs K and V on the fly, landing 57x below MHA -- MQA territory -- with no head tying and reported quality at or above\n"
        "MHA's. The dashed line is one 8xH100 node's total memory, before weights: at 128k context and batch 32, MHA wants over 25\n"
        "nodes' worth of cache and MLA fits in half of one.",
    )


# --------------------------------------------------------------------------
# 16. Sliding-window and hybrid attention
# --------------------------------------------------------------------------


def fig_attention_patterns() -> None:
    """Full causal vs sliding-window, and what a 5:1 hybrid stack does to memory."""
    n, window = 40, 10
    idx = np.arange(n)
    causal = (idx[:, None] >= idx[None, :]).astype(float)
    sliding = causal * (idx[:, None] - idx[None, :] < window)
    sink = sliding.copy()
    sink[:, :2] = causal[:, :2]  # first tokens stay attendable: attention sinks

    # No explicit wspace here: setting one makes the figure incompatible with
    # tight_layout, and the caption band _finish reserves is laid out by it.
    fig, axes = plt.subplots(1, 4, figsize=(12.6, 4.0), gridspec_kw={"width_ratios": [1, 1, 1, 1.75]})

    for ax, (mat, title) in zip(
        axes,
        (
            (causal, "Full causal\nevery layer"),
            (sliding, f"Sliding window\nw = {window}"),
            (sink, f"Window + 2 sinks\nw = {window}"),
        ),
    ):
        ax.imshow(mat, cmap="Blues", vmin=0, vmax=1.35, interpolation="nearest", aspect="auto")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("key position", fontsize=9)
        ax.set_xticks([0, n - 1])
        ax.set_yticks([0, n - 1])
        ax.grid(False)
    axes[0].set_ylabel("query position", fontsize=9)

    ax = axes[3]
    contexts = np.array([8192, 16384, 32768, 65536, 131072])
    layers, mb_per_token_layer = 48, 32 / 1000
    all_global = layers * mb_per_token_layer * contexts / 1000
    local_window = 1024
    hybrid = (layers / 6) * mb_per_token_layer * contexts / 1000 + (5 * layers / 6) * mb_per_token_layer * local_window / 1000
    ax.plot(contexts / 1000, all_global, "o-", color=RED, label="all layers global")
    ax.plot(contexts / 1000, hybrid, "o-", color=GREEN, label="5 local : 1 global, w = 1024")
    ax.set_xlabel("context length (thousands of tokens)")
    ax.set_ylabel("KV cache per sequence (GB)")
    ax.set_title("Only global layers pay for context", fontsize=10)
    ax.legend(frameon=False, fontsize=8.5, loc="upper left")
    ax.annotate(
        f"{all_global[-1] / hybrid[-1]:.1f}x less at 128k",
        xy=(contexts[-1] / 1000, hybrid[-1]),
        xytext=(44, all_global[-1] * 0.68),
        fontsize=9,
        color=MUTED,
        arrowprops=dict(arrowstyle="->", color=MUTED, lw=1),
    )

    _finish(
        fig,
        "attention-patterns.svg",
        "Left three: which keys a query may attend to. A sliding window makes the per-layer cache constant in context instead of linear,\n"
        "but evicting the first tokens collapses quality -- models dump surplus attention mass there -- so those slots are kept, either\n"
        "explicitly (attention sinks) or as a learned per-head sink logit. Right: a 48-layer model, 8 KV heads, head_dim 128, bf16.\n"
        "Interleaving five windowed layers per global layer, as Gemma 3 does, is what makes a 128k context affordable.",
    )


# --------------------------------------------------------------------------
# 17. fp8 scaling granularity
# --------------------------------------------------------------------------


def fig_fp8_scaling() -> None:
    """Why integer formats need fine-grained scales far more than fp8 does."""

    def e4m3(v: np.ndarray) -> np.ndarray:
        """Round to OCP e4m3: 3 mantissa bits, min subnormal 2^-9, max 448.

        Verified element-for-element against torch's float8_e4m3fn cast over
        10k values spanning subnormals, normals, and the clipping range.
        """
        v = np.clip(v, -448.0, 448.0)
        a = np.abs(v)
        nz = a > 0
        exponent = np.floor(np.log2(a, where=nz, out=np.full_like(a, -30.0)))
        exponent = np.clip(exponent, -6, 8)
        step = np.power(2.0, exponent - 3)
        return np.clip(np.round(v / step) * step, -448.0, 448.0)

    def quantise(x: np.ndarray, block: int, fmt: str) -> np.ndarray:
        out = np.empty_like(x)
        for start in range(0, x.size, block):
            chunk = x[start : start + block]
            amax = np.abs(chunk).max()
            if amax == 0:
                out[start : start + block] = chunk
            elif fmt == "fp8":
                scale = 448.0 / amax
                out[start : start + block] = e4m3(chunk * scale) / scale
            else:
                step = amax / 127.0
                out[start : start + block] = np.clip(np.round(chunk / step), -127, 127) * step
        return out

    rng = np.random.default_rng(7)
    n = 4096
    base = rng.normal(0, 1, n)
    outlier_slots = rng.choice(n, 4, replace=False)

    def error(fmt: str, block: int, mult: float) -> float:
        x = base.copy()
        x[outlier_slots] = mult
        q = quantise(x, block, fmt)
        ordinary = np.abs(x) < 10  # fidelity of the values carrying the signal
        return float((np.abs(q - x)[ordinary] / np.abs(x)[ordinary]).mean() * 100)

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.4))

    blocks = [(n, "per-tensor"), (512, "512"), (128, "128"), (32, "32")]
    xs = np.arange(len(blocks))
    for fmt, colour, label in (("int8", RED, "int8 (fixed step)"), ("fp8", BLUE, "fp8 e4m3 (4 exponent bits)")):
        axes[0].plot(xs, [error(fmt, b, 100) for b, _ in blocks], "o-", color=colour, label=label)
    axes[0].set_xticks(xs)
    axes[0].set_xticklabels([lbl for _, lbl in blocks])
    axes[0].set_yscale("log")
    axes[0].set_xlabel("scaling block size (elements per scale)")
    axes[0].set_ylabel("mean relative error, ordinary values (%)")
    axes[0].set_title("With a 100x outlier present")
    axes[0].legend(frameon=False, fontsize=9)

    mults = np.array([1, 3, 10, 30, 100, 300, 1000], dtype=float)
    for fmt, block, colour, style, label in (
        ("int8", n, RED, "-", "int8, per-tensor"),
        ("int8", 128, ORANGE, "-", "int8, block 128"),
        ("fp8", n, VIOLET, "--", "fp8, per-tensor"),
        ("fp8", 128, BLUE, "-", "fp8, block 128"),
    ):
        axes[1].plot(mults, [error(fmt, block, m) for m in mults], style, marker="o", ms=4, color=colour, label=label)
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("outlier magnitude (x the typical value)")
    axes[1].set_ylabel("mean relative error, ordinary values (%)")
    axes[1].set_title("fp8 spends exponent bits so scaling does not have to")
    axes[1].legend(frameon=False, fontsize=8.5)

    _finish(
        fig,
        "fp8-scaling-granularity.svg",
        "4096 standard-normal values with four outliers, quantised two ways. int8 has a fixed step set by the block maximum, so one\n"
        "outlier consumes the range every other value needed: per-tensor error runs away with outlier size, and shrinking the block is\n"
        "the only fix. fp8 carries its own exponent per element, so it barely notices -- which is the real reason a low-bit integer\n"
        "format lives or dies on scaling granularity while fp8 does not. Fine-grained fp8 scaling (DeepSeek-V3's 128-wide blocks,\n"
        "Blackwell's 32-element MX) still buys the last fraction of a percent, but fp8's harder problem is accumulation precision, not\n"
        "this.",
    )


# --------------------------------------------------------------------------
# 18. Muon: what orthogonalizing an update actually does
# --------------------------------------------------------------------------


def fig_muon() -> None:
    """A momentum update is dominated by a few directions; Muon equalizes them."""
    rng = np.random.default_rng(3)
    m, n = 256, 128
    # A realistic momentum buffer: low-rank-dominated, with a long tail.
    scales = np.concatenate([np.linspace(9.0, 3.0, 6), 1.0 / np.sqrt(np.arange(1, n - 5))])
    G = (rng.normal(size=(m, n)) * scales) @ np.linalg.qr(rng.normal(size=(n, n)))[0]

    def newton_schulz(X: np.ndarray, steps: int = 5) -> np.ndarray:
        a, b, c = 3.4445, -4.7750, 2.0315
        Y = X / (np.linalg.norm(X) + 1e-7)
        transposed = Y.shape[0] > Y.shape[1]
        if transposed:
            Y = Y.T
        for _ in range(steps):
            A = Y @ Y.T
            Y = a * Y + (b * A + c * (A @ A)) @ Y
        return Y.T if transposed else Y

    s_raw = np.linalg.svd(G, compute_uv=False)
    s_ns = np.linalg.svd(newton_schulz(G), compute_uv=False)

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.3))

    axes[0].plot(s_raw / s_raw[0], "o-", ms=3.5, color=RED, label="raw momentum update")
    axes[0].plot(s_ns / s_ns[0], "o-", ms=3.5, color=VIOLET, label="after 5 Newton-Schulz steps")
    axes[0].set_yscale("log")
    axes[0].set_xlabel("singular value index")
    axes[0].set_ylabel("singular value (normalized)")
    axes[0].set_title("Muon flattens the update's spectrum")
    axes[0].legend(frameon=False, fontsize=9)

    frac_raw = np.cumsum(s_raw**2) / np.sum(s_raw**2)
    frac_ns = np.cumsum(s_ns**2) / np.sum(s_ns**2)
    axes[1].plot(np.arange(1, n + 1), frac_raw * 100, color=RED, lw=2, label="raw momentum update")
    axes[1].plot(np.arange(1, n + 1), frac_ns * 100, color=VIOLET, lw=2, label="orthogonalized")
    k = int(np.searchsorted(frac_raw, 0.5) + 1)
    axes[1].axvline(k, color=MUTED, ls="--", lw=1)
    axes[1].text(k + 6, 20, f"half the raw update's\nenergy sits in {k} of {n} directions", fontsize=8.5, color=MUTED)
    axes[1].set_xlabel("number of directions kept")
    axes[1].set_ylabel("cumulative share of update energy (%)")
    axes[1].set_title("...so the step stops being a few directions")
    axes[1].legend(frameon=False, fontsize=9, loc="lower right")

    _finish(
        fig,
        "muon-orthogonalization.svg",
        "A synthetic 256x128 momentum buffer built to be low-rank-dominated, the way real ones are, and the same matrix after Muon's\n"
        "five quintic Newton-Schulz steps (coefficients 3.4445, -4.7750, 2.0315). Newton-Schulz approximates the orthogonal factor of\n"
        "the update, driving every singular value toward 1, so a step moves the weight matrix by a comparable amount in every direction\n"
        "instead of being spent on the few the gradient happens to be largest in. It applies to 2-D hidden matrices only.",
    )


# --------------------------------------------------------------------------
# 19. Prefill/decode disaggregation
# --------------------------------------------------------------------------


def fig_pd_disaggregation() -> None:
    """Colocating prefill and decode makes every decode step wait behind a prompt."""
    fig, axes = plt.subplots(2, 1, figsize=(11.8, 4.9), sharex=True)

    prefill_ms, decode_ms = 120.0, 12.0
    # One long prompt arrives at t=140 while three users are already decoding.
    colocated_rows = [
        ("GPU 0", [(0, decode_ms, "d"), (14, decode_ms, "d"), (28, decode_ms, "d"), (42, decode_ms, "d"),
                   (56, decode_ms, "d"), (70, decode_ms, "d"), (84, decode_ms, "d"), (98, decode_ms, "d"),
                   (112, decode_ms, "d"), (126, decode_ms, "d"),
                   (140, prefill_ms, "p"),
                   (262, decode_ms, "d"), (276, decode_ms, "d"), (290, decode_ms, "d"), (304, decode_ms, "d")]),
    ]
    disagg_rows = [
        ("Prefill pool", [(140, prefill_ms, "p")]),
        ("Decode pool", [(t, decode_ms, "d") for t in range(0, 320, 14)]),
    ]

    def draw(ax, rows, title):
        for y, (label, spans) in enumerate(rows):
            for start, width, kind in spans:
                ax.barh(
                    y,
                    width,
                    left=start,
                    height=0.52,
                    color=ORANGE if kind == "p" else BLUE,
                    edgecolor=BG,
                    linewidth=0.6,
                )
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels([r[0] for r in rows], fontsize=9.5)
        ax.set_ylim(-0.6, len(rows) + 0.25)  # headroom below the last row for the legend
        ax.invert_yaxis()
        ax.set_title(title, fontsize=10.5, loc="left")
        ax.grid(axis="y", visible=False)

    draw(axes[0], colocated_rows, "Colocated: one 120 ms prefill stalls every user mid-generation")
    axes[0].annotate(
        "132 ms with no token\nfor anyone decoding",
        xy=(200, 0.32),
        xytext=(200, 0.95),
        ha="center",
        fontsize=9,
        color=RED,
        arrowprops=dict(arrowstyle="->", color=RED, lw=1.1),
    )
    draw(axes[1], disagg_rows, "Disaggregated: prefill runs on its own pool, decode keeps its cadence")
    axes[1].set_xlabel("time (ms)")

    handles = [
        mpatches.Patch(color=ORANGE, label="prefill (compute-bound, one big matmul over the prompt)"),
        mpatches.Patch(color=BLUE, label="decode step (memory-bound, one token per user)"),
    ]
    axes[1].legend(handles=handles, frameon=False, fontsize=9, loc="lower left", ncol=2)

    _finish(
        fig,
        "prefill-decode-disaggregation.svg",
        "Prefill and decode want opposite things from a GPU: prefill saturates the tensor cores on one long prompt, decode is\n"
        "bandwidth-bound and needs to run every 12 ms or users watch generation stutter. Sharing one pool means each arriving prompt\n"
        "blocks every in-flight generation for its whole duration, which is why inter-token latency, not throughput, is the metric\n"
        "that degrades. Splitting the pools and shipping the KV cache across the interconnect (Mooncake, and now vLLM and SGLang)\n"
        "lets each half be scheduled and scaled for its own bottleneck.",
    )


# --------------------------------------------------------------------------
# 20. GRPO's advantage normalization
# --------------------------------------------------------------------------


def fig_grpo_advantage() -> None:
    """Dividing by the group std hands the biggest gradients to the least useful prompts."""
    group = 8
    successes = np.arange(1, group)  # 0 and 8 give a zero-variance group and no signal at all
    p = successes / group
    std = np.sqrt(p * (1 - p))

    adv_norm = (1 - p) / std        # advantage on a correct response, std-normalized
    adv_plain = 1 - p               # advantage on a correct response, mean-only (Dr. GRPO)

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.3))

    axes[0].plot(successes, adv_norm, "o-", color=RED, label=r"GRPO: $(r - \mu)/\sigma$")
    axes[0].plot(successes, adv_plain, "o-", color=GREEN, label=r"mean-only: $r - \mu$")
    axes[0].set_xlabel(f"correct responses out of {group}")
    axes[0].set_ylabel("advantage on a correct response")
    axes[0].set_title("Std division inflates near-solved and near-hopeless prompts")
    axes[0].legend(frameon=False, fontsize=9)

    weight = adv_norm / adv_plain  # = 1/std
    axes[1].bar(successes, weight, color=[GREEN if 2 <= s <= 6 else RED for s in successes], width=0.62)
    axes[1].set_xlabel(f"correct responses out of {group}")
    axes[1].set_ylabel("gradient weight relative to mean-only")
    axes[1].set_title(f"The 1/8 and 7/8 prompts pull {weight.max():.1f}x harder")
    axes[1].grid(axis="x", visible=False)
    for s, w in zip(successes, weight):
        axes[1].text(s, w * 1.02, f"{w:.2f}x", ha="center", fontsize=8.5, color=MUTED)
    axes[1].set_ylim(top=weight.max() * 1.18)

    _finish(
        fig,
        "grpo-advantage.svg",
        "Binary rewards, group of 8. GRPO divides the group-centred reward by the group standard deviation, and for a Bernoulli group\n"
        "that standard deviation is smallest exactly where the prompt is nearly always solved or nearly never solved -- the prompts\n"
        "with the least left to teach. The division therefore scales their gradients up by 1/sigma while a prompt at the 50% frontier,\n"
        "the informative one, gets the smallest weight. Dr. GRPO's fix is to drop the division and centre only. A group that is all\n"
        "right or all wrong has zero variance and contributes nothing either way.",
    )


# --------------------------------------------------------------------------
# 21. MoE anatomy: total vs active, and what routing collapse costs
# --------------------------------------------------------------------------


def fig_moe() -> None:
    models = [
        ("Mixtral 8x7B", 46.7, 12.9),
        ("GPT-OSS-120B", 117.0, 5.1),
        ("Qwen3-235B-A22B", 235.0, 22.0),
        ("DeepSeek-V3", 671.0, 37.0),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.5))

    names = [m[0] for m in models]
    total = np.array([m[1] for m in models])
    active = np.array([m[2] for m in models])
    y = np.arange(len(models))
    axes[0].barh(y, total, height=0.6, color=GRID, edgecolor=MUTED, linewidth=0.8, label="total parameters (memory)")
    axes[0].barh(y, active, height=0.6, color=VIOLET, label="active per token (compute)")
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(names, fontsize=9.5)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("billions of parameters")
    axes[0].set_title("You store the whole model and pay for a slice")
    axes[0].legend(frameon=False, fontsize=9, loc="center right")
    axes[0].grid(axis="y", visible=False)
    for yi, (t, a) in enumerate(zip(total, active)):
        axes[0].text(t + 12, yi, f"{t / a:.0f}x sparsity", va="center", fontsize=8.5, color=MUTED)
    axes[0].set_xlim(right=total.max() * 1.32)

    n_exp, top_k, tokens = 64, 8, 40000
    rng = np.random.default_rng(11)
    balanced = rng.multinomial(tokens * top_k, np.full(n_exp, 1 / n_exp)) / (tokens * top_k / n_exp)
    skew = np.exp(-np.arange(n_exp) / 9.0)
    collapsed = rng.multinomial(tokens * top_k, skew / skew.sum()) / (tokens * top_k / n_exp)

    order_c = np.sort(collapsed)[::-1]
    order_b = np.sort(balanced)[::-1]
    axes[1].plot(order_b, color=GREEN, lw=2, label="balanced routing")
    axes[1].plot(order_c, color=RED, lw=2, label="collapsed routing")
    axes[1].axhline(1.0, color=MUTED, ls="--", lw=1)
    axes[1].text(n_exp * 0.62, 1.12, "perfectly even load", fontsize=8.5, color=MUTED)
    axes[1].set_xlabel("experts, sorted by load")
    axes[1].set_ylabel("tokens routed / even share")
    axes[1].set_title(f"A step costs what the busiest expert costs (top-{top_k} of {n_exp})")
    axes[1].legend(frameon=False, fontsize=9)
    axes[1].annotate(
        f"slowest expert does {order_c[0]:.1f}x its share:\nevery other GPU waits for it",
        xy=(0, order_c[0]),
        xytext=(n_exp * 0.30, order_c[0] * 0.80),
        fontsize=8.5,
        color=RED,
        arrowprops=dict(arrowstyle="->", color=RED, lw=1),
    )

    _finish(
        fig,
        "moe-anatomy.svg",
        "Left: published total and active parameter counts. Sparsity is the whole point -- DeepSeek-V3 holds 671B parameters but spends\n"
        "37B of arithmetic per token -- and it is also the whole problem, because memory and interconnect are sized by the number you\n"
        "are not computing with. Right: simulated expert load over 40k tokens for balanced routing versus a collapsed router. Under\n"
        "expert parallelism each expert lives on its own device, so a step finishes when the busiest one does; this is what the\n"
        "auxiliary balance loss, and DeepSeek-V3's aux-loss-free bias adjustment, exist to prevent.",
    )


# --------------------------------------------------------------------------
# 22. Test-time compute
# --------------------------------------------------------------------------


def fig_test_time_compute() -> None:
    """Two ways to spend more compute at inference, and where each one stops paying."""
    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.3))

    k = np.array([1, 2, 4, 8, 16, 32, 64, 128, 256])
    for p, colour, label in ((0.30, BLUE, "per-sample accuracy 30%"), (0.55, VIOLET, "55%"), (0.75, GREEN, "75%")):
        axes[0].plot(k, (1 - (1 - p) ** k) * 100, "o-", color=colour, label=f"pass@k, {label}")
        # Majority voting cannot exceed the chance the modal answer is right.
        axes[0].plot(k, np.full_like(k, p / (p + (1 - p) / 3) * 100, dtype=float), ls="--", lw=1.2, color=colour)
    axes[0].set_xscale("log", base=2)
    axes[0].set_xlabel("samples drawn (k)")
    axes[0].set_ylabel("accuracy (%)")
    axes[0].set_title("Sampling: pass@k soars, votable accuracy plateaus")
    axes[0].legend(frameon=False, fontsize=8.5, loc="lower right")
    axes[0].text(1.15, 92, "dashed: majority-vote ceiling", fontsize=8.5, color=MUTED)

    tokens = np.logspace(np.log10(256), np.log10(65536), 40)
    for ceiling, colour, label in ((0.92, GREEN, "problem within reach"), (0.55, AMBER, "problem at the edge"), (0.12, RED, "problem out of reach")):
        acc = ceiling * (1 - np.exp(-np.log(tokens / 200) / 1.6)).clip(0, 1)
        axes[1].plot(tokens, acc * 100, color=colour, lw=2, label=label)
    axes[1].set_xscale("log")
    axes[1].set_xlabel("reasoning tokens spent per problem")
    axes[1].set_ylabel("accuracy (%)")
    axes[1].set_title("Thinking longer: log-linear, then flat")
    axes[1].legend(frameon=False, fontsize=9)

    _finish(
        fig,
        "test-time-compute.svg",
        "Both panels are closed-form models, not measured results -- they show the shapes to reason with, not numbers to quote. Left:\n"
        "pass@k assumes independent samples, so it rises fast, but you only get to keep it if a verifier can tell you which sample was\n"
        "right. With majority voting instead of a verifier you are capped by how often the modal answer is correct, which is why\n"
        "verifiable domains behave so differently from open-ended ones. Right: accuracy against thinking tokens is roughly linear in\n"
        "log compute until it saturates at whatever that problem's ceiling is -- more thinking never rescues a problem the model\n"
        "cannot do, and wastes tokens on ones it already could.",
    )


# --------------------------------------------------------------------------
# 23. Sparse attention: what "linear-ish" attention actually buys
# --------------------------------------------------------------------------


def fig_sparse_attention() -> None:
    """Block-sparse selection keeps the quadratic term from dominating."""
    n, block = 64, 8
    idx = np.arange(n)
    causal = (idx[:, None] >= idx[None, :]).astype(float)

    rng = np.random.default_rng(5)
    n_blocks = n // block
    selected = np.zeros((n, n))
    for qb in range(n_blocks):
        allowed = np.arange(qb + 1)
        keep = allowed if allowed.size <= 3 else np.concatenate([[0], rng.choice(allowed[1:-1], 1), [qb]])
        for kb in keep:
            selected[qb * block : (qb + 1) * block, kb * block : (kb + 1) * block] = 1.0
    selected *= causal

    fig, axes = plt.subplots(1, 3, figsize=(12.2, 4.1), gridspec_kw={"width_ratios": [1, 1, 1.7]})

    for ax, (mat, title) in zip(
        axes,
        ((causal, "Dense causal\nevery query sees every past key"), (selected, "Block-sparse selection\ntop blocks + the local block")),
    ):
        ax.imshow(mat, cmap="Blues", vmin=0, vmax=1.35, interpolation="nearest", aspect="auto")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("key position", fontsize=9)
        ax.set_xticks([0, n - 1])
        ax.set_yticks([0, n - 1])
        ax.grid(False)
    axes[0].set_ylabel("query position", fontsize=9)

    ax = axes[2]
    d_model, layers = 4096, 32
    contexts = np.logspace(np.log10(1024), np.log10(1_048_576), 40)
    dense_share = contexts / (12 * d_model)
    # Selection keeps a fixed budget of blocks per query, so the attention term
    # stops growing with context and the model reverts to its linear 6ND cost.
    budget = 8192.0
    sparse_share = np.minimum(contexts, budget) / (12 * d_model)
    ax.plot(contexts, dense_share * 100, color=RED, lw=2, label="dense causal attention")
    ax.plot(contexts, sparse_share * 100, color=GREEN, lw=2, label=f"selection, {int(budget)}-token budget")
    ax.axhline(50, color=MUTED, ls="--", lw=1.2)
    ax.text(1300, 54, "attention is half the model's FLOPs", fontsize=8.5, color=MUTED)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("context length (tokens)")
    ax.set_ylabel("attention FLOPs as % of the 6ND term")
    ax.set_title("Where attention stops being a rounding error", fontsize=10)
    ax.legend(frameon=False, fontsize=9, loc="upper left")

    _finish(
        fig,
        "sparse-attention.svg",
        "Left two: dense causal attention against a block-sparse pattern that keeps a small budget of key blocks per query, always\n"
        "including the local one. Right: for a 32-layer model at d_model 4096, the attention term is S/(12d) of the 6ND estimate -- 8%\n"
        "at 4k, half the 6ND term at 6d = 24.6k tokens, and dominant beyond -- which is why long context, not parameter count, is what\n"
        "forces the issue. Capping each query's key budget flattens that curve: the same argument behind NSA and MoBA, and the reason a\n"
        "trained-in sparse pattern beats bolting sparsity onto a dense checkpoint at inference time.",
    )


# --------------------------------------------------------------------------
# 24. Why long-horizon agents fail: reliability compounds
# --------------------------------------------------------------------------


def fig_agent_horizon() -> None:
    """A 99%-reliable step is a coin flip by step 70."""
    steps = np.arange(1, 201)

    fig, axes = plt.subplots(1, 2, figsize=(11.8, 4.3))

    for rel, colour in ((0.90, RED), (0.95, ORANGE), (0.99, BLUE), (0.999, GREEN)):
        axes[0].plot(steps, rel**steps * 100, color=colour, lw=2, label=f"{rel:.1%} per step")
    axes[0].axhline(50, color=MUTED, ls="--", lw=1.2)
    axes[0].text(112, 54, "coin flip", fontsize=8.5, color=MUTED)
    axes[0].set_xlabel("steps in the task")
    axes[0].set_ylabel("end-to-end success (%)")
    axes[0].set_title("Independent steps multiply")
    axes[0].legend(frameon=False, fontsize=9)

    horizons = np.array([5, 10, 25, 50, 100, 250, 500, 1000])
    for target, colour in ((0.5, BLUE), (0.9, VIOLET), (0.99, RED)):
        required = target ** (1 / horizons)
        axes[1].plot(horizons, (1 - required) * 100, "o-", color=colour, lw=2, label=f"{target:.0%} end-to-end")
    axes[1].set_xscale("log")
    axes[1].set_yscale("log")
    axes[1].set_xlabel("task horizon (steps)")
    axes[1].set_ylabel("per-step error budget (%)")
    axes[1].set_title("What a longer task demands of each step")
    axes[1].legend(frameon=False, fontsize=9)

    _finish(
        fig,
        "agent-horizon.svg",
        "The arithmetic that makes long-horizon agents hard, assuming steps fail independently. A 99%-reliable step -- which sounds\n"
        "excellent -- is a coin flip by step 70 and near-hopeless by step 200. Right: to finish a 100-step task nine times out of ten,\n"
        "every step needs an error budget near 0.1%. This is why the useful work is recovery rather than accuracy: checkpointing,\n"
        "verification, and retry break the chain into segments so a single bad step costs one segment instead of the run. Real steps\n"
        "are not independent -- errors correlate, and a model that recovers turns some failures into successes -- so treat these as\n"
        "the pessimistic bound that motivates the engineering, not a prediction.",
    )

FIGURES = [
    fig_softmax_scaling,
    fig_causal_mask,
    fig_rope,
    fig_param_breakdown,
    fig_kv_cache,
    fig_training_memory,
    fig_lr_schedules,
    fig_scaling_laws,
    fig_arithmetic_intensity,
    fig_sampling,
    fig_precision_formats,
    fig_speculative,
    fig_posttraining_map,
    fig_tokenizer_tradeoff,
    fig_kv_cache_schemes,
    fig_attention_patterns,
    fig_fp8_scaling,
    fig_muon,
    fig_pd_disaggregation,
    fig_grpo_advantage,
    fig_moe,
    fig_test_time_compute,
    fig_sparse_attention,
    fig_agent_horizon,
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for figure in FIGURES:
        figure()


if __name__ == "__main__":
    main()
