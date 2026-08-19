# RMSNorm, SwiGLU, and RoPE

Three components, each of which replaced something from the 2017 architecture. Each is short. Each has a detail people get wrong.

## What to implement

1. **`RMSNorm`** — the norm, plus the fp32 upcast that every serious implementation does and most tutorials skip.
2. **`SwiGLU`** — the gated FFN, sized so it costs the same as a 4x ReLU MLP.
3. **`build_rope_cache` and `apply_rope`** — precompute the sin and cos tables, then rotate Q and K.

## What the script checks

- **RMSNorm** matches a float64 reference, and — the check that matters — a bf16 model with an fp32-internal norm is closer to the float64 answer than a naive all-bf16 norm. You will see the actual numbers.
- **SwiGLU** has exactly the same parameter count as the `4d` ReLU FFN it replaces.
- **RoPE is a rotation**: it preserves the norm of every vector it touches.
- **RoPE is relative**: the script computes $q_m \cdot k_n$ for several $(m, n)$ pairs and asserts the value depends only on $m - n$. This is the whole point of RoPE, and proving it in three lines is a strong thing to be able to do in an interview.
- **Position sensitivity**: attention scores under RoPE actually change with position, so the test above is not passing trivially.

## Why these three together

They are the components a "now build the block" follow-up expects. Once you have attention from the previous module and these three, module 9's full LM is assembly rather than invention.
