# HBM suppliers: memory becomes strategic again

Commodity DRAM is cyclical. HBM is still memory, so it is not immune to cycles,
but AI changed the quality of demand. HBM is not just "more bits"; it is a
qualified stack that must sit beside a specific accelerator die, survive a
specific package flow, and meet bandwidth, power, thermal, and reliability
targets at customer scale.

The practical analyst question is:

> Which memory supplier has qualified HBM capacity with the right customers, and
> how much ordinary DRAM capacity is being pulled into premium AI products?

That question is more useful than "who has the most DRAM revenue?" because HBM
economics are governed by qualification, packaging, and allocation.

## The players

**SK hynix** became the clearest HBM winner in the Hopper/HBM3E era. The
company reported record 2025 financial results: KRW 97.1467 trillion revenue,
KRW 47.2063 trillion operating profit, and a 49% operating margin. It described
its position as built on quality, technology leadership, and the ability to
stably supply HBM3E and HBM4.

**Samsung Electronics** has the broadest memory scale and deep internal
semiconductor capability, but HBM qualification and thermal/power
competitiveness became a visible investor issue in 2024-2025. Samsung's own 2025
commentary emphasized expanding HBM3E sales and preparing competitive HBM4
shipments for 2026. The bull case is not that Samsung lacks memory competence;
it is that scale plus a corrected HBM product can rapidly change the share
picture.

**Micron** is smaller than Samsung and SK hynix in DRAM scale, but it has pushed
HBM3E as a data-center growth vector. Micron is often the "incremental share and
margin recovery" case: if it qualifies into enough high-value programs, a
smaller absolute HBM position can still have a large mix and margin impact.

## What an HBM stack really is

An HBM product is a small vertical memory system:

- Multiple DRAM dies are stacked on top of a base logic die.
- Through-silicon vias, or TSVs, carry signals vertically through the stack.
- Microbumps or hybrid bonding connect the dies with very short links.
- The stack sits beside the accelerator die on an interposer or advanced
  package.
- The final system must move huge bandwidth while staying within power and
  thermal limits.

This creates a different bottleneck map than ordinary DDR. You need good DRAM
dies, good stacking, good test coverage, good thermal behavior, and a package
flow that can assemble the memory with the logic die. A defect can enter through
the wafer, the stack, the base die, the bond, the interposer, or final package
assembly.

## TSV, bonding, and yield

HBM yield is multiplicative. If a stack needs many known-good dies, one bad die
or bad bond can ruin the stack economics. Higher stacks, such as 12-high and
future 16-high versions, can improve capacity per package but also raise
thermal, warpage, test, and assembly difficulty.

Key drill-down questions:

- What stack height is the supplier shipping in volume: 8-high, 12-high, or
  higher?
- Is the supplier talking about sampling, qualification, mass production, or
  customer shipment?
- Are yield problems at the DRAM die, TSV/bonding, base die, or final package?
- Does higher capacity require a material process change, such as improved
  bonding, thinner die, better thermal interface material, or new test flow?
- Are reported shipments constrained by memory output or by advanced packaging
  capacity at the accelerator vendor's supply chain?

## Qualification is the moat

For HBM, "can produce" is not the same as "qualified at the top customer."
NVIDIA, AMD, Broadcom, and hyperscaler ASIC teams care about power, thermals,
reliability, package integration, error behavior, firmware interactions, and
delivery schedule. A supplier that misses qualification can lose premium share
even if its DRAM fabs are large.

Useful evidence has a hierarchy:

| Evidence | What it means | Caveat |
|---|---|---|
| Engineering sample | Product exists and can be tested | Not revenue proof |
| Customer qualification | Meets at least one target program's requirements | May be narrow or low volume |
| Named design win | Stronger proof of commercial adoption | Still may not reveal share |
| Volume shipment | Revenue is flowing | May be capacity-limited elsewhere |
| Multi-year allocation | Customer values secure supply | Can be renegotiated if demand weakens |

When a management team says "customer interest is strong," ask whether that
means lab evaluation, formal qualification, purchase orders, or take-or-pay-like
capacity commitments.

## HBM3E to HBM4 transition

HBM3E rewarded suppliers that could deliver bandwidth, capacity, thermal
performance, and stable yield into the current AI accelerator cycle. HBM4 raises
the stakes. It is expected to widen the interface, increase bandwidth, and
become more tightly co-designed with accelerator packages.

The transition matters because leadership can reset at a generation boundary.
SK hynix can defend with execution and customer trust. Samsung can use HBM4 as a
catch-up window. Micron can use the transition to win incremental programs if
its power, capacity, and availability are compelling.

Student workflow:

1. Separate HBM3E share from HBM4 readiness.
2. Track which customers are qualifying which generation.
3. Ask whether the new generation needs new base die, new packaging process, or
   new thermal assumptions.
4. Watch whether the first volume programs are concentrated at one AI customer
   or diversified across GPU, ASIC, and networking customers.

