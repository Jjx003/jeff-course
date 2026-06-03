# TSMC: the capacity allocator

TSMC is the central foundry case study because it sells scarce manufacturing
capability to the world's strongest chip designers. The SemiAnalysis-style
question is not simply "does TSMC have the best node?" It is:

> Which scarce step controls the customer's product revenue, and how much of
> that scarcity can TSMC convert into durable return on capital?

As of May 2026, TSMC's 2025 annual report says it generated US$122.42 billion
of consolidated revenue and US$55.21 billion of net income. The report also
says TSMC managed more than 17 million 12-inch-equivalent wafers of annual
capacity in 2025, 3nm was 24% of wafer revenue in its third year of volume
ramp, AI-related demand remained robust, and TSMC continued developing CoWoS,
InFO, SoIC, and photonics-related packaging technologies.

Those facts are useful, but they are only the first layer. A strong analyst
decomposes TSMC into several linked capacity markets:

- Leading-edge wafer starts.
- Mature and specialty wafer starts.
- Advanced packaging, especially CoWoS-class capacity for AI accelerators.
- Customer engineering support, masks, IP, process design kits, and yield
  learning.
- Geographic resilience capacity outside Taiwan.

## Controlled capability

TSMC controls:

- High-volume leading-edge logic manufacturing.
- Process design kits and customer enablement.
- Yield learning across many customers.
- Advanced packaging services such as CoWoS and SoIC.
- Capacity allocation across Apple, NVIDIA, AMD, Broadcom, Qualcomm, custom
  ASIC teams, and many others.

TSMC's power is not only that it has good process technology. It has process
technology at scale, with enough trust that customers tape out their most
important products to it.

## Wafer capacity is not packaging capacity

The first mistake is to treat all "capacity" as one pool. TSMC can have enough
wafer capacity for a chip and still be constrained by advanced packaging. For an
AI accelerator, revenue recognition for the customer may require:

1. A logic die on a leading-edge node.
2. HBM supply from memory vendors.
3. A silicon interposer or bridge architecture.
4. CoWoS or another advanced package.
5. Substrate, test, and final assembly.
6. Datacenter qualification by hyperscale buyers.

That means "NVIDIA wants more GPUs" does not translate one-for-one into "TSMC
needs only more 4nm wafers." The binding constraint can shift between wafers,
CoWoS, HBM, substrates, power delivery, networking, or customer datacenter
deployment speed.

**Concrete drill-down:** build a two-axis capacity map.

| Constraint | Evidence to collect | Thesis implication |
|---|---|---|
| Advanced wafer starts | Node revenue mix, capex, tool deliveries, customer tape-outs | Supports pricing and utilization if demand is broad |
| CoWoS / advanced packaging | Management commentary, packaging capex, OSAT partnerships, lead times | Can keep AI supply tight even when wafers improve |
| HBM | SK hynix/Samsung/Micron capex, qualification status, ASPs | Limits AI accelerator shipments outside TSMC's direct control |
| Substrate/test | ABF substrate commentary, test capacity, module yields | Can create less visible bottlenecks late in the flow |
| Customer demand | Cloud capex, GPU lead times, ASIC ramps, inventory | Determines whether shortage is structural or pull-forward |

The best answer is usually not "TSMC has capacity" or "TSMC is constrained."
It is "which step is constrained, for which customer, at which node/package,
and for how many quarters?"

## Node mix and customer mix

TSMC reports revenue by platform and by technology generation. The two cuts
answer different questions.

**Node mix** tells you where the wafer economics are concentrated. Advanced
nodes generally carry higher pricing, higher depreciation, more demanding
process control, and greater customer lock-in. But a node label is not enough:
N3 smartphone wafers, N4 GPU wafers, and mature specialty wafers have different
volume shapes, pricing, and cycle risk.

**Platform mix** tells you what end markets are funding the capacity. For TSMC,
the key tension is HPC versus smartphone. Smartphone demand historically gave
TSMC enormous leading-edge volume and fast node ramps. AI/HPC demand now adds a
second scale engine, but it is more concentrated around a small number of very
large customers and supply-chain dependencies.

