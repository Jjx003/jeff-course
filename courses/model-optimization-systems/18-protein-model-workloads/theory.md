# Sequence length, pair memory, and pipeline cost

Protein workloads are dominated by shape. A sequence of length $L$ is not just
$L$ independent residues. Many structure models construct pair representations
indexed by residue pairs:

$$
z_{ij} \in \mathbb{R}^{d_\text{pair}}
$$

for residues $i$ and $j$. The memory for that representation scales like:

$$
O(L^2 d_\text{pair})
$$

Single-residue representations scale like:

$$
O(L d)
$$

The square term is the danger. Doubling the sequence length roughly quadruples
pair memory before you even account for atom features, templates, recycling, or
diffusion steps.

## Where the cubic term comes from

The pair representation is not just a feature map indexed by two residues; it is
supposed to be *geometrically consistent*. If residue $i$ is close to $k$ and
$k$ is close to $j$, that constrains the relationship between $i$ and $j$ — the
triangle inequality, in a learned form. Enforcing it requires every pair
$(i,j)$ to consult every third residue $k$, and that is where the exponent
comes from.

Two operation families in AlphaFold2's Evoformer do this:

$$
\text{triangular multiplicative update:}\quad
z_{ij} \leftarrow \sum_{k} a_{ik} \odot b_{jk}
$$

$$
\text{triangular self-attention:}\quad
z_{ij} \leftarrow \operatorname{attention over } k \text{ for fixed } i
$$

Both touch $L^2$ output pairs, each summing over $L$ intermediates, giving
$O(L^3 c)$. The full per-block accounting:

| Operation | Cost | Grows with |
|---|---|---|
| MSA row-wise attention (pair-biased) | $O(s L^2 c_m)$ | homologs × length² |
| MSA column-wise attention | $O(s^2 L c_m)$ | homologs² × length |
| Outer product mean (MSA → pair) | $O(s L^2 c)$ | homologs × length² |
| Triangular multiplicative update ×2 | $O(L^3 c_z)$ | **length³** |
| Triangular self-attention ×2 | $O(L^3 c_z)$ | **length³** |
| Transitions | $O(L^2 c)$ | length² |

Multiply by 48 blocks and by $N_r$ recycling iterations. The recycling factor is
easy to forget and it multiplies everything above it — a model run with 3
recycles does three times the trunk work of one run with 1, which makes
recycling count the single cheapest knob in the whole pipeline to experiment
with.

Memory tells the same story more sharply than FLOPs do. The pair representation
at $c_z = 128$ costs:

| $L$ | pair rep (FP32) | triangle attention logits, 4 heads, if materialized |
|---:|---:|---:|
| 384 | 75 MB | 0.9 GB |
| 1000 | 512 MB | 16 GB |
| 2000 | 2.0 GB | 128 GB |

The right column is why AlphaFold2-style models chunk their triangle operations
rather than computing them densely, and why long chains fail with out-of-memory
errors long before they get slow. It is the same structural problem as the
$L \times L$ attention matrix in module 9 — an intermediate that is large,
temporary, and quadratic or worse — met with the same family of answers.

AlphaFold3-style models change this profile without eliminating it. The heavy
MSA stack shrinks to a lighter module, the trunk becomes a pair-and-single
Pairformer, and a diffusion module generates atom coordinates directly over $T$
sampling steps. The triangle operations survive, so the $L^3$ term survives; what
changes is that a tunable $T$ now sits in front of the structure generator, and
sampling steps are a knob that can be traded against quality per request in a
way that trunk depth cannot.

## Three cost profiles

### 1. PLM embedding

A protein language model maps amino-acid tokens into representations. The
systems profile resembles a transformer encoder:

- attention cost grows with sequence length,
- padding waste can be large,
- batches can often be bucketed or packed,
- FlashAttention-style kernels can help,
- quantization may be possible if downstream quality survives.

