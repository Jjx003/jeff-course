## Dies per wafer

A rough industry approximation for rectangular dies on a circular wafer is:

$$
\text{DPW} \approx
\frac{\pi d^2}{4A}
- \frac{\pi d}{\sqrt{2A}}
$$

where:

- $d$ is wafer diameter in millimeters.
- $A$ is die area in square millimeters.

The first term divides wafer area by die area. The second term estimates edge
losses because rectangular dies near the circular boundary are incomplete.

This is still an approximation. Real die-per-wafer depends on scribe lanes,
edge exclusion, reticle layout, die shape, and whether partially usable edge
locations exist. For early reasoning, the approximation is good enough.

## Poisson yield

Convert die area from square millimeters to square centimeters:

$$
A_{\text{cm}^2} = \frac{A_{\text{mm}^2}}{100}
$$

If fatal defects are randomly distributed with density $D$ defects per
cm$^2$, then the expected number of fatal defects on one die is:

$$
\lambda = A_{\text{cm}^2}D
$$

The probability of zero fatal defects under a Poisson distribution is:

$$
Y = e^{-\lambda}
$$

This is why big dies are economically painful. Doubling die area roughly
doubles $\lambda$, which lowers the probability of a perfect die.

## Good dies per month

The basic monthly output model is:

$$
\text{good dies/month} =
\text{wafers/month} \times \text{dies/wafer} \times \text{yield}
$$

This ignores binning, cycle time, package yield, and demand mix. Those omissions
are useful for now because the model shows the core levers clearly.

## Bottleneck capacity

For a line with several required process families, the bottleneck is the
minimum capacity:

$$
\text{capacity} = \min_i C_i
$$

Adding more of a non-bottleneck tool does not increase total output until the
current bottleneck is relieved.
