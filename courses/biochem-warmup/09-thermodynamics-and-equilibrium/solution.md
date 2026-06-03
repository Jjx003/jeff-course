# Solution Walkthrough

The key equation is:

$$
\Delta G^\circ = -RT\ln K
$$

Solving for $K$ gives:

$$
K = e^{-\Delta G^\circ/RT}
$$

Solving for $\Delta G^\circ$ gives the original form:

$$
\Delta G^\circ = -RT\ln K
$$

For Boltzmann probabilities, the solution first subtracts the minimum energy. This keeps the largest exponent equal to zero and makes the calculation more stable:

```python
minimum_energy = min(energies_kj)
weights = [math.exp(-(energy - minimum_energy) / rt) for energy in energies_kj]
```

The final probabilities come from dividing by `sum(weights)`.

For two-state folding, choose an arbitrary zero:

- $G_F = 0$
- $G_U = \Delta G_{U-F}$

Then compute the Boltzmann probability of the folded state. Positive $\Delta G_{U-F}$ means unfolded is higher in free energy, so the folded state dominates.
