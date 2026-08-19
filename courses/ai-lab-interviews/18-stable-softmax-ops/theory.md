# The Derivations

## Max-subtracted softmax

Softmax is invariant to a constant shift:

$$\frac{e^{x_i-c}}{\sum_j e^{x_j-c}} = \frac{e^{x_i}e^{-c}}{e^{-c}\sum_j e^{x_j}} = \frac{e^{x_i}}{\sum_j e^{x_j}}$$

Setting $c = x_{\max}$ gives a largest exponent of $e^0 = 1$ and a denominator of at least 1. Nothing overflows; nothing divides by zero.

In float32, `exp` overflows at $x \approx 88.7$, which the script prints from `torch.finfo`. Attention logits reach that range easily in a large model — especially if the $1/\sqrt{d_k}$ went missing.

## log-sum-exp

$$\log\sum_i e^{x_i} = \log\left(e^{x_{\max}}\sum_i e^{x_i - x_{\max}}\right) = x_{\max} + \log\sum_i e^{x_i-x_{\max}}$$

The largest term inside the sum is $e^0 = 1$, so the sum is between 1 and $n$ — no overflow, and never $\log(0)$.

## Why `x - logsumexp(x)` beats `log(softmax(x))`

Both are mathematically $\log p_i$. Numerically they are very different.

`log(softmax(x))` forms $p_i$ first. For a token 200 logits below the max, $p_i \approx e^{-200}$, which underflows float32 to exactly zero — and then $\log 0 = -\infty$. The information was destroyed by the intermediate representation, not by the logarithm.

`x - logsumexp(x)` never forms $p_i$. The result, $-200$ or so, is a perfectly ordinary float.

This matters in practice for any loss computed on a low-probability token, which is exactly what a language model spends its time on.

## The online recurrence

Maintain a running maximum $m_k$ and a running denominator $d_k = \sum_{j\le k}e^{x_j - m_k}$. Note that $d_k$ is defined relative to the *current* maximum, which is what makes the recurrence work.

$$
\begin{aligned}
d_{k+1} &= \sum_{j=1}^{k+1}e^{x_j-m_{k+1}} \\
&= e^{x_{k+1}-m_{k+1}} + \sum_{j=1}^{k}e^{x_j-m_{k+1}} \\
&= e^{x_{k+1}-m_{k+1}} + \sum_{j=1}^{k}e^{x_j-m_k}\,e^{m_k-m_{k+1}} \\
&= e^{x_{k+1}-m_{k+1}} + d_k\,e^{m_k-m_{k+1}}
\end{aligned}
$$

The factor $e^{m_k-m_{k+1}}$ is the **rescaling term**: it converts the sum from being relative to the old maximum to being relative to the new one. When the maximum has not changed it equals 1 and the update is a plain addition.

Initialize with $m_0 = -\infty$ and $d_0 = 0$. Note $e^{-\infty - x} = 0$, so the first step behaves correctly with no special case.

## From online softmax to FlashAttention

Attention needs a weighted sum, not just a denominator:

$$o = \sum_i \mathrm{softmax}(x)_i\,v_i = \frac{\sum_i e^{x_i}v_i}{\sum_i e^{x_i}}$$

Both numerator and denominator can be accumulated online, with the **same** rescaling factor:

$$\mathrm{acc}_{k+1} = \mathrm{acc}_k\,e^{m_k-m_{k+1}} + e^{x_{k+1}-m_{k+1}}v_{k+1}$$

$$d_{k+1} = d_k\,e^{m_k-m_{k+1}} + e^{x_{k+1}-m_{k+1}}$$

with the output $\mathrm{acc}/d$ at the end.

That is FlashAttention. Everything else in the paper — tile sizes, SRAM budgets, recomputing in the backward pass instead of storing — is engineering on top of this recurrence. The consequence is that the $(B,H,S,S)$ score tensor is never materialized, so attention's memory footprint drops from $O(S^2)$ to $O(S)$ and its HBM traffic falls by a factor of roughly $M/d^2$ — SRAM size over head dimension squared — while the output stays **exact**. (Traffic is reduced by a large constant, not made linear — a standard follow-up.)

## Why reductions stay in fp32

bf16 has 7 mantissa bits — 8 significand bits with the implicit one, or roughly 2–3 decimal digits. A single bf16 multiply is fine: the error is small relative to the value. A *sequential reduction with a bf16 accumulator* is not, and the failure is worse than "errors accumulate". Once the running sum grows past about $2^8 = 256$ times the size of an incoming term, adding that term rounds to **nothing at all** — the accumulator stalls. The script shows the purest case: summing 8192 ones in a bf16 accumulator returns exactly 256, because $256 + 1$ rounds back to 256. On 8192 squared activations the bf16 accumulator comes back ~70% low; the fp32 accumulator is within $10^{-5}$ of the float64 answer.

One honest subtlety the script also demonstrates: `torch.sum` on a bf16 tensor does **not** show this failure, because torch's reduction kernels upcast the accumulator internally (as do cuBLAS/tensor-core matmuls, which accumulate bf16 products in fp32). The rule "reductions stay in fp32" is about the accumulator dtype in kernels and reductions *you* write — a Triton kernel, a fused norm, a handwritten loss — and about not casting statistics down to bf16 between ops. That is the justification for upcasting inside RMSNorm, inside softmax denominators, and inside loss reductions.