This is the friendliest setting for the LLM optimization ideas in the course.

### 2. MSA-based folding

AlphaFold2-style folding adds a multiple sequence alignment:

$$
\text{MSA tensor shape} \approx N_\text{seq} \times L
$$

where $N_\text{seq}$ is the number of homologous sequences retained. It also
uses pair representations of shape roughly:

$$
L \times L \times d_\text{pair}
$$

The pipeline includes non-neural preprocessing: searching sequence databases,
building alignments, choosing templates, and featurizing the result. For a
single user request, that preprocessing can dominate wall-clock time. For a
large batch, caching MSAs and templates can matter more than shaving 5 percent
off a neural kernel.

### 3. All-atom complex prediction

AlphaFold3, Chai, and Boltz-style systems move beyond protein chains. Inputs may
include proteins, nucleic acids, ligands, ions, and modifications. The model has
to reason about chemical identity, atom geometry, chain interfaces, and
sometimes binding affinity.

The cost profile can include:

- token or atom features,
- pair features across molecules,
- diffusion or iterative refinement steps,
- confidence heads,
- affinity or ranking heads,
- optional constraints and templates.

This is not simply "longer text." The shape and meaning of the tensors have
changed.

## Padding and packing

If a batch of independent sequences is padded to the longest length, the padded
token count is:

$$
B \max_i L_i
$$

The useful token count is:

$$
\sum_i L_i
$$

The padding waste is:

$$
B \max_i L_i - \sum_i L_i
$$

For pure sequence embedding, packing multiple shorter proteins into one context
can replace padding tokens with real residues, provided the attention mask
prevents cross-sequence information flow.

This matters more for proteins than for text because the length distribution is
so much wider. Natural proteins run from tens of residues to several thousand,
and a batch drawn at random from UniRef can easily be 70 percent padding. The
same batch, packed, is under 5 percent.

### Packing is bin packing, and greedy is good enough

Filling fixed-capacity contexts with variable-length sequences is exactly the
classical **bin packing** problem, which is NP-hard. That sounds discouraging
until you look at the approximation bounds. Sorting sequences longest-first and
placing each into the first bin that fits — first-fit-decreasing — satisfies

$$
\text{FFD}(I) \le \frac{11}{9}\,\text{OPT}(I) + \frac{6}{9}
$$

Within about 22 percent of optimal in the worst case, and much closer than that
on realistic length distributions, for a sort and a linear scan. There is no
reason to reach for an integer program here; the practical work is elsewhere:

- **Masking.** Packed sequences must not attend across boundaries. The standard
  mechanism is a variable-length attention kernel taking cumulative sequence
  offsets, which computes block-diagonal attention without materializing a mask.
  Getting this wrong is silent — the model still produces embeddings, they are
  just contaminated by whichever neighbor shared the buffer.
- **Position indices.** Positions must restart at each boundary. Continuing the
  index across a boundary tells the model the second protein begins at residue
  512, which it does not.
- **Verification.** Because both failures above are silent, packing is a change
  you test numerically rather than review. The coding lab that follows checks a
  packed sequence's embeddings against the same sequence processed alone, which
  is the only assertion that actually catches a mask bug.

For structure prediction, packing is more delicate. A pair representation for a
packed sequence would include residue pairs from different examples unless the
model is explicitly designed to mask or ignore them. Chain boundaries,
stoichiometry, templates, ligands, and geometry modules all add constraints. And
because the pair tensor is $O(L^2)$, packing two proteins into one context
*quadruples* the pair memory rather than leaving it unchanged — packing is a
win for $O(L)$ representations and can be a loss for $O(L^2)$ ones.

## Cascades and verification

A practical biomolecular pipeline often looks like:

```mermaid
flowchart LR
    A["Many sequences or designs"] --> B["Cheap PLM score or embedding"]
    B --> C["Filter / cluster / diversify"]
    C --> D["Structure or complex prediction"]
    D --> E["Confidence, interface, or affinity ranking"]
    E --> F["Experimental candidates"]
```

