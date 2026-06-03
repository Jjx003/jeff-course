"""Thermodynamics warm-up: Delta G, equilibrium, and folding populations."""

import math

R_KJ_PER_MOL_K = 0.008314462618


def equilibrium_constant(delta_g_kj, temperature_k=298.15):
    """Return K for a standard free energy change in kJ/mol."""
    # TODO: use Delta G = -RT ln K
    raise NotImplementedError


def delta_g_from_k(k_eq, temperature_k=298.15):
    """Return Delta G in kJ/mol for an equilibrium constant K."""
    # TODO: rearrange Delta G = -RT ln K
    raise NotImplementedError


def boltzmann_weights(energies_kj, temperature_k=298.15):
    """Return normalized probabilities for states with free energies in kJ/mol."""
    # TODO: convert energies to normalized Boltzmann weights.
    # For numerical stability, subtract the minimum energy before exponentiating.
    raise NotImplementedError


def folded_fraction(delta_g_unfolded_minus_folded_kj, temperature_k=298.15):
    """Return P(folded) for a two-state protein.

    delta_g_unfolded_minus_folded_kj = G_unfolded - G_folded.
    Positive values favor the folded state.
    """
    # TODO: model energies [G_folded, G_unfolded] as [0, delta_g].
    raise NotImplementedError


def main():
    delta_g = -5.7
    k_eq = equilibrium_constant(delta_g)
    print(f"Delta G {delta_g:.1f} kJ/mol -> K = {k_eq:.3f}")
    print(f"K 10.0 -> Delta G = {delta_g_from_k(10.0):.3f} kJ/mol")

    energies = [0.0, 2.5, 7.5]
    probs = boltzmann_weights(energies)
    print("State probabilities:", ", ".join(f"{p:.3f}" for p in probs))

    for dg in [-5.0, 0.0, 5.0, 10.0]:
        print(f"Delta G_U-F {dg:>5.1f} kJ/mol -> folded fraction {folded_fraction(dg):.3f}")


if __name__ == "__main__":
    main()
