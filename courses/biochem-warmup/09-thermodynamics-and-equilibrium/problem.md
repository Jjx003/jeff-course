## Equilibrium is a population, not a choice

Biochemical systems are noisy, molecular, and reversible. A protein does not "choose" one shape because it wants to; it samples states, and the lower-free-energy states are more populated at equilibrium.

![Two-state folding equilibrium free-energy diagram](/courses/biochem-warmup/folding-equilibrium.svg)

In this exercise you will implement four small calculations:

1. Convert a standard free energy change into an equilibrium constant.
2. Convert an equilibrium constant back into $\Delta G^\circ$.
3. Compute Boltzmann probabilities for a list of state energies.
4. Predict the folded fraction for a two-state protein.

Use the gas constant in kJ units:

$$
R = 0.008314462618\ \text{kJ mol}^{-1}\text{K}^{-1}
$$

## Tasks

Implement these functions in `starter/python.py`:

- `equilibrium_constant(delta_g_kj, temperature_k=298.15)`
- `delta_g_from_k(k_eq, temperature_k=298.15)`
- `boltzmann_weights(energies_kj, temperature_k=298.15)`
- `folded_fraction(delta_g_unfolded_minus_folded_kj, temperature_k=298.15)`

For a reaction written in the forward direction:

$$
\Delta G^\circ = -RT \ln K
$$

For discrete molecular states:

$$
p_i = \frac{e^{-G_i/RT}}{\sum_j e^{-G_j/RT}}
$$

For two-state folding, this module defines:

$$
\Delta G_{U-F} = G_U - G_F
$$

If $\Delta G_{U-F}$ is positive, the folded state is lower in free energy and should be more populated.

## Expected behavior

Your script should run directly and print a short deterministic report. The reference solution rounds output for display, but your internal functions should use floating-point calculations.

Avoid external packages; the Python standard library is enough.
