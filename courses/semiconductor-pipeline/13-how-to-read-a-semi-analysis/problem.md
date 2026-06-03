## The analyst's job is to locate the constraint

This section changes the course from vocabulary to company analysis. The goal is
to read semiconductor companies the way a serious industry analyst does: not as
tickers, and not as isolated products, but as positions inside a physical supply
chain.

The best semiconductor analysis asks a plain question again and again:

> What has to be true, physically and commercially, for this revenue to ship?

Use this five-part frame:

1. **What scarce capability does the company control?**
   Examples: leading-edge wafer capacity, EUV scanners, HBM stacks, advanced
   packaging, interconnect, CUDA software, qualified systems, domestic
   manufacturing, or customer allocation.
2. **Where is the bottleneck today?**
   It may be wafers, packaging, memory, networking, power, yield, tool
   availability, export licenses, or customer capex.
3. **Who captures the economics?**
   Scarcity only matters commercially if the company can price it, allocate it,
   bundle it, or use it to lock in customers.
4. **What evidence can disconfirm the thesis?**
   Look for capacity expansion, substitution, customer concentration, inventory
   charges, margin compression, failed qualifications, or policy shifts.
5. **What is the time lag?**
   Fabs, tools, HBM stacks, packaging lines, and data centers have different
   build and qualification cycles. The lag often explains why revenue, capex,
   and demand signals disagree for several quarters.

This is constraint accounting. You are tracing a claimed growth story through
the slowest real-world link.

## A useful evidence stack

Company analysis should combine several source types. None is enough alone:

| Source | What it is good for | What to distrust |
|---|---|---|
| Annual report / 10-K / 20-F | Segment revenue, margins, risk factors, customer concentration, purchase obligations, inventory, capex | Management framing, broad risk language, stale year-end snapshots |
| 10-Q / interim report | Fresh inventory, receivables, gross margin, commitments, customer or geography changes | Short-term noise, incomplete context |
| Earnings release | Quarterly revenue, margin, guidance, demand commentary | Promotional language and selective emphasis |
| Earnings call | Bottleneck clues, product-ramp timing, customer demand, capacity plans | Carefully worded optimism and non-answers |
| Supplier filings | Cross-checks from foundries, OSATs, memory makers, tool vendors, substrate vendors, network vendors | Segment mismatch and delayed visibility |
| Government rules | Export-control constraints, subsidy timing, license risk, domestic sourcing pressure | Legal complexity and implementation lag |
| Industry reporting | Channel checks, tool lead times, customer qualifications, informal capacity estimates | Rumors, unnamed sources, stale checks, incentive bias |
| Product teardown / BOM work | What is physically inside a system | Hard-to-generalize one-off examples |
| Customer capex commentary | Whether demand has budget, site readiness, and deployment intent | Capex categories that mix compute, buildings, power, and networking |

The most useful analysis compares sources against each other. If an accelerator
vendor says demand is huge, a foundry raises advanced packaging capex, memory
makers describe HBM tightness, and hyperscalers raise AI infrastructure budgets,
those signals reinforce one another. If one link weakens, the thesis needs a
fresh pass.

## Triangulation workflow

Do not start with the stock chart. Start with a claim, then build a source map.

```text
Claim: "Company X will grow because AI demand is supply constrained."

1. Company filings:
   - What segment is growing?
   - Are inventories, purchase obligations, or customer concentration rising?
   - Did gross margin improve because of price/mix, or fall because of system cost?

2. Earnings call:
   - Which product names are tied to revenue now versus "future ramps"?
   - Did management say demand exceeds supply, or merely demand is strong?
   - Did they identify the bottleneck or avoid doing so?

3. Supplier and customer checks:
   - Do foundry, HBM, packaging, networking, and power-infrastructure suppliers
     confirm the same direction?
   - Are hyperscalers ordering, deploying, or only announcing future capacity?

4. News and policy:
   - Are export rules, subsidies, tariffs, or license requirements changing the
     reachable market?
   - Is a product being redesigned for compliance?

5. Disconfirmation:
   - What single data point would make the claim weaker next quarter?
```

Good triangulation often finds timing mismatches. A supplier can be adding
capacity while a customer is still constrained. A product can have strong orders
while a data center cannot yet power the racks. A company can report record
revenue while inventory risk is quietly building.

## Demand signal versus supply signal

Semiconductor stories often blur demand and supply. Separate them.

| Signal type | Examples | Analyst question |
|---|---|---|
| Demand signal | Customer orders, cloud capex, backlog, utilization, product adoption, waitlists | Is there real willingness and ability to pay? |
| Supply signal | Wafer starts, HBM allocation, CoWoS-like capacity, substrate availability, tool shipments, yield | Can the physical product be built and delivered? |
| Price signal | ASPs, gross margin, memory pricing, foundry pricing, attach rates | Who has bargaining power? |
| Deployment signal | Data-center power, networking, cooling, software readiness, cluster acceptance | Can the purchased hardware turn into useful capacity? |

A bullish demand signal with a weak supply signal means near-term revenue may be
capped but pricing power can be strong. A strong supply signal with a weak
demand signal can mean inventory and margin risk. The most dangerous mistake is
treating "everyone wants it" as the same thing as "everyone can receive it,
install it, and pay for it on time."

## Leading versus lagging indicators

The best indicators are not always in the company you are analyzing.

