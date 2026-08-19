# Precision and Numerical Stability

Two topics that look like implementation trivia and are not. Precision questions are how interviewers find out whether you have trained something real, because the answers are only obvious once you have watched a run go to `NaN` at 3am.

## What gets asked

- What is the difference between fp16 and bf16, and why did bf16 win for training?
- What is loss scaling and why do you not need it in bf16?
- What does mixed precision actually keep in fp32?
- Why is softmax computed with a max subtraction?
- Derive the online softmax recurrence.
- Why does `logsumexp` exist when you could just take the log of a sum?
- What breaks first if you train a 70B model in pure bf16?
- What is fp8 training and what makes it hard?

## The format landscape

![Two panels. Left: bit layouts for fp32, tf32, bf16, fp16 and both fp8 formats, split into sign, exponent and mantissa. Right: maximum representable value and decimal digits of precision for each.](/courses/ai-lab-interviews/precision-formats.svg)

The single sentence that answers most precision questions:

> **Exponent bits buy range. Mantissa bits buy precision. bf16 keeps fp32's 8 exponent bits and pays for them with mantissa — full fp32 range, less precision — which is why casting fp32 to bf16 never overflows.**

fp16 has a 5-bit exponent and tops out at 65504. Gradients in a large model routinely underflow that format's small end, which is why fp16 training needed loss scaling — multiply the loss by a large constant so gradients land in representable range, then divide it out before the update. bf16 made that machinery unnecessary overnight.

## The stability toolkit

Four tricks, all of which you should be able to derive:

1. **Max-subtracted softmax** — softmax is shift-invariant, so subtract the row max and nothing can overflow.
2. **log-sum-exp** — never materialize a tiny probability and then take its log.
3. **Online softmax** — fuse the max pass and the sum pass into one, which is what makes FlashAttention possible.
4. **fp32 accumulation in reductions** — norms, softmax denominators, and loss reductions are computed in fp32 even in a bf16 model.

The next module makes you implement all four and measure exactly how much they buy.
