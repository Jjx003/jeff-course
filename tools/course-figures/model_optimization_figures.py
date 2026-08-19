#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.9", "numpy>=1.26"]
# ///
"""Generate the computed figures for the Model Optimization Systems course.

Run with:

    uv run tools/course-figures/model_optimization_figures.py

Figures are written as SVG into `static/courses/model-optimization-systems/`.
Only the data-driven plots live here. Conceptual diagrams in the same directory
(the roofline, the FlashAttention tiling picture, the LoRA merge diagram, the
INT4/NF4 level chart, the protein cost profile) are hand-authored SVG and are
not touched by this script.

Every number plotted below is either computed from a closed-form model stated in
the corresponding course module, or simulated with a fixed seed so the figure and
the module text cannot drift apart.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

OUT = Path(__file__).resolve().parents[2] / "static" / "courses" / "model-optimization-systems"

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
    """Lay the axes out above a reserved caption band, then write the SVG.

    The band is sized from the caption's own line count, so a longer caption
    pushes the plot up instead of landing on top of the x-axis label.
    """
    lines = caption.count("\n") + 1
    band = 0.05 + 0.045 * lines
    fig.tight_layout(rect=(0.0, band, 1.0, 1.0))
    fig.text(0.012, 0.012, caption, fontsize=9.5, color=MUTED, va="bottom", linespacing=1.5)
    path = OUT / name
    fig.savefig(path, format="svg")
    # Set FIG_PREVIEW_DIR to also drop PNGs somewhere scratch; handy when
    # iterating on layout, since SVG text overlap is easier to spot rasterized.
    preview = os.environ.get("FIG_PREVIEW_DIR")
    if preview:
        fig.savefig(Path(preview) / name.replace(".svg", ".png"), dpi=110)
    plt.close(fig)
    print(f"wrote {path.relative_to(OUT.parents[2])}")


# --------------------------------------------------------------------------
# 1. Groupwise INT4 error against group size, clean weights vs outlier channels
# --------------------------------------------------------------------------


def quantize_groupwise_int4(w: np.ndarray, group: int) -> np.ndarray:
    """Symmetric absmax INT4 (codes -7..7) with one scale per contiguous group."""
    flat = w.reshape(-1, group)
    scale = np.abs(flat).max(axis=1, keepdims=True) / 7.0
    scale = np.where(scale == 0, 1.0, scale)
    codes = np.clip(np.rint(flat / scale), -7, 7)
    return (codes * scale).reshape(w.shape)


def fig_group_size_error() -> None:
    rng = np.random.default_rng(0)
    d_in, d_out = 4096, 4096
    groups = np.array([16, 32, 64, 128, 256, 512, 1024])

    clean = rng.standard_normal((d_out, d_in)).astype(np.float64)

    # 0.5% of input channels carry ~20x larger weights, the pattern PTQ methods
    # such as AWQ and SmoothQuant are built around.
    outlier = clean.copy()
    n_out = max(1, int(0.005 * d_in))
    cols = rng.choice(d_in, size=n_out, replace=False)
    outlier[:, cols] *= 20.0

    def sweep(w: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        denom = np.mean(w**2)
        mse = np.array([np.mean((w - quantize_groupwise_int4(w, g)) ** 2) for g in groups])
        bits = 4.0 + 16.0 / groups
        return mse / denom, bits

    clean_nmse, bits = sweep(clean)
    out_nmse, _ = sweep(outlier)

    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(12.2, 5.0), gridspec_kw={"width_ratios": [1.45, 1.0]}
    )

    ax.plot(groups, clean_nmse, "o-", color=BLUE, lw=2.6, ms=7, label="Gaussian weights")
    ax.plot(groups, out_nmse, "o-", color=RED, lw=2.6, ms=7, label="0.5% outlier channels (20x)")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xticks(groups)
    ax.set_xticklabels([str(g) for g in groups])
    ax.set_xlabel("group size G (weights per scale)")
    ax.set_ylabel("normalized MSE:  E[(w − ŵ)²] / E[w²]")
    ax.set_title("Quantization error grows with group size", fontsize=13, fontweight="bold", pad=12)
    ax.legend(frameon=False, loc="upper left")

    ratio = out_nmse[list(groups).index(128)] / clean_nmse[list(groups).index(128)]
    ax.annotate(
        f"at G = 128 the outlier tensor is\n{ratio:.0f}x worse than the clean one",
        xy=(128, out_nmse[list(groups).index(128)]),
        xytext=(150, out_nmse[0] * 0.55),
        fontsize=10,
        color=RED,
        arrowprops=dict(arrowstyle="->", color=RED, lw=1.4),
    )

    ax2.plot(groups, bits, "o-", color=GREEN, lw=2.6, ms=7)
    ax2.set_xscale("log", base=2)
    ax2.set_xticks(groups)
    ax2.set_xticklabels([str(g) for g in groups])
    ax2.set_ylim(4.0, 5.1)
    ax2.set_xlabel("group size G")
    ax2.set_ylabel("effective bits per weight")
    ax2.set_title("...and so does the storage you save", fontsize=13, fontweight="bold", pad=12)
    for g, b in zip(groups, bits):
        if g in (32, 128, 1024):
            ax2.annotate(
                f"{b:.3f}",
                xy=(g, b),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                fontsize=10,
                color=INK,
            )
    ax2.text(
        150,
        4.86,
        "4 + 16/G bits\n(one FP16 scale per group)",
        fontsize=10,
        color=MUTED,
        ha="center",
    )

    _finish(
        fig,
        "quant-group-size-error.svg",
        "Simulated on a 4096 x 4096 weight matrix, symmetric absmax INT4 with codes -7..7, seed 0.\n"
        "The clean curve is nearly flat: for well-behaved weights, group size buys almost nothing.\n"
        "The outlier curve is where the whole design question lives.",
    )


# --------------------------------------------------------------------------
# 2. KV cache versus weights as context and concurrency grow
# --------------------------------------------------------------------------


def fig_kv_vs_weights() -> None:
    # Llama-3-70B shape: 80 layers, 8 KV heads, head dim 128, GQA.
    layers, kv_heads, head_dim = 80, 8, 128
    kv_bytes_per_token = 2 * layers * kv_heads * head_dim * 2  # K and V, BF16
    params = 70e9

    ctx = np.logspace(np.log2(512), np.log2(131072), 200, base=2)
    fig, ax = plt.subplots(figsize=(11.4, 5.6))

    for batch, color in [(1, BLUE), (8, GREEN), (32, AMBER), (128, RED)]:
        gb = batch * ctx * kv_bytes_per_token / 1e9
        ax.plot(ctx, gb, lw=2.8, color=color, label=f"KV cache, batch {batch}")

    ax.axhline(params * 2 / 1e9, color=INK, ls="--", lw=2)
    ax.axhline(params * 0.5 / 1e9, color=VIOLET, ls="--", lw=2)
    ax.axhspan(80, 640, color="#e0f2fe", zorder=0)

    ax.text(560, params * 2 / 1e9 * 1.14, "BF16 weights, 140 GB", fontsize=10, color=INK)
    ax.text(560, params * 0.5 / 1e9 * 1.14, "INT4 weights, 35 GB", fontsize=10, color=VIOLET)
    ax.text(
        120000,
        230,
        "one H100 (80 GB) up to an 8-GPU node (640 GB)",
        fontsize=10,
        color="#0369a1",
        ha="right",
        bbox=dict(facecolor=BG, edgecolor="none", alpha=0.85, pad=2),
    )

    # Crossover: batch 32 KV cache equals the INT4 weight footprint.
    t_cross = params * 0.5 / (32 * kv_bytes_per_token)
    ax.plot([t_cross], [params * 0.5 / 1e9], "o", color=AMBER, ms=10, zorder=5)
    ax.annotate(
        f"at batch 32 and {t_cross/1000:.1f}K tokens the KV cache\n"
        "already outweighs the INT4 model itself",
        xy=(t_cross, params * 0.5 / 1e9),
        xytext=(3000, 1.35),
        fontsize=10,
        color=AMBER,
        bbox=dict(facecolor=BG, edgecolor="none", alpha=0.9, pad=3),
        arrowprops=dict(arrowstyle="->", color=AMBER, lw=1.4),
    )

    ax.set_xscale("log", base=2)
    ax.set_yscale("log")
    ax.set_xlim(512, 131072)
    ax.set_ylim(0.2, 4000)
    ax.set_xticks([512, 2048, 8192, 32768, 131072])
    ax.set_xticklabels(["512", "2K", "8K", "32K", "128K"])
    ax.set_xlabel("context length per request (tokens)")
    ax.set_ylabel("GPU memory (GB)")
    ax.set_title(
        "For long context, the cache is the model", fontsize=14, fontweight="bold", pad=12
    )
    ax.legend(frameon=False, loc="upper left", ncols=2)

    _finish(
        fig,
        "kv-cache-vs-weights.svg",
        "Llama-3-70B shape: 80 layers, 8 KV heads (GQA), head dim 128, BF16 cache -> 320 KB per token per request.\n"
        "Weight memory is fixed; cache memory is the product of batch and context, which is why admission control,\n"
        "not weight quantization, is usually the binding constraint at long context.",
    )


# --------------------------------------------------------------------------
# 3. Speculative decoding: expected speedup has an interior optimum in k
# --------------------------------------------------------------------------


def fig_specdec_optimal_k() -> None:
    k = np.arange(1, 21)
    fig, (ax, ax2) = plt.subplots(
        1, 2, figsize=(12.4, 5.2), gridspec_kw={"width_ratios": [1.15, 1.0]}
    )

    def speedup(k, a, cd):
        committed = (1 - a ** (k + 1)) / (1 - a)
        return committed / (1 + k * cd)

    cd = 0.08
    # Labelled at the right end of each curve rather than in a legend box, which
    # would sit on top of the low-acceptance curves.
    for a, color in [(0.5, BLUE), (0.6, GREEN), (0.7, AMBER), (0.8, ORANGE), (0.9, RED)]:
        s = speedup(k, a, cd)
        ax.plot(k, s, lw=2.6, color=color)
        best = int(k[np.argmax(s)])
        ax.plot([best], [s.max()], "o", color=color, ms=9, zorder=5)
        ax.annotate(
            f"a = {a}",
            xy=(k[-1], s[-1]),
            xytext=(6, 0),
            textcoords="offset points",
            va="center",
            fontsize=10,
            color=color,
        )

    ax.axhline(1.0, color=MUTED, ls=":", lw=1.6)
    ax.text(1.2, 1.04, "break-even", fontsize=10, color=MUTED, va="bottom")
    ax.set_xticks([1, 4, 8, 12, 16, 20])
    ax.set_xlim(0.5, 23.5)
    ax.set_ylim(0.6, None)
    ax.set_xlabel("draft length k")
    ax.set_ylabel("expected speedup over plain decode")
    ax.set_title(
        f"Optimal draft length, draft cost {cd} target-steps per token",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )

    # How the optimum moves with draft cost.
    alphas = np.linspace(0.30, 0.95, 140)
    for cd2, color in [(0.02, GREEN), (0.08, AMBER), (0.20, RED)]:
        best_k = [int(np.argmax([speedup(kk, a, cd2) for kk in k]) + 1) for a in alphas]
        ax2.plot(alphas, best_k, lw=2.8, color=color, label=f"draft cost {cd2}")
    ax2.set_xlabel("acceptance rate a")
    ax2.set_ylabel("k that maximizes speedup")
    ax2.set_ylim(0, 21)
    ax2.set_title("A cheaper draft earns a longer draft", fontsize=13, fontweight="bold", pad=12)
    ax2.legend(frameon=False, loc="upper left", fontsize=10)

    _finish(
        fig,
        "specdec-optimal-k.svg",
        "Speedup = [(1 - a^(k+1)) / (1 - a)] / (1 + k*c_d), the closed form derived in module 13.\n"
        "Dots mark the maximizing k. The curve is flat near its peak, which is why serving stacks tune k\n"
        "adaptively from the recent acceptance rate rather than searching for an exact optimum.",
    )


# --------------------------------------------------------------------------
# 4. Tensor-parallel decode scaling: the collective term flattens the curve
# --------------------------------------------------------------------------


def fig_tp_decode_scaling() -> None:
    # 70B BF16 on H100 SXM: 140 GB over 3.35 TB/s per GPU; 80 layers,
    # 2 all-reduces per layer at a fixed 10 us effective latency (batch-1
    # payloads are ~16 KB, so the bandwidth term is nanoseconds).
    mem_ms_tp1 = 140e9 / 3.35e12 * 1e3
    comm_ms = 80 * 2 * 10e-6 * 1e3

    p = np.array([1, 2, 4, 8])
    ideal = mem_ms_tp1 / p
    real = ideal + np.where(p > 1, comm_ms, 0.0)

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.0, 5.0))

    ax.plot(p, ideal, "o--", color=MUTED, lw=2.2, ms=7, label="memory floor alone (41.79/p)")
    ax.plot(p, real, "o-", color=BLUE, lw=2.8, ms=8, label="with 160 all-reduces @ 10 us")
    ax.axhline(comm_ms, color=RED, ls=":", lw=1.8)
    ax.text(1.05, comm_ms * 1.12, "collective term: 1.6 ms, independent of p", fontsize=10, color=RED)
    ax.set_xscale("log", base=2)
    ax.set_xticks(p)
    ax.set_xticklabels([str(v) for v in p])
    ax.set_xlabel("tensor-parallel degree p")
    ax.set_ylabel("decode step floor (ms)")
    ax.set_title("The term parallelism cannot shrink", fontsize=13, fontweight="bold", pad=12)
    ax.legend(frameon=False, loc="upper right", fontsize=10)

    speedup = real[0] / real
    ax2.plot(p, p, "--", color=MUTED, lw=2.0, label="ideal (p)")
    ax2.plot(p, speedup, "o-", color=GREEN, lw=2.8, ms=8, label="achieved")
    for pv, sv in zip(p[1:], speedup[1:]):
        ax2.annotate(
            f"{sv:.2f}x",
            xy=(pv, sv),
            xytext=(0, -16),
            textcoords="offset points",
            ha="center",
            fontsize=10,
            color=GREEN,
        )
    ax2.set_xscale("log", base=2)
    ax2.set_xticks(p)
    ax2.set_xticklabels([str(v) for v in p])
    ax2.set_xlabel("tensor-parallel degree p")
    ax2.set_ylabel("effective speedup over TP 1")
    ax2.set_title("Efficiency falls as p rises: 93%, 87%, 77%", fontsize=13, fontweight="bold", pad=12)
    ax2.legend(frameon=False, loc="upper left", fontsize=10)

    _finish(
        fig,
        "dist-tp-decode-scaling.svg",
        "Step floor = 140 GB / (p x 3.35 TB/s) + 160 x 10 us for p > 1; batch-1 decode of a 70B BF16 model.\n"
        "The 10 us is a representative small-message NVLink all-reduce latency; the 16 KB payload's wire time\n"
        "is nanoseconds. TP 1 is a bookkeeping baseline - 140 GB does not fit on one 80 GB GPU.",
    )


# --------------------------------------------------------------------------
# 5. MoE decode intensity: batching buys E/k times less reuse
# --------------------------------------------------------------------------


def fig_moe_decode_intensity() -> None:
    B = np.unique(np.round(np.logspace(0, 4.3, 220)).astype(int)).astype(float)
    ridge = 295.0
    b_bytes = 2.0  # BF16

    def m_touched(batch, experts, k):
        return experts * (1.0 - (1.0 - k / experts) ** batch)

    configs = [
        ("Mixtral-shaped: E=8, k=2", 8, 2, ORANGE),
        ("DeepSeek-shaped: E=256, k=8", 256, 8, VIOLET),
    ]

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.4, 5.2))

    for label, E, k, color in configs:
        ax.plot(B, m_touched(B, E, k), lw=2.8, color=color, label=label)
        ax.axhline(E, color=color, ls=":", lw=1.2)
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("decode batch size B (tokens this step)")
    ax.set_ylabel("expected distinct experts touched, m(B)")
    ax.set_title("The union of routed experts saturates fast", fontsize=13, fontweight="bold", pad=12)
    ax.legend(frameon=False, loc="lower right", fontsize=10)

    ax2.plot(B, 2 * B / b_bytes, lw=2.4, color=BLUE, label="dense: I = B")
    crossings = []
    for label, E, k, color in configs:
        intensity = 2 * B * k / (m_touched(B, E, k) * b_bytes)
        ax2.plot(B, intensity, lw=2.8, color=color, label=label)
        # Interpolate the ridge crossing in log-log space (the grid is coarse).
        cross = float(np.exp(np.interp(np.log(ridge), np.log(intensity), np.log(B))))
        crossings.append((label, cross, color))
    ax2.axhline(ridge, color=INK, ls="--", lw=1.8)
    ax2.text(1.3, ridge * 1.25, "H100 ridge point, 295 FLOP/byte", fontsize=10, color=INK)
    for label, cross, color in crossings:
        ax2.plot([cross], [ridge], "o", color=color, ms=9, zorder=5)
        ax2.annotate(
            f"B = {cross:,.0f}",
            xy=(cross, ridge),
            xytext=(0, -22),
            textcoords="offset points",
            ha="center",
            fontsize=10,
            color=color,
        )
    ax2.plot([ridge], [ridge], "o", color=BLUE, ms=9, zorder=5)
    ax2.annotate("B = 295", xy=(ridge, ridge), xytext=(0, 10), textcoords="offset points",
                 ha="center", fontsize=10, color=BLUE)
    ax2.set_xscale("log")
    ax2.set_yscale("log")
    ax2.set_xlabel("decode batch size B")
    ax2.set_ylabel("expert-weight arithmetic intensity (FLOP/byte)")
    ax2.set_title("Each unit of batch buys E/k times less reuse", fontsize=13, fontweight="bold", pad=12)
    ax2.legend(frameon=False, loc="upper left", fontsize=10)

    _finish(
        fig,
        "moe-decode-intensity.svg",
        "m(B) = E(1 - (1 - k/E)^B) under uniform independent routing; I = 2Bk / (m(B) b) for BF16 expert weights,\n"
        "counting expert FLOPs and expert bytes only (attention and shared weights stay dense). Ridge crossings:\n"
        "dense at B = 295, Mixtral-shaped at B = 1,180, DeepSeek-shaped at B = 9,440 - the E/k dilution.",
    )


# --------------------------------------------------------------------------
# 6. Serving latency vs load, and coordinated omission (module 17's queue)
# --------------------------------------------------------------------------


def _fcfs_waits(gaps: np.ndarray, services: np.ndarray) -> np.ndarray:
    waits = np.empty_like(gaps)
    now = 0.0
    free = 0.0
    for i in range(len(gaps)):
        now += gaps[i]
        start = now if now > free else free
        waits[i] = start - now
        free = start + services[i]
    return waits


def fig_latency_vs_load() -> None:
    rng = np.random.default_rng(17)
    prefill, itl = 40.0, 5.0
    n_req, warm = 100_000, 10_000
    mean_service = prefill + itl * (16 + 256) / 2.0

    rhos = np.array([0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95])
    p50s, p99s, means, pk = [], [], [], []
    for rho in rhos:
        lam = rho / mean_service
        gaps = rng.exponential(1.0 / lam, n_req)
        services = prefill + itl * rng.integers(16, 257, n_req)
        waits = _fcfs_waits(gaps, services)[warm:]
        ttft = waits + prefill
        p50s.append(np.percentile(ttft, 50))
        p99s.append(np.percentile(ttft, 99))
        means.append(ttft.mean())
        es2 = (services**2).mean()
        pk.append(lam * es2 / (2 * (1 - rho)) + prefill)

    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(12.2, 5.2), gridspec_kw={"width_ratios": [1.35, 1.0]})

    ax.plot(rhos, np.array(p99s) / 1e3, "o-", color=RED, lw=2.8, ms=7, label="TTFT p99")
    ax.plot(rhos, np.array(p50s) / 1e3, "o-", color=BLUE, lw=2.8, ms=7, label="TTFT p50")
    ax.plot(rhos, np.array(means) / 1e3, "o-", color=GREEN, lw=2.0, ms=5, label="TTFT mean (measured)")
    ax.plot(rhos, np.array(pk) / 1e3, "--", color=INK, lw=1.8, label="mean (Pollaczek-Khinchine)")
    ax.set_yscale("log")
    ax.set_xlabel("utilization rho")
    ax.set_ylabel("TTFT (seconds)")
    ax.set_title("The hockey stick: capacity is a cliff, not a point", fontsize=13, fontweight="bold", pad=12)
    ax.legend(frameon=False, loc="upper left", fontsize=10)

    # Coordinated omission at rho = 0.98: open loop vs 16 closed-loop clients.
    rho = 0.98
    lam = rho / mean_service
    n_co = 20_000
    gaps = rng.exponential(1.0 / lam, n_co)
    services = prefill + itl * rng.integers(16, 257, n_co)
    open_ttft = _fcfs_waits(gaps, services)[2000:] + prefill

    n_clients = 16
    think = n_clients / lam - mean_service
    import heapq

    pend = [(rng.exponential(think), c) for c in range(n_clients)]
    heapq.heapify(pend)
    free = 0.0
    closed = []
    for _ in range(n_co):
        arr, c = heapq.heappop(pend)
        start = arr if arr > free else free
        svc = prefill + itl * float(rng.integers(16, 257))
        free = start + svc
        closed.append(start - arr)
        heapq.heappush(pend, (free + rng.exponential(think), c))
    closed_ttft = np.array(closed[2000:]) + prefill

    labels = ["p50", "p90", "p99"]
    qs = [50, 90, 99]
    xpos = np.arange(len(qs))
    open_vals = [np.percentile(open_ttft, q) / 1e3 for q in qs]
    closed_vals = [np.percentile(closed_ttft, q) / 1e3 for q in qs]
    width = 0.36
    ax2.bar(xpos - width / 2, open_vals, width, color=RED, label="open loop (honest)")
    ax2.bar(xpos + width / 2, closed_vals, width, color=BLUE, label="closed loop, 16 clients")
    for x, ov, cv in zip(xpos, open_vals, closed_vals):
        ax2.text(x - width / 2, ov * 1.04, f"{ov:.0f}s", ha="center", fontsize=10, color=RED)
        ax2.text(x + width / 2, cv * 1.04, f"{cv:.1f}s", ha="center", fontsize=10, color=BLUE)
    ax2.set_yscale("log")
    ax2.set_xticks(xpos)
    ax2.set_xticklabels(labels)
    ax2.set_ylabel("TTFT (seconds)")
    ax2.set_title("Coordinated omission at rho = 0.98", fontsize=13, fontweight="bold", pad=12)
    ax2.legend(frameon=False, loc="upper left", fontsize=10)

    _finish(
        fig,
        "bench-latency-vs-load.svg",
        "Single-server FCFS queue, service = 40 ms prefill + 5 ms x Uniform{16..256} tokens, Poisson arrivals,\n"
        "100k requests per load with 10k warmup dropped, seed 17. The measured mean tracks Pollaczek-Khinchine\n"
        "at every load; the p99 must be measured. Right: the same server probed two ways - the closed-loop\n"
        "generator backs off exactly when the server congests, and its p99 is a small multiple of p50.",
    )


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    fig_group_size_error()
    fig_kv_vs_weights()
    fig_specdec_optimal_k()
    fig_tp_decode_scaling()
    fig_moe_decode_intensity()
    fig_latency_vs_load()
