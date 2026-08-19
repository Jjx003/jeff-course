# Drill: Model Accounting

The formulas from module 13, under a clock.

The goal is not to be a calculator. It is to remove the hesitation — so that when an interviewer says "how much memory would that take", the structure of the answer arrives before you have finished hearing the question, and you spend your attention on the reasoning instead of the multiplication.

## Conventions

- **Decimal, not binary.** 1 GB is $10^9$ bytes here. Say which you are using and it never matters.
- **$12d^2$ per layer**, $Vd$ for embeddings.
- **$6ND$** training FLOPs, **$2N$** inference FLOPs per token.
- **16 bytes per parameter** for Adam training state.
- **KV cache** $= 2 \cdot L \cdot G \cdot d_h \cdot \text{bytes} \cdot S$ per sequence.

Tolerances are generous enough that rounding sensibly is fine and being sloppy is not.

## Target

85% at 20 prompts in 150 seconds. Clear it twice, then come back a week later — this is the module whose decay you will notice most, because none of it is conceptual.
