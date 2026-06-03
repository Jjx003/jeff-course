## Resolution intuition

A simplified lithography resolution relationship is:

$$
\text{minimum feature} \approx k_1 \frac{\lambda}{NA}
$$

where $\lambda$ is wavelength, $NA$ is numerical aperture, and $k_1$ represents
process and imaging tricks. Smaller wavelength, higher numerical aperture, and
better process control can print smaller features.

This formula is not a complete manufacturing model, but it explains why EUV's
13.5 nm wavelength matters and why high-NA EUV is an important next step.
Concretely, current production EUV scanners (the TWINSCAN NXE series) have a
numerical aperture of about 0.33, while high-NA EUV (the EXE series) raises $NA$
to about 0.55. A higher $NA$ shrinks the achievable feature size for the same
wavelength and $k_1$, at the cost of a smaller printable field, which is one
reason high-NA tools change reticle and stitching strategy as well as
resolution.

## Throughput and critical layers

Not every layer needs the most advanced scanner. A chip may use EUV for the
most critical dense layers and DUV for many others. Capacity analysis therefore
needs a layer mix:

$$
\text{scanner demand} =
\sum_{\text{layers}} \text{wafers} \times \text{exposures per wafer per layer}
$$

Multi-patterning increases exposures per wafer. EUV can reduce exposure count
on some layers, but EUV tools are expensive and have their own throughput and
availability constraints.

## Reticle limits and chiplets

A lithography scanner exposes a maximum field size. Very large monolithic dies
run into this reticle limit and are also harder to yield because area is large.
Chiplets split a system across multiple smaller dies, then reconnect them in an
advanced package.

Chiplets do not remove complexity. They move some complexity from wafer
fabrication into packaging, interconnect, testing, and software-visible system
architecture.

## Node labels as product generations

Treat node names as foundry product generations. A node bundles:

- Transistor architecture and device improvements.
- Metal stack and design rules.
- Density, power, and performance targets.
- Mask requirements and process assumptions.
- Yield learning and customer enablement.

The label may be marketing-ish, but the generation is real.