Ask these questions:

- Is advanced-node growth coming from one flagship smartphone customer, many
  AI customers, or a broader set of high-performance ASICs?
- Are customers prepaying, signing long-term agreements, or simply giving
  optimistic forecasts?
- Is a new node ramp replacing revenue on an older node, or adding incremental
  wafer demand?
- Does packaging capacity grow at the same pace as the advanced-node wafer
  plan?
- Are non-leading-edge fabs healthy enough to absorb fixed costs if consumer,
  automotive, or industrial demand weakens?

Customer concentration cuts both ways. A small set of customers can fund
enormous capacity with high confidence, but it also means a product delay,
architecture shift, or inventory correction can move the whole model.

## Capex cycles, utilization, and depreciation

Foundry capex is paid before demand is proven. The machine arrives, the fab is
built, depreciation begins, and yield learning consumes time. The income
statement therefore lags the strategic decision.

Think in three clocks:

- **Ordering clock:** ASML, Applied Materials, Lam, Tokyo Electron, KLA, and
  other suppliers receive tool orders long before wafer revenue appears.
- **Ramp clock:** the fab installs tools, qualifies process recipes, and moves
  from engineering lots to high-volume manufacturing.
- **Demand clock:** customers launch products, then either pull more capacity
  or digest inventory.

Margin pressure often appears when these clocks are misaligned. If capacity is
installed before customer demand arrives, utilization falls while depreciation
rises. If demand arrives before capacity, utilization and pricing improve but
customers complain about allocation.

**Red flags in the model:**

- Revenue growth slows while depreciation and overseas start-up costs rise.
- Advanced-node utilization is strong but mature-node utilization is weak.
- Management talks more about "long-term demand" than current order visibility.
- Packaging bottlenecks ease while wafer capacity additions keep accelerating.
- Gross margin guidance deteriorates even when headline AI demand sounds strong.

## Overseas fabs versus the Taiwan ecosystem

TSMC's Taiwan concentration is strategically powerful and politically risky.
Customers and governments want geographic resilience, but duplicating advanced
manufacturing in Arizona, Japan, Europe, or elsewhere is expensive and slow.

The key distinction:

- **Resilience capacity** reduces geopolitical and customer risk.
- **Lowest-cost scale capacity** usually remains tied to the deepest existing
  ecosystem.

An analyst should not treat overseas fabs as instantly interchangeable with
Taiwan giga-fabs. Tool install, yield ramp, workforce depth, suppliers,
materials logistics, engineering culture, customer qualification, and local
utilities all matter.

The overseas question is not "is it good or bad?" It is:

1. Who pays for the cost gap?
2. Which customers commit real volume?
3. Does the site run leading-edge process steps or only selected nodes?
4. Does the site receive enough local supplier density to compound learning?
5. How much gross margin dilution is acceptable in exchange for resilience?

Government incentives can improve project returns, but they do not magically
create Taiwan's full ecosystem. The base case should usually assume slower
ramps, higher costs, and strategic value that may not show up as peak margin.

## CoWoS expansion changes bargaining power

Historically, analysts could focus on wafer capacity and node share. AI
accelerators force a second question: can the finished package be built?

For NVIDIA, AMD, Broadcom, and custom ASIC customers, the wafer is only one
input. The accelerator also needs HBM and a large advanced package. TSMC's CoWoS
capacity therefore becomes a governor on customers' AI revenue.

This is why TSMC can capture value outside pure wafer fabrication. Advanced
packaging is no longer a back-end afterthought; it is part of the product
architecture.

But CoWoS is also a forecasting trap. Public commentary may confirm expansion
without giving enough detail on usable capacity, mix by package type, yield,
customer allocation, or whether OSAT partners are absorbing overflow. Avoid
turning vague capacity-expansion language into precise unit forecasts unless
you can tie it to customer shipments, HBM availability, and package design.

## Example analysis workflow

