## The memory-distance problem

Moving data costs energy and time. The farther a bit travels, the more
capacitance it charges, the more repeaters it touches, and the more scheduling
complexity it creates. AI accelerators are built around this fact.

HBM improves the tradeoff by putting DRAM stacks close to the compute die and
using a very wide interface:

$$
\text{Bandwidth} = \text{transfers per second} \times \text{bits per transfer}
$$

Instead of pushing a narrow interface to extreme clock rates, HBM makes the
interface wide and nearby. The package is what makes that possible.

## Why yield is harder than it looks

Advanced packages combine several expensive components. If any critical piece
fails, the whole assembly may be lost or downgraded. A simple independent-yield
model shows the sensitivity:

$$
Y_\text{package} \approx Y_\text{logic} \times \prod_i Y_{\text{HBM}, i}
\times Y_\text{assembly}
$$

This formula is too simple for real manufacturing, but the intuition is right:
more components and more attach points create more opportunities for failure.
Good process control, known-good-die testing, and repair strategies are
therefore essential.

## Why substrates matter

The substrate is less glamorous than EUV or HBM, but it can still throttle
shipments. Large AI packages need substrates with:

- Many routing layers.
- Fine line/space capability.
- Low warpage despite large package size.
- Strong power delivery and signal integrity.
- Thermal and mechanical compatibility with the attached die.

Substrate vendors must qualify materials, build capacity, and tune yields. That
capacity does not appear instantly when GPU demand spikes.

## Packaging as a margin lever

Advanced packaging changes who captures value. If customers urgently need HBM
integration and only a few suppliers can provide qualified capacity, the
packaging provider has pricing power. If capacity catches up and the process
becomes standardized, margins can normalize.

This is the same economic pattern as wafer fabrication: scarce qualified
capacity plus high switching costs creates leverage.
