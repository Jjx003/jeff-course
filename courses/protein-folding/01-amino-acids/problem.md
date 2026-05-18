## Why an amino-acid alphabet?

Every protein in every organism on Earth is built from the same short list of
small molecules called **amino acids**. The standard set has **20** members.
String them together in different orders and you get insulin, hemoglobin,
the keratin in your fingernails, the enzymes digesting your lunch, and the
antibodies guarding your cells. Same alphabet — wildly different words.

This is the single most important fact for the whole course: because there is
a fixed, small vocabulary, **a protein can be written as a string of letters**,
exactly like a sentence in English. Myoglobin, the oxygen-shuttling protein in
your muscles, looks like this:

```text
MGLSDGEWQLVLNVWGKVEADIPGHGQEVLIRLFKGHPETLEKFDKFKHLKSEDEMKASE
DLKKHGATVLTALGGILKKKGHHEAEIKPLAQSHATKHKIPVKYLEFISECIIQVLQSKH
PGDFGADAQGAMNKALELFRKDMASNYKELGFQG
```

A single character per amino acid. By convention the 20 standard amino acids
get the letters `ACDEFGHIKLMNPQRSTVWY` — every letter of the alphabet *except*
`B`, `J`, `O`, `U`, `X`, `Z`. (Some sources include `U` and `O` as the 21st and
22nd "non-standard" amino acids — selenocysteine and pyrrolysine — but they
appear in only a handful of proteins and we will ignore them.)

This text representation is what makes machine learning on proteins look so
much like machine learning on natural language. Everything from BLAST to
ESM-2 to AlphaFold2's MSA stack ultimately operates on these strings.

## The chemistry in one picture

Every amino acid shares the same backbone:

```text
        H
        |
  H2N — Cα — COOH
        |
        R
```

- `H2N–` is an **amino group** (basic).
- `–COOH` is a **carboxylic acid** (acidic).
- The central carbon is the **alpha carbon** (`Cα`).
- The **side chain** `R` is what makes the 20 amino acids different.

When two amino acids link, the carboxyl `–COOH` of one reacts with the amino
`H2N–` of the next, losing a water molecule and forming a **peptide bond**.
A chain of these linked amino acids is a **polypeptide**, and once it has a
stable folded structure, it's a **protein**.

Once bonded into a chain, each individual amino acid is called a **residue**.
You will see this word everywhere in the rest of the course — "residue 47 of
the chain", "co-evolving residues", "per-residue embedding". It just means
"one amino acid in its place inside the chain".

## What the 20 side chains buy you

The side chain `R` is where all the personality lives. The 20 standard amino
acids cover a wide range of chemical behaviour with surprisingly few atoms:

| Property | Typical letters | Why it matters |
|---|---|---|
| Hydrophobic (greasy) | `A V L I M F W` | Buried in the protein core, away from water |
| Polar (water-loving) | `S T N Q Y` | Form hydrogen bonds on the surface |
| Positively charged | `K R H` | Salt bridges, DNA binding |
| Negatively charged | `D E` | Salt bridges, active-site acids |
| Special structure-formers | `G P C` | Glycine bends, proline kinks, cysteine bridges |

Three of those special cases are worth remembering because they break the
"every residue is the same except for R" pattern:

- **Glycine (`G`)** has *no* side chain. Just a hydrogen. This makes it the
  most flexible amino acid — it can sit in tight turns that no other residue
  can fit into.
- **Proline (`P`)** has a side chain that loops back and bonds to its own
  backbone nitrogen. This makes it the *least* flexible amino acid — it kinks
  the chain into a fixed angle, often breaking helices.
- **Cysteine (`C`)** has a thiol (`–SH`) side chain that can form a covalent
  **disulfide bond** with another cysteine. These bonds act like staples that
  pin distant parts of the chain together.

Most of what a protein language model "learns" is the statistical pattern of
which side chains tend to appear in which contexts. The biochemistry above is
the underlying reason those patterns exist.

## The hydrophobicity rule

If you only remember one thing from biochemistry for the rest of this course,
remember this: **water hates grease**.

Proteins fold in water. The hydrophobic side chains (`A V L I M F W`) cluster
together in the **core** of the folded protein where they are shielded from
water. The polar and charged side chains line the **surface**, where they
interact with the surrounding water and other molecules.

This single thermodynamic preference is the dominant driving force of protein
folding. Almost every other detail — hydrogen bonds, salt bridges, packing —
is fine-tuning on top of it. We'll come back to it in module 3 when we look at
folding thermodynamics.

## A quick worked example: reading a sequence

Take a tiny fragment of myoglobin:

```text
M K T A Y G L S E R N
```

What can we already say just from the letters?

- `M` (methionine, hydrophobic) — start codon, very common as residue 1.
- `K` (lysine, positively charged) — likely on the surface.
- `T` (threonine, polar) — surface, can hydrogen-bond.
- `A` (alanine, small hydrophobic) — happy on the surface or buried.
- `Y G L` — aromatic / flexible / hydrophobic.
- `S E R` — polar / negative / positive — almost certainly all on the surface.
- `N` (asparagine, polar) — surface, hydrogen-bonds.

That's already a structural hypothesis from text alone. A protein language
model is just a *much* more sophisticated version of this kind of reasoning,
trained on hundreds of millions of sequences.

## Recap

- Proteins are chains built from a fixed alphabet of **20 standard amino
  acids**, represented by 20 letters.
- Every amino acid shares the same backbone; the **side chain** is what
  varies.
- Side chains range from hydrophobic to polar to charged, plus three special
  cases (`G`, `P`, `C`).
- **Hydrophobic side chains cluster in the core; polar and charged side
  chains line the surface.** This is the dominant force in folding.
- Linked amino acids are called **residues**.

In the next module we'll see what happens when those residues bond into a
chain and start folding into shapes.
