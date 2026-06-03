## Mini-model: capex discipline

For a foundry, the core return question is:

$$
\text{return on capacity} =
\frac{\text{wafer price} \times \text{utilization} \times \text{yield} - \text{operating cost}}
{\text{capital invested}}
$$

This is why utilization matters so much. A tool with low utilization still
depreciates.

## Decompose the revenue engine

A useful TSMC model has at least four blocks:

$$
\text{revenue} =
\text{wafer volume} \times \text{wafer ASP}
+ \text{advanced packaging}
+ \text{specialty/mature-node services}
+ \text{other services}
$$

The exact company reporting lines will not always match this simplified model,
but the decomposition keeps the analyst honest. A wafer shortage, a CoWoS
shortage, and a smartphone inventory correction have different margin and capex
implications.

## Utilization and depreciation intuition

High fixed-cost manufacturing creates operating leverage in both directions:

$$
\text{gross margin} \approx
\frac{\text{revenue} - \text{variable cost} - \text{depreciation} - \text{fab overhead}}
{\text{revenue}}
$$

If utilization rises, the same fab overhead is spread across more wafers. If a
new fab ramps slowly, depreciation can rise before revenue catches up. That is
why a company can be strategically right and still show near-term margin
pressure.

## Packaging as a second bottleneck

Advanced packaging adds a second capacity curve:

$$
\text{shipments} \leq
\min(\text{usable wafers}, \text{HBM stacks}, \text{CoWoS slots}, \text{substrates}, \text{test capacity})
$$

This equation is not a literal production formula. It is a reminder that the
most constrained input controls the shipment rate. For AI accelerators, that
constraint may sit outside front-end lithography.

## Why customer diversity helps

TSMC serves smartphones, CPUs, GPUs, ASICs, networking, automotive, IoT, and
specialty markets. Diversity helps smooth cycles, but leading-edge capacity can
still become concentrated around a few large customers.

Customer diversity is strongest when it is diverse by:

- End market.
- Architecture.
- Node.
- Package type.
- Product launch timing.
- Balance sheet strength.

A foundry with ten customers on the same AI cycle is less diversified than it
looks.

## What "node leadership" means commercially

Node leadership matters only if customers can use it profitably. That requires
PDKs, IP, EDA flows, design rules, yield, packaging, and enough volume capacity.
The node is the headline; the platform is what customers buy.

The commercial test is:

1. Do customers tape out their most valuable products?
2. Do yields ramp fast enough for product windows?
3. Is there enough packaging and test capacity to ship finished systems?
4. Does the node improve performance per watt enough to justify wafer price?
5. Does TSMC keep enough economics after sharing value with customers and
   absorbing capex?

## Source-aware caveat

Company reports are excellent for verified history and management framing. They
are weaker for bottleneck quantification. When management says packaging
capacity is expanding, avoid assuming exact wafer-equivalent output, customer
allocation, or lead-time normalization unless those facts are separately
sourced.
