## Solution walkthrough

`die_per_wafer` starts with the circular wafer area divided by die area, then
subtracts an edge-loss correction for incomplete dies near the wafer boundary.
The result is floored because the function returns complete dies.

`poisson_yield` converts die area from mm^2 to cm^2, multiplies by defect
density to get the expected number of fatal defects, then returns the
probability of zero fatal defects:

$$
Y = e^{-AD}
$$

`good_die_per_month` composes the first two functions:

$$
\text{good dies} =
\left\lfloor \text{wafers} \times \text{dies per wafer} \times Y \right\rfloor
$$

`bottleneck_capacity` uses `min()` over the dictionary items with capacity as
the comparison key. The returned pair is the step that limits the line.
