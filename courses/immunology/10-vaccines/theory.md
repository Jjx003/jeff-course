# Deeper theory: waning, boosting, and breadth

A useful two-component approximation extends the single-decay model from the
memory module by separating short- and long-lived antibody sources:

$$T(t)=A_s e^{-k_s t}+A_l e^{-k_l t},\qquad k_s>k_l.$$

$T(t)$ is measured serum titer at time $t$. $A_s$ and $A_l$ are the starting
contributions from faster- and slower-decaying sources, while $k_s$ and $k_l$ are
their apparent decay rates. The early steep decline can reflect contraction of short-lived plasmablasts;
the slower tail reflects longer-lived plasma cells. This is why extrapolating a
single exponential from the first month can badly underestimate durability.
Memory B cells are not in $T(t)$: they can broaden and mature while serum titer
falls, but recall takes time.

## A neutralization threshold is a distribution

Suppose protection follows a logistic relation to log titer:

$$P(\text{protected}\mid T)=\frac{1}{1+\exp[-(\alpha+\beta\log T)]}.$$

Here $T$ is measured titer, $\alpha$ sets the baseline position of the curve, and
$\beta$ controls how sharply protection changes with log titer. These parameters
must be estimated for a defined population, endpoint, assay, and time window;
they are not universal immune constants. There is no magical universal cutoff. Assay error, exposure dose, variant,
host age, and tissue concentration spread risk around any reported threshold.
Report uncertainty and calibration, not only discrimination.

## Breadth versus magnitude

A booster that raises the same strain-focused clones can increase peak titer
without improving escape coverage. Compare antigenic panels, epitope targeting,
memory-clone recruitment, and durability. A geometric mean titer averaged across
people also does not tell whether a vulnerable subgroup remains unprotected.

## Evidence ladder

Binding, neutralization, systems signatures, animal challenge, randomized
clinical endpoints, effectiveness studies, and post-licensure surveillance
answer different questions. The strongest program links them rather than asking
one assay to stand in for all of them.
