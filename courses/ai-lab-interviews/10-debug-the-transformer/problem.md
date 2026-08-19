# Debug the Transformer

*"Here is a transformer implementation. It trains, but the model is bad. Find out why."*

This is a real interview format, and it is a good one, because it tests something an implementation question cannot: whether you have a **method** for finding a bug you cannot see.

The starter contains a complete decoder-only LM with **six seeded bugs**. Every one of them has shipped in real code. None of them raises an exception. Several of them let the model train to a low loss while producing a model that is useless.

## The rules

- Only the `MODEL` section is yours to change. The `HARNESS` section below it is a set of independent reference implementations and probes — it is the oracle, and editing it defeats the point.
- The probes run **local to global**: mask, then head reshape, then the attention kernel, then the attention module, then the final norm, then the loss, then the whole model. Fix the first failure, rerun, repeat.
- Give yourself 40 minutes. That is roughly what you would get in the room.

## Why the probe ordering matters

A failure at the bottom of the list tells you almost nothing while anything above it is broken. "The model does not learn" is compatible with all six bugs at once. "`causal_mask(6)` is not lower-triangular" is compatible with exactly one.

This is the entire method, and it is what the interviewer is actually watching for. Bisect the system, not the symptom.

## A warning about check 9

The end-to-end memorization check is the **least** informative probe in the file, and one of the seeded bugs will make it pass while the model is deeply broken. Watch for that when it happens — it is the most valuable thing in the module.

## The six bug classes

Not which lines. What kind of thing to look for:

1. A masking bug.
2. A tensor-reshape bug that produces the right shape and the wrong semantics.
3. A missing scalar.
4. A component applied to a tensor it should never touch.
5. A component that is constructed and then never used.
6. An off-by-one in the training objective.
