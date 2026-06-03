## Bottleneck math

A finished accelerator shipment is a serial process. If each required stage has
available capacity $C_i$, the system output is capped by the smallest effective
capacity:

$$
C_\text{system} \le \min_i C_i
$$

The equality is too clean for reality because buffers, yield, mix, and rework
matter. But the intuition is essential: excess capacity in non-bottleneck steps
does not raise final output.

## Lead-time asymmetry

Demand can change faster than capacity. A model release, cloud capex cycle, or
export-control deadline can move orders in weeks. New semiconductor capacity may
need quarters or years because it requires:

- Tool ordering and installation.
- Cleanroom buildout.
- Process qualification.
- Customer qualification.
- Reliability testing.
- Yield learning.
- Supplier capacity upstream of the supplier.

The gap between demand speed and capacity speed is where shortages and pricing
power appear.

## Substitutability

Substitutability is the release valve. A bottleneck with easy substitutes has
limited pricing power. A bottleneck with no qualified substitute can dominate
the chain.

Examples:

- A mature-node microcontroller may be redesigned across foundries if volumes
  justify the work.
- A leading-edge AI accelerator cannot casually move from one advanced package
  flow to another after tapeout.
- A model can sometimes be quantized to fit less HBM, but only if accuracy,
  latency, and software constraints allow it.

## Pricing power

Scarcity rent accrues where three things meet:

1. Demand is urgent.
2. Supply is qualified and limited.
3. Switching costs are high.

This can describe a foundry node, an HBM generation, an advanced package line,
a substrate vendor, or a piece of design IP. The glamorous part of the chip is
not always the part with the best near-term pricing power.
