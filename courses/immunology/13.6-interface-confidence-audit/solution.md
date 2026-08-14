# Walkthrough

The reference solution separates geometry, confidence, ranking, and reporting.
That separation mirrors the scientific reasoning: first identify a possible
interface, then ask which parts of it are supported, then choose perturbations.

`find_contacts` compares only `H` with `A`, so each pair is generated once. The
supported list requires both local confidence scores to pass the threshold. Only
that list contributes to hotspot counts.

The two top residues tie. Reporting both is more honest than inventing a ranking
from uncertain contacts or amino-acid identity. The final interpretation remains
narrow: these are mutation priorities, not proven energetic hotspots or escape
sites.
