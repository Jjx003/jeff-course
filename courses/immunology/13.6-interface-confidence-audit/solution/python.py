"""Reference solution for the immune-interface confidence audit."""

from math import sqrt


RESIDUES = [
    {"chain": "H", "position": 31, "aa": "Y", "xyz": (0.0, 0.0, 0.0), "confidence": 92.0},
    {"chain": "H", "position": 32, "aa": "W", "xyz": (0.0, 4.0, 0.0), "confidence": 88.0},
    {"chain": "H", "position": 33, "aa": "S", "xyz": (0.0, 8.0, 0.0), "confidence": 55.0},
    {"chain": "A", "position": 101, "aa": "E", "xyz": (3.0, 0.0, 0.0), "confidence": 91.0},
    {"chain": "A", "position": 102, "aa": "K", "xyz": (4.0, 3.0, 0.0), "confidence": 82.0},
    {"chain": "A", "position": 103, "aa": "Q", "xyz": (3.0, 7.0, 0.0), "confidence": 60.0},
    {"chain": "A", "position": 104, "aa": "N", "xyz": (10.0, 10.0, 0.0), "confidence": 95.0},
]

CONTACT_CUTOFF = 5.0
CONFIDENCE_CUTOFF = 70.0


def distance(left: dict, right: dict) -> float:
    dx = left["xyz"][0] - right["xyz"][0]
    dy = left["xyz"][1] - right["xyz"][1]
    dz = left["xyz"][2] - right["xyz"][2]
    return sqrt(dx * dx + dy * dy + dz * dz)


def find_contacts(residues: list[dict], cutoff: float) -> list[tuple[dict, dict, float]]:
    antibody = [residue for residue in residues if residue["chain"] == "H"]
    antigen = [residue for residue in residues if residue["chain"] == "A"]
    contacts = []
    for left in antibody:
        for right in antigen:
            separation = distance(left, right)
            if separation <= cutoff:
                contacts.append((left, right, separation))
    return sorted(contacts, key=lambda item: (item[0]["position"], item[1]["position"]))


def label(residue: dict) -> str:
    return f'{residue["aa"]}{residue["chain"]}{residue["position"]}'


def main() -> None:
    contacts = find_contacts(RESIDUES, CONTACT_CUTOFF)
    supported = [
        contact for contact in contacts
        if min(contact[0]["confidence"], contact[1]["confidence"]) >= CONFIDENCE_CUTOFF
    ]
    uncertain = [contact for contact in contacts if contact not in supported]

    counts: dict[tuple[str, int], int] = {}
    for _, antigen, _ in supported:
        key = (antigen["aa"], antigen["position"])
        counts[key] = counts.get(key, 0) + 1

    top_count = max(counts.values(), default=0)
    hotspots = sorted(
        ((key, count) for key, count in counts.items() if count == top_count and count > 0),
        key=lambda item: item[0][1],
    )

    print(f"Interface contacts (distance <= {CONTACT_CUTOFF:.1f} A): {len(contacts)}")
    print(f"Confidence-supported contacts: {len(supported)}")
    print(f"Uncertainty-dependent contacts: {len(uncertain)}")
    print("Supported contact pairs: " + ", ".join(
        f"{label(left)}-{label(right)}" for left, right, _ in supported
    ))
    print("Candidate antigen hotspots: " + ", ".join(
        f'{aa}A{position} ({count})' for (aa, position), count in hotspots
    ))
    print(
        "Interpretation: prioritize E101 and K102 for controlled mutation; "
        "structure alone does not prove escape."
    )


if __name__ == "__main__":
    main()
