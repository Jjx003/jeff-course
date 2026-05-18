"""
Reference solution for module 21.
"""

import numpy as np

ALPHABET = "ACDEFGHIKLMNPQRSTVWY"

WT_SEQUENCE = "MAEGLKWIVASR"

PDB_BACKBONE = """\
ATOM      1  N   MET A   1       0.000   0.000   0.000  1.00  0.00           N
ATOM      2  CA  MET A   1       1.500   0.000   0.000  1.00  0.00           C
ATOM      3  C   MET A   1       2.300   1.300   0.000  1.00  0.00           C
ATOM      4  O   MET A   1       1.800   2.400   0.000  1.00  0.00           O
ATOM      5  N   ALA A   2       3.600   1.300   0.500  1.00  0.00           N
ATOM      6  CA  ALA A   2       4.500   2.500   0.500  1.00  0.00           C
ATOM      7  C   ALA A   2       5.500   2.300   1.700  1.00  0.00           C
ATOM      8  O   ALA A   2       5.300   1.300   2.500  1.00  0.00           O
ATOM      9  CA  GLU A   3       6.500   3.500   2.000  1.00  0.00           C
ATOM     10  CA  GLY A   4       7.500   4.700   2.300  1.00  0.00           C
ATOM     11  CA  LEU A   5       8.500   5.900   2.600  1.00  0.00           C
ATOM     12  CA  LYS A   6       9.500   7.100   2.900  1.00  0.00           C
ATOM     13  CA  TRP A   7      10.500   8.300   3.200  1.00  0.00           C
ATOM     14  CA  ILE A   8      11.500   9.500   3.500  1.00  0.00           C
ATOM     15  CA  VAL A   9      12.500  10.700   3.800  1.00  0.00           C
ATOM     16  CA  ALA A  10      13.500  11.900   4.100  1.00  0.00           C
ATOM     17  CA  SER A  11      14.500  13.100   4.400  1.00  0.00           C
ATOM     18  CA  ARG A  12      15.500  14.300   4.700  1.00  0.00           C
TER
END
"""

NUM_SAMPLES = 5
TEMPERATURE = 1.0
SEED = 0


def parse_backbone(pdb_str: str) -> int:
    n = 0
    for line in pdb_str.splitlines():
        if line.startswith("ATOM") and " CA " in line:
            n += 1
    return n


def stub_inverse_fold(
    wt_sequence: str,
    num_samples: int = 5,
    seed: int = 0,
    temperature: float = 1.0,
    wt_bias: float = 2.0,
) -> list[tuple[str, float]]:
    samples: list[tuple[str, float]] = []
    for k in range(num_samples):
        rng = np.random.default_rng(seed + k)
        seq_chars: list[str] = []
        log_prob_total = 0.0
        for wt_aa in wt_sequence:
            logits = rng.standard_normal(20) * 1.5
            wt_idx = ALPHABET.index(wt_aa)
            logits[wt_idx] += wt_bias
            scaled = logits / temperature
            probs = np.exp(scaled - scaled.max())
            probs /= probs.sum()
            chosen_idx = int(rng.choice(20, p=probs))
            log_prob_total += float(np.log(probs[chosen_idx]))
            seq_chars.append(ALPHABET[chosen_idx])
        samples.append(("".join(seq_chars), log_prob_total))
    return samples


def recovery(seq: str, wt: str) -> int:
    return sum(a == b for a, b in zip(seq, wt))


def main() -> None:
    n_res = parse_backbone(PDB_BACKBONE)
    print("ProteinMPNN inverse folding (stub fallback)")
    print(f"Backbone: {n_res} residues (chain A)")
    print(f"Wild-type sequence: {WT_SEQUENCE}")
    print()
    print(f"Sampling {NUM_SAMPLES} candidates at temperature = {TEMPERATURE} ...")

    samples = stub_inverse_fold(
        WT_SEQUENCE,
        num_samples=NUM_SAMPLES,
        seed=SEED,
        temperature=TEMPERATURE,
    )

    L = len(WT_SEQUENCE)
    for i, (seq, lp) in enumerate(samples, 1):
        recov = recovery(seq, WT_SEQUENCE)
        pct = 100.0 * recov / L
        print(f"  {i}. {seq}  log_prob = {lp:7.3f}  recovery = {recov:>2}/{L} ({pct:5.1f}%)")


if __name__ == "__main__":
    main()
