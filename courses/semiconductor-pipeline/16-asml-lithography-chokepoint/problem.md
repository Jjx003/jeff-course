# ASML: the tool bottleneck

ASML is the cleanest example of a semiconductor chokepoint company. It does not
sell chips. It sells the lithography systems that make many advanced chips
possible.

The SemiAnalysis-style question is:

> Which customer capacity plans require ASML tools, which tool class is
> constrained, and how much future revenue is already embedded in bookings,
> backlog, installed-base upgrades, and service?

As of May 2026, ASML's 2025 annual report and FY2025 release reported EUR 32.7
billion of total net sales, EUR 9.6 billion of net income, 52.8% gross margin,
535 total system sales, 48 EUV lithography systems sold, EUR 8.2 billion of
installed-base management sales, EUR 28.0 billion of net bookings, and EUR 38.8
billion of backlog. ASML also highlighted stronger-than-anticipated China DUV
demand during the cycle and a meaningful installed-base business.

Those facts make ASML look simple. It is not. The analyst has to separate:

- EUV systems for leading-edge logic and advanced DRAM.
- DUV immersion and dry systems for mature nodes, memory, multipatterning, and
  trailing-edge capacity.
- Installed-base management: service, field options, productivity upgrades, and
  lifetime support.
- Bookings and backlog, which are forward-looking but can shift with customer
  capex cycles.
- Export-control effects, especially China DUV pull-forward and future caps.

## Controlled capability

ASML controls:

- EUV scanner technology.
- Advanced DUV immersion lithography.
- Field upgrades and service for installed systems.
- A supplier network so specialized that replication is extremely hard.

EUV is the obvious moat, but DUV is not obsolete. Many layers still use DUV, and
DUV multipatterning can extend older process flows. This is why export-control
debates include advanced DUV tools, not only EUV.

## EUV versus DUV economics

EUV and DUV are different businesses inside the same company.

| Tool class | Main demand driver | Analyst trap |
|---|---|---|
| EUV | Leading-edge logic, advanced DRAM, node transitions, layer intensity | Treating units as the whole story when ASP, configuration, and timing matter |
| High-NA EUV | Future patterning needs at the most advanced nodes | Assuming early shipments equal broad high-volume adoption |
| DUV immersion | Mature/trailing nodes, memory, multipatterning, China capacity | Calling DUV "old tech" even though it remains strategically important |
| Dry DUV and other systems | Specialty, mature, and support layers | Ignoring long tail demand and service needs |
| Installed base | Uptime, productivity, field options, service contracts | Missing revenue when new system units are cyclically weak |

EUV can reduce some multipatterning complexity, but advanced chips still need
many lithography layers. DUV remains essential because not every layer needs
EUV, not every chip is leading edge, and mature-node supply chains are still
strategic.

## System shipments versus installed-base management

ASML's installed base matters because scanners require service, parts, upgrades,
and productivity improvements. When ASML performs a field upgrade, some revenue
can shift from new system sales to installed-base revenue.

This is an analyst trap: lower new-tool units do not automatically mean weaker
customer demand if upgrades raise productivity or if revenue mix shifts.

Installed-base management can be powerful because the tool does not disappear
after sale. A scanner becomes part of a customer's production system for years.
Uptime, throughput, overlay, software, field upgrades, and parts availability
all affect customer wafer output.

Ask:

- Are customers buying new systems or upgrading installed tools?
- Is installed-base growth service-like, cyclical, or tied to field-option
  pull-ins?
- Are upgrades increasing customer capacity without a visible new unit sale?
- Does installed-base strength offset weakness in new DUV or EUV shipments?

## Bookings and backlog

Bookings and backlog are essential, but they are not magic. A booking is not
the same as revenue, and backlog can be shaped by lead times, customer pull-ins,
export rules, and delivery schedules.

Use this interpretation ladder:

1. **Bookings** show new demand signals, but can be lumpy.
2. **Backlog** shows accumulated future work, but not exact quarterly revenue.
3. **Shipments** show physical output, but revenue recognition can depend on
   acceptance and installation.
4. **Installed-base revenue** shows lifetime monetization, but not necessarily
   new fab expansion.

A high-quality ASML thesis connects all four instead of cherry-picking the most
bullish metric.

## China DUV pull-forward and export controls

ASML sits at the center of U.S.-China technology restrictions. EUV systems have
long been unavailable to China, and controls have expanded around some advanced
DUV systems. At the same time, China has been a large DUV customer, especially
for mature-node and trailing-edge expansion.

The thesis tension:

- China DUV demand can support near-term revenue.
- Export controls can cap the most strategic sales.
- Customers outside China drive EUV and leading-edge demand.
- Geopolitics can affect both sales opportunity and supply-chain inputs.

Pull-forward risk matters. If Chinese customers bought more DUV tools ahead of
tighter restrictions or to build strategic inventory, future DUV demand could
fall even if the installed base keeps generating service revenue. Conversely,
non-China leading-edge demand can offset some China weakness if TSMC, Samsung,
Intel, SK hynix, and Micron sustain capex.

Do not analyze "China exposure" as one number. Split it into mature-node DUV,
restricted advanced DUV, service on already installed tools, and indirect demand
from non-China customers serving global end markets.

## High-NA EUV adoption

High-NA EUV improves resolution, but the investment case depends on adoption
economics. Customers must justify:

- Tool price and total cost of ownership.
- Throughput and availability.
- Mask, resist, metrology, and defectivity learning.
- Design-rule and process integration changes.
- Whether lower multipatterning complexity offsets new integration cost.
- Whether the node's performance-per-watt gains justify wafer pricing.

