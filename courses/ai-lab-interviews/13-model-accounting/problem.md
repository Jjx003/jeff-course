# Accounting: Parameters, FLOPs, and Memory

There is a specific moment in a technical discussion where a candidate either lands or does not. The interviewer asks something like *"could you fine-tune a 70B model on one node?"* and you either produce a number with the arithmetic behind it, or you say "it depends".

Both answers are technically true. Only one gets you the offer.

This module is the set of formulas that make the first answer possible without a calculator. There are about eight of them, and once they are automatic, a whole class of interview question turns into mental arithmetic.

## The formulas

| Quantity | Formula | Why |
|---|---|---|
| Parameters | $N \approx 12Ld^2 + Vd$ | $4d^2$ attention, $8d^2$ FFN, per layer |
| Training FLOPs | $C \approx 6ND$ | 2 forward, 4 backward, per parameter per token |
| Inference FLOPs | $\approx 2N$ per token | forward only |
| Weights in memory | $N \times$ bytes/param | 2 for bf16, 1 for int8, 0.5 for int4 |
| Adam training state | $16N$ bytes (fp32) | param + grad + two moments |
| KV cache | $2 \cdot L \cdot G \cdot d_h \cdot b \cdot S \cdot \text{bytes}$ | K and V, per layer, per token |
| Activation memory | $\approx s \cdot b \cdot S \cdot d \cdot L$ | $s$ is 10–30 depending on what is stored |
| Attention scores | $b \cdot H \cdot S^2$ elements | the tensor FlashAttention avoids |

## What gets asked

- "How much memory to train a 7B model? To fine-tune it? To serve it?"
- "How many GPUs for a 70B model at 128k context and batch 32?"
- "How long would this pretraining run take on 1024 H100s?"
- "Where does the memory actually go in a training step?"
- "You have 80 GB. What is the largest model you can full-fine-tune? LoRA-fine-tune? Serve?"

![Two panels. Left: stacked parameter counts for four models split into attention, FFN and embeddings. Right: embeddings as a percentage of parameters, 31% for GPT-2 small down to under 1% for Llama-2 70B.](/courses/ai-lab-interviews/params-breakdown.svg)

## The habit to build

Round aggressively and say so. $12Ld^2$, not the exact count. 2 bytes per parameter. $10^9$ for a "billion" rather than $2^{30}$. An interviewer wants to see the *structure* of the estimate; if they want precision they will ask for it, and you can add the correction terms then.

Say the units out loud as you go. Most arithmetic errors under pressure are unit errors, and narrating "bytes per parameter, times parameters, gives bytes" catches them before they land.
