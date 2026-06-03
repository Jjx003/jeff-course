# Solution walkthrough

The streaming version rescales the old numerator and denominator whenever a later block has a larger maximum. That is the trick that keeps the computation stable and exact without seeing all scores at once.

Real kernels tile across query blocks, key blocks, heads, and batches, but the recurrence is the same.

