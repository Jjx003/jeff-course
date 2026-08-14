# Deeper theory: diagnostic information and redundancy

Bayes' rule separates how common a defect was before the clue from how characteristic
the clue is:

$$P(D\mid E)=\frac{P(E\mid D)P(D)}{P(E\mid D)P(D)+P(E\mid \neg D)P(\neg D)}.$$

Here $D$ means the defect is present, $E$ is the observed evidence, $P(D)$ is the
prior probability, and $P(D\mid E)$ is the updated probability after observing
the evidence. A rare diagnosis becomes plausible when early onset, family structure, a distinctive
organism, and a matching functional assay each contribute information. Avoid counting
correlated clues twice: "opportunistic infection" and "Pneumocystis pneumonia" are
not independent pieces of evidence.

## Choose the test that splits the tree

The expected value of a test depends on whether its possible results change action.
A broad genetic panel may eventually identify a cause, but an absolute lymphocyte
count and T/B/NK flow panel can immediately identify a dangerous combined defect and
alter isolation, transfusion, live-vaccine, and treatment decisions.

| Question | High-information test | Low-information substitute |
|---|---|---|
| are neutrophils present? | CBC with differential | total white count alone |
| can neutrophils oxidize? | stimulated DHR assay | neutrophil count |
| can B cells make specific antibody? | pre/post vaccine titers | B-cell count alone |
| where is complement interrupted? | paired CH50/AH50 | C3 alone |
| is new T-cell output low? | age-aware TREC screen/subsets | total lymphocytes alone |

## Redundancy hides defects until context changes

Immune pathways overlap. A partial defect may be silent until pathogen burden rises,
anatomy is damaged, or a drug removes a compensating pathway. Conversely, a dramatic
laboratory abnormality can have modest clinical effect when parallel defenses remain.

This is why longitudinal phenotype and functional challenge often outperform one
static measurement. The immune system is a network under load, not a collection of
independent reference ranges.

## Correction does not rewind damage

Gene addition, editing, enzyme replacement, or stem-cell transplantation can repair
the causal immune defect while bronchiectasis, liver injury, chronic viral infection,
or altered tissue niches persist. Trials should separately measure molecular
correction, lineage reconstitution, immune function, infection burden, and existing
organ damage.
