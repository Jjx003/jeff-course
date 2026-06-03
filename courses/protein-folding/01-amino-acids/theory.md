![General amino-acid structure: shared backbone and variable side chain](/courses/protein-folding/wiki-amino-acid-zwitterions.svg)

*The shared backbone and variable side chain `R` common to all 20 standard
amino acids. Image from Wikimedia Commons, Tim Vickers / GYassineMrabet,
CC BY 3.0.*

## The full amino-acid lookup table

The one-letter codes, three-letter codes, full names, and approximate
properties of the 20 standard amino acids. Memorising this table is *not*
necessary, but having it handy makes reading the biology literature much
easier.

| 1-letter | 3-letter | Name | Side-chain category |
|---|---|---|---|
| A | Ala | Alanine | Small hydrophobic |
| R | Arg | Arginine | Positively charged |
| N | Asn | Asparagine | Polar |
| D | Asp | Aspartate | Negatively charged |
| C | Cys | Cysteine | Polar / disulfide-forming |
| E | Glu | Glutamate | Negatively charged |
| Q | Gln | Glutamine | Polar |
| G | Gly | Glycine | Smallest / flexible |
| H | His | Histidine | Positively charged at neutral pH |
| I | Ile | Isoleucine | Hydrophobic |
| L | Leu | Leucine | Hydrophobic |
| K | Lys | Lysine | Positively charged |
| M | Met | Methionine | Hydrophobic (sulfur-containing) |
| F | Phe | Phenylalanine | Aromatic, hydrophobic |
| P | Pro | Proline | Rigid kink |
| S | Ser | Serine | Polar |
| T | Thr | Threonine | Polar |
| W | Trp | Tryptophan | Aromatic, hydrophobic |
| Y | Tyr | Tyrosine | Aromatic, polar |
| V | Val | Valine | Hydrophobic |

## Why no B, J, O, U, X, Z?

The IUPAC one-letter alphabet reserves a handful of letters for situations
where the exact identity of a residue is uncertain or non-standard:

- **B** = either `D` (Asp) or `N` (Asn) — used when the experiment can't tell
  which.
- **Z** = either `E` (Glu) or `Q` (Gln) — same idea.
- **J** = either `I` (Ile) or `L` (Leu) — these two have identical masses in
  mass spectrometry and are sometimes indistinguishable.
- **X** = any amino acid — used as a wildcard when the residue is unknown.
- **U** = selenocysteine — a rare 21st amino acid found in a few enzymes.
- **O** = pyrrolysine — even rarer 22nd amino acid, only in some archaea
  and bacteria.

For machine learning, most protein language model vocabularies include the
20 standard letters, plus `X`, plus a `<MASK>` / `<PAD>` / `<CLS>` token or
two for transformer machinery.

## The genetic code in one paragraph

DNA is read in **codons** — triplets of nucleotides like `ATG` or `TAC`. Each
codon maps to exactly one amino acid (with a few special codons signalling
"stop translation"). There are $4^3 = 64$ possible codons and only 20 amino
acids, so the code is **redundant**: most amino acids are encoded by 2–6
different codons. The codon `ATG` always means "start here, and add a
methionine", which is why so many proteins begin with `M`.

This redundancy is also why **synonymous mutations** (DNA changes that don't
alter the protein sequence) are common — most random single-letter DNA
changes either change nothing or change one amino acid to a similar one.

## Side-chain pKa and pH

A few amino acids are **titratable** — their charge depends on the pH of the
surrounding solution. Inside a cell (pH ≈ 7.4):

- `D` and `E` are usually deprotonated, carrying a `−1` charge.
- `K` and `R` are usually protonated, carrying a `+1` charge.
- `H` sits right at the borderline — its imidazole side chain has a pKa
  around 6.0, so a small drop in local pH can flip it from neutral to `+1`.

Histidine's tunable charge is why it shows up so often in enzyme active
sites: shuttling a proton in and out is a routine catalytic move.

## Stereochemistry: only L-amino acids

Every amino acid except glycine has a chiral alpha carbon — there are two
mirror-image versions, "L" and "D". Almost all amino acids in living
proteins are the **L** form. D-amino acids exist in nature but are rare and
specialised (bacterial cell walls, a few peptide antibiotics, certain
neurotransmitters). When you see a protein sequence written as letters,
assume L-amino acids unless explicitly told otherwise.

Why does life pick L? Nobody is sure. It's one of the oldest unresolved
questions in origin-of-life chemistry.
