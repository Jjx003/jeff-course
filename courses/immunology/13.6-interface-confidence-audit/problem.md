# Audit a predicted antibody-antigen interface

## Goal

The structural-immunology module argued that a plausible complex is a hypothesis,
not a mechanism verdict. In this short lab, turn that principle into code.

The starter file contains a tiny predicted complex represented by one coordinate
per residue:

- chain `H` is an antibody heavy-chain loop;
- chain `A` is an antigen surface;
- each residue has a local confidence score from 0 to 100.

Your program must find cross-chain contacts, determine which contacts are supported
by confident local geometry, and rank antigen residues for mutation experiments.
It uses only the Python standard library and runs on any machine with Python.

## The data

Each residue is a dictionary with:

```python
{
    "chain": "H",
    "position": 31,
    "aa": "Y",
    "xyz": (0.0, 0.0, 0.0),
    "confidence": 92.0,
}
```

Treat two residues as an interface contact when:

1. they belong to different chains; and
2. their Euclidean distance is at most `5.0` angstroms.

A contact is **confidence-supported** only when both residues have confidence at
least `70.0`. A contact involving either lower-confidence residue is
**uncertainty-dependent**.

## Tasks

1. Implement `distance(a, b)` using the three coordinates in `xyz`.
2. Implement `find_contacts(residues, cutoff)` so every cross-chain pair appears
   once and contacts are sorted by antibody position, then antigen position.
3. Split contacts into confidence-supported and uncertainty-dependent groups.
4. Count confidence-supported contacts for each antigen residue.
5. Report all antigen residues tied for the highest positive count as candidate
   hotspots. Do not use uncertain contacts to break a tie.

## Required output

Your output must match exactly:

```text
Interface contacts (distance <= 5.0 A): 6
Confidence-supported contacts: 4
Uncertainty-dependent contacts: 2
Supported contact pairs: YH31-EA101, YH31-KA102, WH32-EA101, WH32-KA102
Candidate antigen hotspots: EA101 (2), KA102 (2)
Interpretation: prioritize E101 and K102 for controlled mutation; structure alone does not prove escape.
```

The label `YH31` means tyrosine (`Y`) at position 31 in chain `H`. Keep distances
internal; the required output summarizes the audit rather than printing every
floating-point value.

## What the result means

`E101` and `K102` are good first perturbations because each participates in two
contacts whose local geometry is confidence-supported. `Q103` also appears near
the antibody, but its contacts depend on lower-confidence residues. That makes it
a useful uncertainty target, not stronger evidence of a hotspot.

A mutation experiment still needs:

- antigen expression and fold controls;
- binding affinity or kinetics;
- unrelated-antibody controls;
- a cellular or neutralization assay;
- ideally, a compensatory rescue.

The code prioritizes experiments. It does not convert a predicted interface into
proof of binding or immune escape.
