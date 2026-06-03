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

For structure prediction, packing is more delicate. A pair representation for a
packed sequence would include residue pairs from different examples unless the
model is explicitly designed to mask or ignore them. Chain boundaries,
stoichiometry, templates, ligands, and geometry modules all add constraints.

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

The hard part is false negatives. If the cheap screen throws away rare but
valuable proteins, the expensive model never gets a chance to recover them.
Systems optimization and assay design are coupled.

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
