# Analysis preflight

- Write the deployment claim before choosing a split.
- Draw the nesting: cell -> sample -> patient -> site.
- Freeze preprocessing within training folds.
- Report prevalence, precision-recall, calibration, and confidence intervals.
- Compare against a cheap clinical baseline.
- Name the prospective action and perturbation.

## Red flags

Random cell-level cross-validation, outcome-confounded batches, post-treatment
features in a baseline model, unlabeled missingness, and external validation that
reuses the same institution are reasons to discount a headline metric.

Useful standards and data sources include AIRR Community, IEDB, VDJdb, and Human
Cell Atlas resources. Reproducing one published figure from processed data is a
better first exercise than running an opaque end-to-end pipeline.