| Indicator | Usually leads or lags? | Why it matters |
|---|---|---|
| Tool orders and foundry capex | Leading, but noisy | Capacity must be ordered before it exists |
| HBM supply agreements | Leading | Memory allocation can constrain accelerator shipments |
| Advanced packaging expansion | Leading to coincident | Package capacity is often the bridge from die to shippable module |
| Hyperscaler capex plans | Leading | Budgets reveal intent, though categories can be broad |
| Data-center power interconnect approvals | Leading for deployment | Hardware demand can exceed site readiness |
| Reported revenue | Lagging | It confirms shipments that already happened |
| Gross margin | Lagging to coincident | It reveals mix, pricing, charges, and transition cost |
| Inventory and purchase commitments | Leading risk / lagging evidence | They can show confidence or future write-down risk |

Leading indicators create hypotheses. Lagging indicators grade them. Do not use
last quarter's reported revenue as proof that next year's bottleneck is solved.

## Handling stale data

Semiconductor facts decay at different speeds. A capacity number from six months
ago may still matter for fabs, but it may be stale for product allocation,
export rules, channel inventory, or cloud deployment timing.

Use a freshness label in your notes:

| Label | Use when | How to treat it |
|---|---|---|
| Fresh | Filed, reported, or announced this quarter | Can support a current claim if it matches other sources |
| Aging | One to three quarters old | Use for context; verify before using as a current constraint |
| Structural | Multi-year asset, architecture, qualification, or policy frame | May remain useful, but check for exceptions |
| Stale | Older than the relevant product or policy cycle | Do not use as current evidence without an update |

When you cite a stale source, say what it still proves. For example: "This 2023
CoWoS article is useful for the mechanism of the bottleneck, not for today's
exact capacity." That is how serious analysts avoid laundering old numbers into
new certainty.

## Installed base versus new capacity

Many mistakes come from mixing installed base with incremental capacity.

**Installed base** is what already exists: GPUs deployed, tools installed, fabs
qualified, HBM lines running, servers in data centers. It matters for software
ecosystems, service revenue, replacement cycles, and customer lock-in.

**New capacity** is what can be added: incremental wafer starts, package
substrate output, HBM bits, rack assembly, power, cooling, networking, and
customer deployments. It matters for next-quarter and next-year revenue growth.

Ask different questions:

| Topic | Installed-base question | New-capacity question |
|---|---|---|
| GPUs | What workloads are already standardized on this platform? | How many additional accelerators can ship and be deployed? |
| Tools | How many tools are installed and qualified? | How many new tools can be delivered, installed, and ramped? |
| HBM | Which products already use which HBM generation? | How much incremental HBM is allocated to this customer or platform? |
| Packaging | What flows are proven in production? | Which new package lines, yields, and substrates limit the ramp? |
| Software | Which developers and models are already optimized? | Does a new product require porting, tuning, or qualification? |

Installed base supports durability. New capacity supports growth. A company can
have a wonderful installed base and still miss a ramp because the next system is
constrained somewhere else.

## Worked mini-thesis template

When you read a company, write a thesis in this shape. Keep it short enough that
you can revise it after every filing or call.

```text
Company:
Date of thesis:

One-sentence claim:
Example: Company X benefits because AI infrastructure demand is constrained by
advanced packaging and HBM, and it controls customer allocation plus the system
architecture that turns scarce parts into deployable clusters.

Controlled capability:
- What the company owns, qualifies, bundles, or allocates.

Current demand driver:
- Who is buying, for what workload, with what budget signal?

Likely bottleneck:
- The slowest link today.
- The link most likely to become slowest next.

Demand evidence:
- Filings:
- Calls:
- Customer comments:
- Channel / industry reporting:

Supply evidence:
- Foundry:
- HBM:
- Packaging:
- Networking / power / deployment:

Economic capture mechanism:
- Pricing, mix, allocation, software lock-in, service revenue, or bundle scope.

Red flags:
- Inventory growth:
- Margin compression:
- Customer concentration:
- Product transition friction:
- Export or policy risk:
- Substitution:

Disconfirming signal:
- What would make you reduce confidence?

Time horizon:
- Next quarter:
- Next 12 months:
- Multi-year:

Confidence:
- High / medium / low, and why.
```

This is deliberately not a discounted cash flow model. Finance matters, but a
semiconductor thesis often starts upstream: what physical capability is scarce,
who owns it, and how long before alternatives arrive?

## Example: reading "AI demand"

"AI demand is strong" is not an analysis. It is a prompt.

Ask:

- Does the demand require leading-edge logic, HBM, CoWoS-like packaging, optics,
  power infrastructure, or all of them?
- Which suppliers are capacity constrained versus merely benefiting from price?
- Is the company selling components, complete systems, tools, or manufacturing
  capacity?
- Is demand pulled by hyperscalers with real deployment plans, or by customers
  double-ordering scarce parts?
- Does the bottleneck shift over time from compute die to memory, packaging,
  networking, power, cooling, or data-center construction?
- Are customers buying for training, inference, sovereign AI, internal use, or
  resale through cloud capacity?
- Is the same signal visible in supplier filings, or only in management's
  language?

That is the style of analysis the next modules practice.

## Red flags that deserve a second pass

Watch for these patterns:

- Revenue grows, but gross margin falls without a clearly temporary explanation.
- Management says demand exceeds supply but does not identify the constrained
  component.
- Backlog rises while customers also slow capex or delay deployments.
- Inventory grows faster than revenue during a product transition.
- A company reports "design wins" but not shipments, revenue, or qualification.
- A supplier announces capacity expansion, but the timing is after the period
  your thesis needs.
- Policy changes make a product legal status, geography, or customer set
  uncertain.
- A single customer or geography silently becomes too large for comfort.

The red flag is not automatically bearish. It is a prompt to update the
constraint map.

## Recap

Real semiconductor analysis is constraint accounting. You build a thesis by
tracing scarce capabilities through the value chain, separating demand from
supply, checking leading indicators against lagging evidence, and naming exactly
what would make you change your mind.
