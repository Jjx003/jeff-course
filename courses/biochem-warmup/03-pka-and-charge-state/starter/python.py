from __future__ import annotations

from dataclasses import dataclass
from math import pow


@dataclass(frozen=True)
class IonizableGroup:
    name: str
    kind: str  # "acid" or "base"
    pka: float


GROUPS: dict[str, IonizableGroup] = {
    "n_term": IonizableGroup("N-terminus", "base", 9.0),
    "c_term": IonizableGroup("C-terminus", "acid", 2.2),
    "asp": IonizableGroup("Asp", "acid", 3.9),
    "glu": IonizableGroup("Glu", "acid", 4.2),
    "his": IonizableGroup("His", "base", 6.0),
    "cys": IonizableGroup("Cys", "acid", 8.3),
    "tyr": IonizableGroup("Tyr", "acid", 10.1),
    "lys": IonizableGroup("Lys", "base", 10.5),
    "arg": IonizableGroup("Arg", "base", 12.5),
}


def protonated_fraction(pH: float, pka: float) -> float:
    """Return the fraction of a group in its protonated form."""
    # TODO: implement the Henderson-Hasselbalch fraction.
    raise NotImplementedError


def group_charge(group: IonizableGroup, pH: float) -> float:
    """Return the expected charge for one ionizable group at this pH."""
    # TODO: acids are neutral when protonated and negative when deprotonated.
    # Bases are positive when protonated and neutral when deprotonated.
    raise NotImplementedError


def net_charge(group_keys: list[str], pH: float) -> float:
    """Return the summed expected charge for a collection of group keys."""
    # TODO: look up each group key in GROUPS and sum its charge.
    raise NotImplementedError


def main() -> None:
    examples = {
        "acidic_peptide": ["n_term", "asp", "glu", "c_term"],
        "basic_peptide": ["n_term", "lys", "arg", "his", "c_term"],
        "mixed_active_site": ["cys", "his", "asp", "tyr"],
    }

    for pH in (2.0, 7.0, 12.0):
        print(f"pH {pH:.1f}")
        for label, groups in examples.items():
            charge = net_charge(groups, pH)
            print(f"  {label}: {charge:.3f}")


if __name__ == "__main__":
    main()
