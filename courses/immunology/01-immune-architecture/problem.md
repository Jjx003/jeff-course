# Immune architecture: solving a search problem

At 8:10 a.m., a wood splinter pushes *Staphylococcus aureus* into a fingertip.
The first bacterium is millimeters from a tissue macrophage but centimeters
from the nearest naive T cell that can recognize one of its peptides. By lunch,
neutrophils are entering the finger. Several days later, clonally expanded
lymphocytes and antibody return through the blood.

Immunity works because anatomy turns those separated events into one circuit.

![Diagram tracing antigen and cell traffic from an infected fingertip through a draining lymph node and back to tissue](/courses/immunology/foundations-01-search-circuit.svg)

*Antigen and dendritic cells travel from tissue to a draining node through
afferent lymphatics. Naive lymphocytes mostly enter the node from blood, while
activated cells leave through efferent lymph and later return to tissue.*

## The five coordinates used throughout the course

Every later module revisits the same five questions:

1. **Recognition:** what molecular feature is detected, and by which receptor?
2. **Context:** which activating, inhibitory, metabolic, or damage signals alter the response?
3. **Compartment:** where are antigen, responding cells, and vulnerable tissue?
4. **Time:** what happens first, what persists, and what changes on re-exposure or treatment?
5. **Control:** which brake, feedback loop, or intervention limits the response?

These are not five independent facts. A receptor can be protective in one tissue
and pathogenic in another; the same signal can help early and harm late. Use the
coordinates to keep the mechanism attached to place and time.

## Learning objectives

By the end, you should be able to:

- trace antigen, dendritic cells, naive lymphocytes, and effectors through the
  correct vessels;
- explain why marrow and thymus are **primary** lymphoid organs;
- distinguish a cell's lineage from its current state and location;
- estimate how organized scanning changes the probability of a rare encounter;
- predict which compartment is most affected by an anatomical defect.

## A quantitative thread for the course

This course uses a small set of quantitative models repeatedly. They are not
extra facts to memorize. Each model answers one biological question:

| Question | First model | Where it returns |
|---|---|---|
| Will rare partners meet? | encounter probability | lymph nodes, repertoire screens, spatial tumors |
| Will a cell act? | activating inputs minus inhibitory inputs | innate cells, T-cell priming, tolerance, checkpoints, cell therapy |
| How does a population change? | growth minus loss | clonal expansion, memory, tumor escape, living drugs |
| How should evidence change belief? | base rates plus test performance | autoantibodies, allergy, immunodeficiency, predictive models |

For every equation, ask what the variables mean, what changes them biologically,
and which assumptions make the model fail. If an equation does not improve a
prediction, comparison, or experimental design, the prose should do the work.

## Begin with compartments, not a cell catalog

| Compartment | What arrives | What leaves | Main design problem |
|---|---|---|---|
| Barrier tissue | microbes, resident sentinels, blood leukocytes | antigen, dendritic cells, debris | detect and contain locally |
| Draining lymph node | afferent lymph, antigen, dendritic cells, naive lymphocytes | activated clones, antibody | match rare antigen to rare receptor |
| Spleen | blood-borne antigen and cells | activated cells and antibody | survey the blood |
| Bone marrow | stem and progenitor cells | most blood-cell precursors | renew lineages; develop B cells |
| Thymus | T-cell precursors | selected naive T cells | build a useful, restrained T-cell pool |

The spleen and a lymph node are not interchangeable. An encapsulated bacterium
in blood is routed to the spleen; antigen from a toe wound reaches a draining
lymph node. Asking "where did the antigen enter?" is often more useful than
asking "which immune cell is strongest?"

![Low-magnification lymph-node histology showing a capsule, pale follicles, and darker intervening lymphoid tissue](/courses/immunology/architecture-lymph-node-histology.jpg)

*Low-power H&E of a normal lymph node. The pink capsule surrounds a pale
subcapsular sinus and densely basophilic lymphoid tissue. In pathology, the
first question is whether this normal architecture is preserved or effaced.*

