## What an MSA actually is

A **multiple sequence alignment (MSA)** is a stack of sequences, all
padded with gap symbols (`-`) so that every sequence has the same length
and homologous positions sit in the same column. The output is a
2-D matrix:

```text
        col 0   col 1   col 2   ...   col L-1
seq 1   V       L       S       ...   H
seq 2   V       L       S       ...   H
seq 3   M       G       L       ...   H
...
seq N   V       E       K       ...   Y
```

Where pairwise alignment (module 6) lines up *two* sequences, an MSA
lines up *many* — usually hundreds to thousands of homologs of one
"query" protein. Building one is a non-trivial dynamic-programming
exercise that takes minutes to hours on real-world databases. We won't
build an MSA from scratch in this course; we'll consume pre-built ones.

Tools you'll see in the wild:

- **HHblits** — iterative profile-HMM search against the UniRef HMM
  database. Slow but high-recall.
- **jackhmmer** — iterative HMM search from HMMER. AlphaFold2's MSA
  pipeline used jackhmmer for a long time.
- **MMseqs2** — much faster alignment over big databases. ColabFold's
  MSA service is built on it.

A real-world MSA for AlphaFold2 might be a $10{,}000 \times 400$ matrix
of one query sequence plus 9,999 homologs spanning hundreds of millions
of years of evolution.

## Two conservation scores

The two most common ways to score "how conserved is this column":

### Frequency of the most common residue

The simplest score:

$$f_i = \max_a \frac{n_{a,i}}{N}$$

where $n_{a,i}$ is the number of sequences with residue $a$ at column
$i$, and $N$ is the number of sequences in the MSA. $f_i = 1$ means
"every sequence agrees"; $f_i = 1/N$ means "every sequence has a
different residue".

### Shannon entropy

Information-theoretic and what almost every published method uses:

$$H_i = -\sum_a p_{a,i} \, \log_2 p_{a,i}, \qquad p_{a,i} = \frac{n_{a,i}}{N}$$

Units of $H_i$ depend on the log base — `log_2` gives **bits**, `log` (natural) gives **nats**. In bioinformatics, bits are standard.

For protein MSAs, $H_i$ ranges from $0$ (perfect conservation) to
$\log_2 20 \approx 4.32$ (uniform over all 20 amino acids). The maximum
is rarely seen in real data because amino-acid distributions are
non-uniform even at random sites.

A common visualisation is the **information content** $\log_2 20 - H_i$,
typically plotted as a **sequence logo** (Schneider & Stephens 1990) —
a stacked-letter plot where letter heights are proportional to
information content. You've seen these in every protein-domain paper
ever written.

## What about gaps?

Real MSAs are full of gap columns. Three reasonable strategies:

1. **Skip gaps.** Compute entropy only over the residues actually
   present. Best when gaps are rare.
2. **Treat `-` as a 21st symbol.** A column that is mostly gaps becomes
   highly conserved as "this position usually doesn't exist". Useful
   for some structural inference tasks.
3. **Reweight by sequence weights.** When the MSA has many near-duplicate
   sequences (a common situation if one species has been heavily
   sampled), down-weight the duplicates so they don't dominate the
   statistics. This is what serious tools like GREMLIN do.

Our toy MSA in this exercise has no gaps, so we use strategy 1
implicitly — the `Counter` only sees actual residues.

## Conservation $\Leftrightarrow$ structural / functional importance

The single most valuable biological intuition:

> **Conserved columns are conserved for a reason.**

Evolution preserves residues that are doing something important.
Examples:

- **Active-site residues.** The catalytic Asp-His-Ser triad of serine
  proteases is essentially invariant across the entire protease
  superfamily. Mutate any of the three and the enzyme stops working.
- **Buried hydrophobic core.** Mutating an `L` to `K` in the protein
  core typically destroys folding. Surface residues, by contrast, can
  often tolerate substantial substitution.
- **Disulfide bridges.** The two cysteines of a disulfide bond *both*
  show up as conserved Cs in the MSA — an experimentalist trick is to
  scan an MSA for paired conserved Cs as a structural fingerprint.

The flipside: **variable columns are variable for a reason too.** They're
typically surface loops where amino-acid identity doesn't matter much,
or specificity-determining residues where different family members
evolved different functions.

## Co-evolution: the next layer up

Single-column conservation tells you which positions matter on their
own. But there's a richer signal hiding in *pairs* of columns: residues
that change together. If column $i$ and column $j$ are physically in
contact in the folded protein, then a mutation at $i$ that disrupts the
contact tends to be compensated by a co-occurring mutation at $j$.
Statistically, $i$ and $j$ "co-evolve".

You can detect this by computing the **mutual information** of column
pairs:

$$I(i, j) = \sum_{a, b} p_{ab,ij} \, \log_2 \frac{p_{ab,ij}}{p_{a,i}\, p_{b,j}}$$

High $I(i,j)$ means columns $i$ and $j$ are not independent — and
therefore likely in contact. This is the foundation of pre-AlphaFold
contact predictors like **EVfold**, **PSICOV**, **GREMLIN**, and **DCA**.

AlphaFold2's MSA stack (module 15) and outer-product-mean operation
(module 16) are direct descendants of these co-evolution methods,
extended to a learned end-to-end neural network.

## Why this all matters for ML

Three things to take away into the rest of the course:

1. **PLMs are MSA replacements.** The whole point of ESM-2 and ESMFold
   (modules 11-17) is that a protein language model's weights, trained
   on hundreds of millions of sequences, *implicitly* contain the same
   conservation and co-evolution signal you'd get from running an
   explicit MSA — without the slow database search at inference time.
2. **MSA-based fine-tuning ("evotuning") still helps.** Even with a
   trained PLM, fitting it to a *specific* protein family's MSA can
   improve downstream task accuracy. Module 22 (Cradle / Magnus Ross
   blog) covers this.
3. **Conservation is a useful prior for design.** When you're designing
   a new protein, you usually want to leave conserved positions alone
   (they're conserved for a reason) and explore variation at the
   variable positions. Module 21 (ProteinMPNN) and module 22 use this
   intuition heavily.
