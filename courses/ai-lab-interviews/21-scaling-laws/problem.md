# Scaling Laws

Scaling laws are the closest thing modern ML has to a design equation. They are also a favourite technical-discussion topic, because the reasoning is compact enough to hold in a conversation and the follow-ups reveal quickly whether someone has thought about it or memorized "20 tokens per parameter".

## What gets asked

- What did Kaplan get wrong and Chinchilla get right?
- What is compute-optimal, and why do deployed models ignore it?
- You have $10^{23}$ FLOPs. What model do you train, and on how much data?
- Why does the loss curve have an irreducible term?
- How do you use scaling laws to make a decision *before* running the big model?
- What breaks scaling laws?

## The parametric form

$$L(N, D) = E + \frac{A}{N^{\alpha}} + \frac{B}{D^{\beta}}$$

Three terms, each with a plain meaning:

- $E \approx 1.69$ — the **irreducible loss**, the entropy of natural text. No model gets below it.
- $A/N^{\alpha}$ — loss from the model being too small to represent the distribution.
- $B/D^{\beta}$ — loss from having seen too little data to learn it.

With $C \approx 6ND$ as the compute constraint, minimizing $L$ subject to fixed $C$ gives the compute-optimal frontier. Because $\alpha \approx 0.34$ and $\beta \approx 0.28$ are close, the optimum scales $N$ and $D$ at roughly the same rate — which is the entire Chinchilla result in one sentence.

![Two panels. Left: loss against parameter count at four fixed compute budgets, each curve U-shaped with a marked minimum. Right: tokens per parameter against training compute, showing the published parametric fit's optimum rising from about 30 to 95, the paper's 20:1 headline as a flat line, and four Llama models plotted far above both.](/courses/ai-lab-interviews/scaling-laws.svg)

## The reframe that matters

Compute-optimal means **cheapest to train** for a given loss. It says nothing about deployment.

If you will serve a model billions of times, a smaller model trained far past compute-optimal is dramatically cheaper overall, even though it cost more to train. Llama-family models span roughly 20–1900 tokens per parameter — Llama-2-70B at 29, Llama-3-70B at 214, Llama-3-8B at 1875 — with the small models pushed hardest, because they are the ones that get served most. Being able to explain *why* the ratio varies that way is a much better answer than reciting the Chinchilla number.