## Capacity allocation and DRAM mix shift

HBM consumes advanced DRAM wafer capacity, test capacity, engineering attention,
and advanced packaging support. A supplier does not simply add HBM revenue on
top of ordinary DRAM. It chooses what to build.

This matters in two directions:

- If HBM demand is strong, conventional server DDR and other DRAM markets can
  tighten because wafer starts and leading-edge bits are redirected.
- If AI demand pauses, HBM-focused capex can become underutilized or force
  discounting.

The SemiAnalysis-style move is to model the second-order effect: HBM strength
can lift the whole DRAM cycle by removing supply from commodity markets, but it
can also make the next downturn harsher if suppliers overbuild the same premium
capacity.

## ASP, margin, and the cycle

HBM usually carries higher average selling prices than commodity DRAM because it
is scarce, technically hard, and qualified into high-value systems. But high ASP
does not automatically mean permanent high margin.

Red flags:

- HBM ASPs fall before volume grows enough to offset the price decline.
- A lagging supplier prices aggressively to gain qualification.
- Customer concentration gives the buyer leverage in the next allocation round.
- Expensive capex arrives just as demand growth slows.
- Commodity DRAM pricing weakens while HBM capex keeps fixed costs elevated.

## Packaging interdependence

HBM suppliers do not control the whole AI module. HBM stacks must meet the
capacity of the advanced packaging ecosystem: interposers, substrate supply,
assembly, thermal solution, test, and the logic die itself. A memory supplier
can have qualified stacks but still fail to recognize all possible revenue if
the accelerator program is bottlenecked at CoWoS-like packaging, substrates, or
system integration.

Ask the bottleneck question every quarter:

> Is the scarce thing HBM wafers, stack assembly, base dies, advanced packaging,
> substrates, power delivery, networking, or customer data-center deployment?

The answer can move without the HBM supplier doing anything wrong.

## Customer concentration

HBM demand is tied to a small number of very large accelerator platforms. That
is good when the customer is capacity-starved and willing to reserve supply. It
is risky when a single platform slips, changes stack count, dual-sources, or
uses qualification to pressure pricing.

Concrete questions:

- How much HBM revenue depends on one AI accelerator customer?
- Is the supplier qualified across NVIDIA, AMD, Broadcom, and custom ASICs, or
  mainly one ecosystem?
- Are allocations locked by long-term agreements, or are they ordinary purchase
  forecasts?
- Does the customer want a second source for strategic reasons?
- Could a new accelerator architecture reduce stacks per accelerator or use a
  lower-cost memory configuration?

## Bull/base/bear setup

| Case | What has to be true | Evidence to seek | Main risk |
|---|---|---|---|
| Bull | HBM remains structurally scarce, SK hynix defends leadership, Samsung/Micron supply does not crash ASPs, and AI accelerators keep increasing memory content | Multi-year HBM sold-out commentary, stable or rising HBM ASPs, broad HBM4 qualifications, tight DDR/server DRAM supply | Customers dual-source and negotiate away excess returns |
| Base | HBM grows rapidly but share rotates; SK hynix stays strong, Samsung improves, Micron gains selective slots, and margins normalize from peak levels | Qualified second sources, expanding HBM capacity, solid but less explosive margins, ordinary DRAM cycle improvement | Investors overpay for peak-cycle economics |
| Bear | HBM capacity arrives faster than accelerator demand or packaging capacity; qualification gaps close; ASPs fall and capex depresses returns | Falling HBM pricing, inventory build, weaker customer capex, delayed accelerator ramps, underutilized stack capacity | The bear case can look wrong for several quarters because backlog lags demand |

## What to watch

- Customer qualification language: sample, qualified, designed-in, shipping, or
  allocated.
- HBM3E versus HBM4 mix, especially 12-high and higher stack readiness.
- HBM ASP and gross-margin commentary, not just bit shipment growth.
- Conventional DRAM pricing, because HBM mix shift can tighten non-HBM supply.
- Capex split between wafer capacity, TSV/stacking, test, and packaging support.
- Customer concentration and whether second-source qualification changes pricing.
- Packaging capacity updates from foundries, OSATs, substrate suppliers, and AI
  accelerator vendors.
- Any evidence that accelerator customers reduce HBM stacks per system.

## Source-aware caveats

Company commentary is useful but promotional. "Preparing HBM4," "expanding
sales," and "strong customer demand" are not equivalent. Prefer filings,
customer-named design wins, shipment data, segment margins, and capacity
commitments. Also remember that market-share estimates may differ by metric:
revenue share, bit share, stack count, and qualified capacity can tell different
stories.

## Analyst conclusion

HBM turns memory from a pure commodity cycle into a systems qualification story.
SK hynix, Samsung, and Micron are not simply selling bits; they are competing
for qualified positions inside AI accelerator roadmaps. The best analysis links
customer qualification, stack yield, packaging capacity, DRAM mix shift, and
cycle timing into one operating model.