Use this workflow when a new TSMC earnings report, annual report, or customer
capex update appears.

1. **Separate wafer and package demand.** Identify whether the update refers to
   wafers, advanced packaging, or total AI supply.
2. **Map the node mix.** Track 3nm, 5nm, 7nm, and mature-node revenue shares.
   Ask whether growth is mix, price, volume, or currency.
3. **Map the platform mix.** Compare HPC and smartphone trends. A healthy
   thesis prefers multiple engines, not one heroic customer.
4. **Check utilization clues.** Listen for inventory digestion, customer
   forecasts, and gross margin guidance.
5. **Compare capex to demand duration.** Decide whether the capex plan assumes
   a one-year shortage, a multi-year AI buildout, or geopolitical duplication.
6. **Translate overseas fabs into economics.** Estimate the margin drag and
   strategic option value separately.
7. **Write the disconfirming evidence first.** Make the bear case concrete
   before updating the bull case.

## Bull/base/bear frame

| Scenario | What has to be true | Evidence you would expect |
|---|---|---|
| Bull | AI/HPC demand compounds for years, CoWoS remains scarce, N2/N3 ramps are strong, overseas dilution is manageable | Strong HPC growth, firm advanced packaging commentary, stable or improving gross margin, broad customer commitments |
| Base | TSMC keeps node and packaging leadership, but capex and overseas ramps absorb some upside | Good advanced-node mix, periodic utilization softness, gross margin within guided ranges, packaging additions gradually ease bottlenecks |
| Bear | AI demand was pulled forward, advanced packaging overbuilds, mature nodes weaken, or geopolitics forces costly duplication | Falling lead times, customer order cuts, lower utilization, margin pressure from depreciation, meaningful share shifts to Samsung or Intel |

## What to watch

- Revenue by platform, especially HPC and smartphone.
- Revenue by node, especially 3nm, 5nm, and 7nm.
- Gross margin, operating margin, depreciation, and overseas start-up costs.
- Capex guidance and whether it is framed as leading-edge, packaging, mature
  node, or geographic resilience.
- CoWoS and advanced packaging commentary, including whether capacity remains
  fully allocated.
- Customer concentration clues from Apple, NVIDIA, AMD, Broadcom, Qualcomm,
  Amazon, Google, Microsoft, Meta, and other ASIC buyers.
- Memory-side evidence from HBM suppliers, because TSMC cannot ship a complete
  AI accelerator without HBM availability.
- Samsung Foundry and Intel Foundry customer wins that move from press release
  to high-volume revenue.
- Taiwan geopolitical risk, energy security, water availability, earthquake
  resilience, export controls, and government incentive execution.

## What evidence changes the thesis?

Change the thesis when the facts change, not when the narrative gets louder.

Upgrade the thesis if:

- Multiple AI customers commit to multi-year volumes across wafers and packages.
- Advanced packaging remains the binding constraint even after announced
  expansions.
- New nodes ramp with strong yield, pricing, and customer breadth.
- Overseas fabs qualify strategic customers without a larger-than-expected
  margin penalty.
- Mature and specialty nodes recover enough to reduce fixed-cost drag.

Downgrade the thesis if:

- AI accelerator customers cut orders or shift architectures in ways that reduce
  TSMC package intensity.
- CoWoS lead times normalize while TSMC is still adding capacity aggressively.
- Advanced-node share growth slows despite heavy capex.
- Gross margin falls for structural reasons rather than temporary ramp costs.
- A credible second source wins meaningful high-volume leading-edge business.
- Taiwan risk becomes an operational issue, not only a valuation discount.

## Analyst conclusion

TSMC is a capacity allocator with unusually strong customer trust. Its upside is
structural demand for energy-efficient compute plus advanced packaging. Its risk
is that capacity must be built years before demand is certain, and much of its
strategic value sits in a geopolitically sensitive geography.

The highest-quality TSMC work is specific. Do not ask only whether AI demand is
strong. Ask which customer, which node, which package, which bottleneck, which
capex clock, and which margin consequence.
