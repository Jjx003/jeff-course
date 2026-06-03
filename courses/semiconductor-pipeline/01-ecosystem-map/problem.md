## The chip industry is a relay race

When people talk about "semiconductors," they often sound as if one company
simply decides to make a chip and then chips appear. The real industry is more
like a relay race with specialized runners. A leading AI accelerator may need
architecture work in California, EDA software from another vendor, IP blocks
from a third, wafers processed in Taiwan, memory from Korea, packaging capacity
from an advanced assembly line, and cloud buyers who reserve a large share of
the finished supply before consumers ever see it.

![Semiconductor value chain](/courses/semiconductor-pipeline/semiconductor-value-chain.png)

*A simplified map of the semiconductor value chain. SemiAnalysis-style work often
starts by locating which box owns the scarce capacity, pricing power, or
technical know-how in a given cycle.*

This module gives you the map. Later modules zoom into the fab, yield, process
nodes, and packaging bottlenecks.

## The main roles

**Fabless design companies** design chips but do not own the main wafer fabs.
NVIDIA, AMD, Qualcomm, Broadcom, and many custom-silicon teams at cloud
companies fit this model. Their scarce resources are architecture, software
ecosystems, customer relationships, and the ability to reserve enough foundry,
memory, and packaging supply.

**IDMs** (integrated device manufacturers) design and manufacture chips inside
one corporate umbrella. Intel, Samsung, Texas Instruments, Micron, and SK hynix
are examples, though the exact mix differs by product line. An IDM can tune
process technology and product design together, but it also carries the capital
burden of factories.

**Foundries** manufacture wafers for other companies. TSMC is the leading pure
play foundry at the advanced edge; Samsung Foundry and Intel Foundry also serve
external customers. Foundries sell process capability, manufacturing discipline,
capacity, and trust. A fabless company hands the foundry a design database; the
foundry returns tested wafers, not magic.

**OSATs** (outsourced semiconductor assembly and test) package, assemble, and
test chips after wafer fabrication. Traditional packaging can be relatively
simple. Advanced packaging, such as 2.5D interposers and chiplet integration,
is now a strategic constraint for AI accelerators because the package connects
large logic dies to high-bandwidth memory.

**EDA vendors** sell the software used to design and verify chips. Layout,
timing closure, power analysis, formal verification, simulation, and design rule
checking are all EDA-heavy. Synopsys, Cadence, and Siemens EDA matter because a
modern chip is too complex to design manually.

**IP vendors** sell reusable blocks: CPU cores, interconnects, memory
controllers, SerDes, PCIe, USB, security engines, and more. Arm is the famous
example, but the long tail is large. IP shortens design cycles and lets teams
focus on differentiated blocks.

**Equipment vendors** build the machines inside fabs: lithography scanners,
deposition tools, etchers, ion implanters, metrology systems, inspection
systems, cleaning tools, and testers. ASML is central in lithography, especially
EUV. Applied Materials, Lam Research, Tokyo Electron, KLA, and many others own
critical steps.

**Materials suppliers** provide wafers, photoresist, specialty gases, targets,
slurries, chemicals, masks, substrates, and packaging materials. A fab is not
only a building full of machines; it is also a controlled river of ultra-pure
inputs.

**Cloud and hyperscaler buyers** increasingly shape demand. Microsoft, Amazon,
Google, Meta, Oracle, xAI, and other infrastructure buyers do not merely buy
servers after the fact. They influence accelerator roadmaps, memory demand,
networking choices, rack power, and how much advanced packaging capacity gets
reserved.

## Why ecosystem literacy matters

SemiAnalysis-style semiconductor conversation usually asks: *where is the
constraint?* The answer might not be "NVIDIA cannot design enough GPUs." It
could be HBM supply, CoWoS-like advanced packaging, reticle-limited die size,
EUV scanner availability, substrates, cleanroom ramp rate, power delivery in
data centers, or enough qualified engineers to bring a new line to yield.

That is why the ecosystem map matters. Revenue and power often sit where a
scarce capability meets urgent demand. A company can be strategically important
even if it never sells a consumer-branded chip.

## Reading the map like an operator

When you see a semiconductor headline, try translating it into this chain:

1. Who designed the chip?
2. Which process node and foundry manufacture it?
3. Which memory, packaging, and substrates does it require?
4. Which tools and materials are hard to add quickly?
5. Who is buying the finished systems, and what alternatives do they have?

The best analysis usually avoids single-cause explanations. Chips are systems,
and the chip industry is a system of systems.

## Recap

You now have the vocabulary for the semiconductor value chain: fabless,
IDM, foundry, OSAT, EDA, IP, equipment, materials, and hyperscaler demand.
Next, we enter the fab and follow a wafer through the manufacturing loop.
