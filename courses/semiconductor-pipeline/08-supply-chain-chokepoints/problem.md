## Chokepoints are where time, uniqueness, and demand collide

A semiconductor supply chain is not constrained by "capacity" in the abstract.
It is constrained by specific tools, materials, skills, facilities, and
qualified process flows. The useful question is not "is there enough supply?"
It is:

> Which non-substitutable step has the longest lead time and the most urgent
> incremental demand?

That framing turns a messy ecosystem into a bottleneck map.

## A practical chokepoint checklist

For each suspected bottleneck, score five properties:

| Property | Question |
|---|---|
| Bottleneck | What exact step blocks finished shipments? |
| Lead time | How long does new qualified capacity take? |
| Substitutability | Can customers switch suppliers, nodes, materials, or designs? |
| Pricing power | Who can charge more because the constraint is scarce? |
| Geopolitics | Is the constraint exposed to export controls or regional concentration? |

This is the operating version of a SemiAnalysis-style supply-chain note: name
the constraint, quantify the time lag, and identify who captures the scarcity
rent.

## EUV scanners

Extreme ultraviolet lithography scanners are among the clearest chokepoints in
the ecosystem. They are complex, expensive, slow to build, and supplied by a
tiny vendor base. Leading-edge logic depends on them for the most advanced
layers.

- **Bottleneck:** scanner output, installation, service, and process maturity.
- **Lead time:** long, because tools require specialized components and field
  qualification.
- **Substitutability:** low for leading-edge layers. Multipatterning with older
  tools can help in some cases but usually costs cycle time, complexity, and
  yield.
- **Pricing power:** strong for the tool supplier and for fabs that already own
  qualified EUV capacity.
- **Geopolitics:** high, because access to EUV is a central export-control
  lever.

## HBM

High-bandwidth memory is a chokepoint because AI accelerators need both
bandwidth and capacity near the compute die. HBM supply depends on advanced DRAM
processes, TSV stacking, test, and tight coordination with packaging.

- **Bottleneck:** qualified HBM stacks of the right generation and capacity.
- **Lead time:** medium to long, especially when demand shifts to newer stack
  heights or faster interfaces.
- **Substitutability:** limited. GDDR or DDR can be cheaper but cannot match the
  same package-local bandwidth and energy profile.
- **Pricing power:** strong when AI demand exceeds available stacks.
- **Geopolitics:** meaningful because memory manufacturing is geographically
  concentrated.

## CoWoS and advanced packaging

Advanced packaging is where many AI accelerators become real products. Even if
the logic die and HBM stacks exist, they must be assembled with high yield into
large packages.

- **Bottleneck:** interposer or bridge capacity, HBM attach, substrate supply,
  thermal-mechanical yield, and final test.
- **Lead time:** long enough that sudden accelerator demand can outrun expansion
  plans.
- **Substitutability:** low for designs already built around a specific package.
  Redesigning the memory interface or package floorplan is not a quick swap.
- **Pricing power:** strong for qualified advanced-packaging providers and
  substrate suppliers.
- **Geopolitics:** high because capacity is concentrated in a small number of
  regions and firms.

## Substrates

Large AI packages need high-end organic substrates. They are easy to overlook
because they are less famous than EUV scanners or HBM stacks, but they can block
shipments just as effectively.

The hard parts are fine routing, layer count, warpage control, power delivery,
and yield at large package sizes. A substrate shortage can make every upstream
step look healthy while finished accelerator output remains capped.

## EDA and IP

Electronic design automation tools and reusable IP blocks are chokepoints of
knowledge and verification rather than physical throughput.

Modern chips depend on synthesis, place-and-route, timing closure, verification,
signoff, memory compilers, SerDes, PCIe, HBM controllers, and security blocks.
There may be multiple vendors in some categories, but switching tools or IP
late in a program can invalidate months of work.

Export controls can therefore target design capability before any wafer is
started.

## Metrology, chemicals, and gases

Manufacturing also depends on less visible inputs:

- **Metrology and inspection** tools find defects and keep process windows
  under control.
- **Photoresists and specialty chemicals** determine patterning quality.
- **Industrial gases** such as neon, argon, hydrogen, and nitrogen support
  lithography, etch, deposition, and cleanroom operations.

These markets can be narrow. A shortage may not sound dramatic until it stops a
specific recipe at a specific layer.

## Geographic concentration and export controls

Semiconductor supply chains are globally distributed but locally concentrated.
One region may dominate leading-edge logic manufacturing, another memory, another
tool components, another substrates, and another final electronics assembly.

Export controls exploit this concentration. They do not need to block every
input; they only need to block the input that cannot be substituted in time.
That is why chokepoint analysis is geopolitical analysis.

## Recap

To analyze a semiconductor bottleneck, avoid vague claims about "shortages."
Name the constrained step, estimate how long capacity takes to qualify, ask what
customers can substitute, identify who gains pricing power, and map the
geopolitical exposure.

In AI hardware, the answer is often a stack of constraints rather than one
constraint: leading-edge wafers, HBM, advanced packaging, substrates, test,
networking, power, and data-center deployment all have to arrive together.
