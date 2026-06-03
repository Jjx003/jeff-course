## Hint 1

Use `math.exp` and `math.log`. The gas constant should be in kJ so it matches the input energy units.

## Hint 2

For `boltzmann_weights`, compute unnormalized weights first, sum them, then divide each weight by the sum.

## Hint 3

To avoid overflow or underflow in the Boltzmann calculation, subtract `min(energies_kj)` before exponentiating:

$$
e^{-(G_i - G_{min})/RT}
$$

This does not change the normalized probabilities.

## Going deeper

- Ask what happens when temperature increases. Energy gaps matter less because $RT$ gets larger.
- A mutation that stabilizes a protein by only $5\ \text{kJ/mol}$ can strongly change the folded fraction near room temperature.
- Thermodynamic stability does not guarantee rapid folding. A high activation barrier can trap a molecule away from equilibrium.
