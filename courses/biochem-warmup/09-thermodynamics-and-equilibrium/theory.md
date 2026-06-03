## Free energy sets the direction of change

Free energy measures the part of a system's energy that can bias change at
constant temperature and pressure. In chemistry and biochemistry, the sign of
$\Delta G$ tells you which direction is favored, not how fast it happens.

For a standard-state reaction,

$$
\Delta G^\circ = -RT\ln K
$$

This equation connects a thermodynamic preference to an equilibrium ratio:

- $\Delta G^\circ < 0$ means $K > 1$, so products are favored.
- $\Delta G^\circ = 0$ means $K = 1$, so neither side is favored.
- $\Delta G^\circ > 0$ means $K < 1$, so reactants are favored.

The relationship is exponential. A few kJ/mol can shift populations noticeably because $RT$ at room temperature is only about $2.48\ \text{kJ/mol}$.

## Boltzmann weighting

At equilibrium, states with lower free energy are more probable, but higher-energy states do not disappear. Their probability is suppressed by a Boltzmann factor:

$$
w_i = e^{-G_i/RT}
$$

Probabilities are normalized weights:

$$
p_i = \frac{w_i}{\sum_j w_j}
$$

Because adding the same constant to every $G_i$ does not change the final probabilities, stable code often subtracts the minimum energy first before exponentiating.

## Two-state folding

A minimal folding model has only two macrostates:

$$
F \rightleftharpoons U
$$

where $F$ is folded and $U$ is unfolded. This is a cartoon, but it is a useful first model. If

$$
\Delta G_{U-F} = G_U - G_F
$$

then the folded fraction is:

$$
P(F) = \frac{e^{-G_F/RT}}{e^{-G_F/RT} + e^{-G_U/RT}}
$$

Setting $G_F = 0$ and $G_U = \Delta G_{U-F}$ gives the same population without changing the answer.

## Thermodynamics is not kinetics

A lower-free-energy folded state can still form slowly. Thermodynamics tells you the final equilibrium bias; kinetics tells you the route and rate. The next module separates these ideas by introducing activation barriers and catalysts.