This is the protein version of proposal plus verification. The cheap stage
should reduce the candidate set while preserving the biological signal. The
expensive stage should be reserved for candidates where geometry matters.

### The cascade has two numbers, and only one of them is recoverable

Give the screen two parameters: it retains a fraction $f$ of candidates and
costs $c_s$ per candidate relative to the expensive model's cost of 1. Then the
cost per original candidate is $c_s + f$ and the speedup is

$$
\text{speedup} = \frac{1}{c_s + f}
$$

This is structurally the same expression as the speculative-decoding speedup in
module 13, and it fails the same way: a screen that is not actually cheap
($c_s$ comparable to 1) buys nothing no matter how selective it is.

But the analogy breaks at the place that matters, and the break is the whole
point of this section. Speculative decoding is **lossless** — module 13 proved
that a bad draft costs time and nothing else. A screening cascade has no such
theorem. Introduce the screen's recall $r$, the fraction of true hits it
retains:

$$
\text{hits found} = r \times \text{hits the expensive model would have found}
$$

Errors in the two directions are not symmetric:

| Error | Cost | Recoverable? |
|---|---|---|
| False positive | one wasted expensive prediction | yes — the expensive model rejects it |
| False negative | a real hit never evaluated | **no** — nothing downstream can see it |

A false positive is a compute bill. A false negative is a molecule you will
never know you had. Nothing downstream can recover it, because the expensive
model is never shown the candidate, and the experimental campaign is never shown
the prediction.

That asymmetry should determine how the screen is tuned, and it usually does
not. Screens get selected by accuracy, AUC, or F1 — metrics that weight the two
error types roughly equally. The right objective is **maximum recall at the
retention rate your compute budget allows**. Concretely: 100,000 candidates,
a 0.1 percent hit rate, a screen that keeps 1 percent at recall 0.8. You spend
about 1 percent of the full-folding cost and find 80 of the 100 real hits. Then
ask the question the metric cannot answer for you — is finding 80 of 100 a
success or a failure? For "we need one viable binder," it is a success. For
"characterize this target's binding landscape," 20 unexamined true positives may
invalidate the conclusion.

Systems optimization and assay design are coupled, and this is where they touch.
The engineer picks $f$ and $c_s$; the biologist has to live with $r$. Those
numbers belong in the same conversation.

## Validation caveats

Protein benchmarks can leak in subtle ways:

- homologous proteins can appear across train and test splits,
- structures from the same family can make a "new" target familiar,
- ligand benchmarks can overrepresent common scaffolds,
- mutation datasets can reflect assay noise or expression artifacts,
- temporal splits are harder but often more honest.

When a paper or internal benchmark claims a large speed or quality win, ask what
was held out. Sequence identity splits, target-family splits, scaffold splits,
and time splits answer different questions.

## Going deeper

- ESMFold paper: https://www.science.org/doi/10.1126/science.ade2574
- AlphaFold 3: https://www.nature.com/articles/s41586-024-07487-w
- Chai-1 technical report: https://chaiassets.com/chai-1/paper/technical_report_v1.pdf
- Boltz-2: https://pmc.ncbi.nlm.nih.gov/articles/PMC12262699/
- Efficient PLM inference and fine-tuning: https://www.sciencedirect.com/science/article/pii/S2589004225017560
- AlphaFold2 and the Evoformer, where the triangle operations are defined: https://www.nature.com/articles/s41586-021-03819-2
- ESM-2 and ESMFold, single-sequence structure prediction at scale: https://www.science.org/doi/10.1126/science.ade2574
- FlashAttention variable-length API, the mechanism packing relies on: https://github.com/Dao-AILab/flash-attention
- Tight bound on first-fit-decreasing for bin packing (Dosa): https://doi.org/10.1007/978-3-540-74450-4_1