The first High-NA tools prove ecosystem progress. They do not automatically
prove steep high-volume adoption. Track customer milestones separately:
research install, pilot line use, process qualification, product tape-out, and
high-volume manufacturing.

## Supplier constraints

ASML's moat is also a dependency map. The company relies on specialized optics,
stages, light sources, metrology, precision mechatronics, software, and a very
deep supplier base. The most famous supplier is Zeiss for EUV optics, but the
broader point is that ASML output is constrained by an ecosystem, not just by
ASML's assembly floor.

Red flags include:

- Management citing supplier capacity as a limiter.
- Long lead times extending despite strong demand.
- Inventory or working-capital changes that imply bottlenecked production.
- High-NA ramps requiring supplier learning at the same time customers want
  more regular EUV.
- Geopolitical controls affecting components, service, or customer acceptance.

## Connecting ASML demand to customer capex

ASML demand is derived demand. Start with the customers.

| Customer group | What to read | ASML implication |
|---|---|---|
| TSMC | Advanced-node ramps, CoWoS-linked AI demand, overseas fabs, capex | EUV and DUV for leading-edge logic plus service and upgrades |
| Samsung | Foundry share, advanced logic ramps, DRAM roadmap | EUV demand if foundry and memory execution improve |
| Intel | Foundry strategy, internal process roadmap, government-backed fab plans | Potentially large EUV/High-NA demand, but execution risk is high |
| SK hynix/Micron/Samsung Memory | DRAM node transitions, HBM capacity, NAND cycle | EUV for advanced DRAM, DUV for memory and support layers |
| China fabs | Mature-node expansion, local policy, export-control timing | DUV demand and pull-forward risk, limited EUV opportunity |

The key move is to align timing. A TSMC fab plan may imply lithography demand
years before wafer revenue. A memory recovery may first show up in capex
guidance, then equipment orders, then ASML revenue, then customer bit output.

## Example analysis workflow

1. **Start with customer capex.** Read TSMC, Samsung, Intel, SK hynix, Micron,
   and major China-fab commentary.
2. **Classify the capex.** Is it leading-edge logic, DRAM, NAND, mature-node,
   packaging, buildings, or support infrastructure?
3. **Translate to lithography mix.** Decide whether the demand needs EUV,
   High-NA EUV, DUV immersion, dry DUV, metrology, or service.
4. **Check ASML bookings/backlog.** Ask whether the customer signals are already
   in orders or still only in narrative.
5. **Adjust for export controls.** Separate what can be shipped, licensed,
   serviced, delayed, or cancelled.
6. **Look for supplier bottlenecks.** Strong demand without ASML output growth
   can mean supply constraint, not weak orders.
7. **Write the timing bridge.** Explain when orders become shipments, when
   shipments become revenue, and when customer capacity becomes chip output.

## Bull/base/bear frame

| Scenario | What has to be true | Evidence you would expect |
|---|---|---|
| Bull | AI-led foundry capex, advanced DRAM/HBM, and High-NA adoption compound while installed-base revenue grows | Strong EUV bookings, resilient backlog, more customer High-NA milestones, service and field options growing |
| Base | Leading-edge demand remains healthy, DUV normalizes after China pull-forward, and High-NA ramps gradually | Solid but lumpy bookings, China mix declines, installed-base revenue offsets some system cyclicality |
| Bear | Customer capex pauses, China DUV demand rolls over, High-NA adoption is slower, or supplier constraints cap output | Weak bookings, backlog burn without replenishment, lower DUV sales, delayed customer node ramps, margin pressure |

## What to watch

- EUV unit sales, EUV revenue, and EUV bookings.
- DUV immersion sales and China regional mix.
- Installed-base management sales and field-option commentary.
- Net bookings, backlog, order cancellations, and delivery timing.
- High-NA EUV shipments, customer acceptance, and high-volume milestones.
- TSMC/Samsung/Intel foundry capex and node timing.
- SK hynix/Micron/Samsung memory capex, especially DRAM and HBM.
- Export-control changes from the Netherlands, U.S., Japan, and the EU.
- Supplier constraints around optics, stages, light sources, and critical
  subassemblies.

## What evidence changes the thesis?

Upgrade the thesis if:

- EUV bookings improve across multiple customers, not just one pull-in.
- High-NA moves from pilot activity to named high-volume node plans.
- Installed-base management grows because customers are increasing productive
  output, not merely catching up on deferred service.
- Memory capex recovers with credible HBM/advanced DRAM demand.
- China weakness is offset by non-China leading-edge demand without margin
  damage.

Downgrade the thesis if:

- Bookings weaken while customer capex commentary also deteriorates.
- China DUV demand falls faster than EUV and installed-base growth can offset.
- High-NA economics fail to justify broad adoption.
- Supplier constraints prevent ASML from converting demand into shipments.
- Export controls expand in ways that reduce service or DUV revenue beyond
  current expectations.
- TSMC, Samsung, Intel, or memory makers delay node transitions.

## Analyst conclusion

ASML is not a normal equipment vendor. It is a bottleneck supplier whose demand
is derived from other companies' capacity plans. To analyze ASML, read TSMC,
Samsung, Intel, SK hynix, Micron, and export controls at the same time.

The best ASML analysis is a timing bridge: customer capex intent to ASML order,
order to shipment, shipment to revenue, and installed tool to customer wafer
output.