## The fingertip case, frame by frame

1. **Minutes:** keratinocytes, mast cells, macrophages, and other resident cells
   detect damage and microbial products.
2. **Hours:** local endothelium becomes adhesive. Neutrophils leave nearby
   venules; plasma proteins enter the tissue.
3. **Hours to a day:** soluble antigen drains, while activated dendritic cells
   migrate, through afferent lymphatics.
4. **In the node:** dendritic cells display peptide-MHC in the T-cell zone. B
   cells sample intact antigen in follicles. Naive lymphocytes continuously
   recirculate through this organized space.
5. **Days:** selected clones divide and change homing programs. They exit by
   efferent lymph, cross the thoracic duct into blood, and reach inflamed tissue.

Notice the asymmetry: naive cells mostly search secondary lymphoid organs;
effector cells are licensed to enter inflamed peripheral tissue.

## A rare-cell calculation

Suppose one relevant naive T cell occurs per $10^5$ naive T cells. A node lets a
dendritic cell make productive contacts with roughly $5{,}000$ distinct naive T
cells over a period of scanning. In a deliberately simple independent-sampling
model, let $f=10^{-5}$ be the fraction of naive T cells that match and let
$n=5{,}000$ be the number of distinct cells sampled. Then

$$
P(\text{at least one matching T cell}) = 1-(1-10^{-5})^{5000} \approx 0.049.
$$

One dendritic cell is not enough for reliability. Ten antigen-bearing dendritic
cells sampling nonidentical cells raise the effective sample to $50{,}000$:

$$
P \approx 1-(1-10^{-5})^{50000} \approx 0.39.
$$

The exact numbers vary and contacts are not independent. The useful conclusion
is architectural: concentrating many presenters and recirculating many rare
clones changes encounter probability by orders of magnitude.

## Lineage is not destiny

A lineage diagram answers "where did this cell develop?" It does not fully
answer "what is it doing now?" A lung alveolar macrophage and a recently
recruited inflammatory monocyte can both phagocytose, yet differ in origin,
signals, lifespan, and repair functions. Naive, effector, central-memory, and
tissue-resident T cells can share one rearranged receptor while occupying
different physiological states.

Use four labels when describing a cell:

1. lineage;
2. developmental or activation state;
3. anatomical location;
4. current input and output.

## Data interpretation: where is the broken link?

A mouse strain has normal marrow cell counts, normal thymic T-cell output, and
normal neutrophil killing in a dish. After a skin infection, however, its
dendritic cells remain near the wound. The draining node contains little
microbial peptide-MHC and antigen-specific T cells do not expand.

Before reading on, decide which observations argue against a defect in:

- receptor generation;
- neutrophil microbicidal machinery;
- T-cell development;
- dendritic-cell migration or lymphatic entry.

The last explanation fits all four observations. The experiment is a reminder
that a normal cell can fail as part of a broken route.

## Clonal selection in one sentence

Receptor diversity is generated before this infection; antigen plus context
selects rare pre-existing clones; their descendants preserve specificity while
changing number, state, and location.

That mechanism creates both coverage and danger. Random receptor generation
inevitably makes some self-reactive clones, so selection and peripheral
regulation are part of the architecture, not later accessories.

## Check yourself

1. Why does lymph from a finger enter a node before returning to blood?
2. Why would removal of the spleen particularly impair defense against some
   blood-borne encapsulated bacteria?
3. In the probability model, which biological changes increase the effective
   sample size $n$?
4. A tissue biopsy contains many T cells. What four labels are needed before
   calling them protective effectors?

## Recap

- Barriers detect locally; lymphoid organs organize rare encounters.
- Afferent lymph enters a node; efferent lymph carries activated cells away.
- Marrow and thymus generate and select cells; nodes and spleen activate them.
- Anatomy changes the probability and control of recognition.
- Cell identity is lineage plus state, location, and current signals.
