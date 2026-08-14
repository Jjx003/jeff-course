# Deeper theory: hierarchy, calibration, and leakage

For cell $i$ from patient $j$, a mixed model can separate patient variation:

$$y_{ij}=\beta_0+\beta_1 x_{ij}+u_j+\epsilon_{ij},\qquad u_j\sim N(0,\sigma_u^2).$$

$y_{ij}$ is the measured outcome for cell $i$ in patient $j$; $x_{ij}$ is a
cell-level predictor; $\beta_0$ and $\beta_1$ are the population intercept and
association; $u_j$ is a patient-specific shift; and $\epsilon_{ij}$ is remaining
cell-level variation. The final term states that patient shifts are modeled with
variance $\sigma_u^2$. This does not fix a three-patient study, but it makes the dependence explicit.
Biological replication comes from additional independent patients, not cells.

## Compositional coordinates

For two populations, a log-ratio such as

$$z=\log\frac{p_{T}}{p_{myeloid}}$$

where $p_T$ and $p_{myeloid}$ are the measured fractions of T cells and myeloid
cells in the same sample. The log-ratio $z$ compares their relative abundance and
can be more interpretable than testing each fraction independently. Zeros,
absolute abundance, and the chosen reference still require biological care.

## Calibration and utility

A model can rank patients well and still systematically predict probabilities
that are too high. Check calibration in the deployment population. Decision
curves compare the net value of model-guided action with treat-all and treat-none
strategies at clinically meaningful thresholds.

## Leakage audit

Fit normalization, feature selection, imputation, and batch correction inside
each training fold. Remove technical duplicates and near-homologs across folds.
Do not let post-treatment data enter a baseline predictor, even indirectly through
a label or feature-selection step.

## Causal bridge

An inferred ligand-receptor edge becomes credible through spatial proximity,
protein expression, receptor competence, perturbation, dose response, rescue,
and a downstream functional readout. Agreement among algorithms is not an
independent biological replication.
