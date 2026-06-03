# NVIDIA: not just the die

As of May 2026, the useful NVIDIA question is not "does NVIDIA sell GPUs?" It is
"which parts of the AI compute stack does NVIDIA control, and where can
shipments be constrained?"

The public facts have to be treated with dates attached. NVIDIA's fiscal 2025
results showed the first full scale of the AI infrastructure shift: revenue was
$130.5 billion and Data Center revenue was $115.2 billion. Its fiscal 2026
results pushed the frame further: full-year revenue reached $215.9 billion and
Data Center revenue reached $193.7 billion. Earlier in fiscal 2026, NVIDIA also
reported a $4.5 billion H20-related charge tied to U.S. export restrictions.

That is the evidence stack in miniature: demand, segment mix, supply chain,
product transition, and policy all in one company. The numbers are not the
analysis. The analysis is what must be true for those numbers to persist.

## Controlled capability

NVIDIA controls several layers:

- Accelerator architecture: Hopper, Blackwell, Blackwell Ultra, and successor
  roadmaps.
- Software ecosystem: CUDA, CUDA-X libraries, compilers, inference runtimes,
  training frameworks, NIM, enterprise software, and developer familiarity.
- Systems integration: HGX boards, GB200/NVL systems, rack-scale designs,
  networking, switches, NICs, DPUs, reference architectures, and validation.
- Customer allocation: hyperscaler, cloud, sovereign AI, and enterprise
  relationships determine where scarce supply goes first.
- Platform narrative: customers often buy the roadmap, not only the current
  chip, because they need continuity across model generations.

The strongest thesis is not "NVIDIA has the fastest chip." It is "NVIDIA sells
the most complete path from model demand to deployed cluster."

## Hopper to Blackwell: why transitions matter

Product transitions are where semiconductor theses become testable. Hopper
proved demand for large-scale AI accelerators and helped create a huge installed
base of CUDA-optimized training and inference capacity. Blackwell changes the
question from "can NVIDIA sell more GPUs?" to "can NVIDIA ramp a more complex
system without losing the economics that made Hopper so attractive?"

During the transition, separate four issues:

| Question | Why it matters |
|---|---|
| Is demand shifting from Hopper to Blackwell, or adding on top of Hopper? | A smooth transition protects revenue; a pause creates air pockets |
| Are customers waiting for the next platform? | Waiting can look like weak demand even when long-term demand is intact |
| Does Blackwell require different packaging, power, cooling, or rack integration? | The bottleneck can migrate from chip supply to system deployment |
| Does the new system improve token economics enough to justify the complexity? | Customers buy capacity when it lowers training or inference cost per useful output |

The analyst move is to track the transition by product generation, not just by
"Data Center revenue." A revenue line can hide whether the company is shipping
older products, ramping new ones, or mixing both to satisfy allocation.

## Bottleneck map

For a complete accelerator system, NVIDIA depends on:

| Link | Why it matters | What to watch |
|---|---|---|
| TSMC leading-edge or near-leading-edge wafers | Compute die supply and yield | Wafer allocation, yield commentary, node transition timing |
| HBM from memory suppliers | Bandwidth and capacity per accelerator | HBM generation, stack height, qualified suppliers, attach per GPU |
| Advanced packaging | Logic die and HBM must be assembled into one module | CoWoS-like capacity, substrates, interposers, package yields |
| Board and rack assembly | Systems must be built, tested, and shipped | ODM capacity, burn-in, liquid-cooling readiness |
| Networking silicon and optics | Cluster scale-out, not just single-node speed | NVLink, InfiniBand, Ethernet, Spectrum-X, optics availability |
| Power and cooling | Rack-scale systems are thermal and electrical products | Data-center power, liquid cooling, site retrofit timing |
| Export licenses | Some products and geographies can be blocked or redesigned | H20-like restrictions, charge risk, China revenue assumptions |

The analyst move is to ask which link is binding this quarter and which link
will bind next. During Hopper, HBM and CoWoS-like packaging were central. During
Blackwell-class systems, the constraint can include full-system integration,
liquid cooling, networking, and customer data-center readiness.

## HBM attach and packaging dependence

HBM is not a side component. It is part of the accelerator product definition.
For AI training and many inference workloads, memory bandwidth and memory
capacity can determine how much of the compute die is actually useful.

Ask:

- Which HBM generation is qualified for the platform?
- How many HBM stacks are attached per accelerator or module?
- Are multiple memory suppliers qualified, or is allocation concentrated?
- Does higher HBM attach raise performance, but also consume scarce packaging
  capacity?
- Are memory makers expanding supply fast enough, and at what margin?

Advanced packaging is the bridge between the compute die and the HBM stacks.
That makes packaging both a supply constraint and a strategic dependency. If
packaging capacity expands, NVIDIA may ship more systems. If packaging yields,
substrates, or interposer supply disappoint, demand does not matter enough by
itself.

## Networking: NVLink, InfiniBand, and Ethernet

NVIDIA's systems value is partly that it sells clusters, not isolated chips.
Large AI workloads need fast communication inside a server, across racks, and
across data-center fabrics.

Think in three layers:

| Layer | NVIDIA asset | Analyst question |
|---|---|---|
| Scale-up | NVLink / NVSwitch | Can many accelerators behave like one larger pool of compute? |
| Scale-out | InfiniBand and Ethernet products | Can many nodes train or serve models efficiently? |
| Operations | Software, telemetry, reference designs | Can customers deploy and keep clusters productive? |

InfiniBand matters where customers prioritize low latency and proven AI cluster
performance. Ethernet matters because hyperscalers often prefer open,
standardized, internally operated networks. NVIDIA's Spectrum-X strategy is an
attempt to keep more of the Ethernet AI networking value inside its platform.

Red flag: if customers increasingly buy accelerators but choose non-NVIDIA
networking at scale, NVIDIA may still grow revenue but capture less of the
cluster economics.

## CUDA and the software moat

CUDA is not just an API. It is a distribution channel for performance. The moat
comes from libraries, kernels, model frameworks, developer habits, debugging
tools, deployment recipes, and the accumulated work of making real workloads
fast.

The software moat is strongest when:

- Customers need time-to-train or time-to-deploy more than the lowest chip cost.
- Workloads use mature CUDA libraries or custom kernels.
- Teams lack spare engineering time to port and tune code.
- The model stack changes quickly enough that a full platform has value.

It is weaker when:

- The workload is stable, high volume, and narrow.
- A hyperscaler controls the full software stack.
- Inference kernels can be optimized once and amortized over massive internal
  volume.
- Open compiler stacks and model runtimes reduce switching cost.

This is why custom ASICs can coexist with NVIDIA rather than automatically
replace it.

## Hyperscaler concentration

NVIDIA's largest customers are cloud and internet infrastructure buyers with
enormous budgets and enormous bargaining power. Hyperscaler concentration is
both a strength and a risk.

It is a strength because a small number of customers can absorb massive volumes,
standardize on a platform, and fund multi-year AI infrastructure buildouts. It
is a risk because those same customers can delay capex, digest prior purchases,
push for price concessions, build internal ASICs, or shift networking choices.

Ask:

- Are cloud capex increases specifically tied to AI compute, or broad data
  center spending?
- Are customers buying for their own models, for resale through cloud capacity,
  or for strategic positioning?
- Is demand concentrated in training, inference, sovereign AI, or enterprise
  workloads?
- Are customers deploying systems quickly enough to justify more orders?

## Export controls and H20

Export controls belong in the operating model, not the footnotes. They can
reduce addressable revenue, force product redesigns, change customer mix, and
create charges when inventory or purchase commitments can no longer be used as
planned.

NVIDIA's H20-related charge in fiscal 2026 is a clean case study. The lesson is
not only "China revenue is risky." The broader lesson is:

```text
Policy change
  -> product eligibility changes
  -> shipment plan changes
  -> inventory and purchase obligations may be impaired
  -> gross margin and guidance can move abruptly
```

When reading future filings, look for whether management assumes China data
center compute revenue, whether alternate products are allowed, and whether
restrictions affect only direct sales or also cloud access, service, and
re-export paths.

## System-level margin tradeoffs

Selling more complete systems can strengthen customer lock-in and raise the
dollar content per deployment. It can also pressure margins because the system
contains more non-GPU content, logistics, testing, networking, cooling, and
partner work.

Do not assume system revenue has the same margin shape as accelerator boards.
Ask:

- Is gross margin moving because of product transition, export charges, mix, or
  pricing?
- Is NVIDIA capturing value from networking and software, or passing through
  more third-party hardware cost?
- Are rack-scale systems reducing customer friction enough to justify any lower
  margin percentage?
- Does a lower margin percentage still produce higher gross profit dollars?

For a systems company, margin percentage and strategic control can move in
opposite directions for a while.

## Custom ASICs can coexist with NVIDIA

Hyperscalers build internal accelerators because they control workloads and want
cost, power, supply-chain leverage, and architectural specialization. That is a
real competitive threat. It is not automatically an existential one.

Custom ASICs are most compelling for stable, high-volume inference workloads
where the buyer controls the software stack and can tolerate the engineering
cost. NVIDIA is most compelling where workloads change quickly, training
performance matters, software maturity matters, clusters need to be deployed
quickly, or customers lack the scale to build a full stack.

The coexistence thesis:

| Workload / buyer | Why custom ASIC can win | Why NVIDIA can still win |
|---|---|---|
| Hyperscaler internal inference | Massive volume, known models, full-stack control | Fast-changing models, overflow demand, software maturity |
| Frontier training | Cost pressure over time | Time-to-train, ecosystem, interconnect, roadmap confidence |
| Enterprise AI | Lower-cost alternatives may emerge | Customers want supported platforms, not chip projects |
| Sovereign AI | Domestic or strategic sourcing pressure | Need for proven deployment and software stack |

The key question is not "ASICs or NVIDIA?" It is "which workloads are stable
enough to specialize, and which still pay for flexibility?"

## Bull / base / bear case

| Case | What has to be true | Evidence to watch | Main risk |
|---|---|---|---|
| Bull | Blackwell and successors ramp cleanly; HBM and packaging expand; networking attach rises; CUDA remains the default; hyperscaler and sovereign demand stay strong | Data Center growth, high gross margin, supplier capex, cloud capex, networking revenue, deployment commentary | Power, packaging, or policy becomes the binding constraint |
| Base | NVIDIA remains the default AI platform, but growth normalizes as customers digest capacity and system mix adds cost | Stable demand, margin normalization, mixed Hopper/Blackwell shipments, continued customer concentration | Investors mistake slower growth for thesis failure |
| Bear | Customers overordered, ASICs take meaningful internal workloads, export controls limit geographies, and system complexity compresses margins | Inventory, weaker guidance, lower cloud capex, margin pressure, non-NVIDIA networking wins | The installed base and software moat slow the downside |

## What students should watch next

- Product transition: Hopper mix, Blackwell shipments, Blackwell Ultra timing,
  and any Rubin-related customer commitments.
- HBM: supplier qualification, generation transitions, stack attach, and memory
  maker capex.
- Advanced packaging: CoWoS-like capacity, package yields, substrate supply,
  and whether packaging remains the gating item.
- Networking attach: NVLink/NVSwitch, InfiniBand, Spectrum-X Ethernet, optics,
  and customer choices in large clusters.
- Gross margin: product mix, rack-scale system cost, export charges, and
  purchase obligations.
- Hyperscaler capex: whether spending converts into deployed AI capacity or
  pauses for digestion.
- Export controls: China revenue assumptions, H20 successor products, license
  requirements, and cloud access restrictions.
- ASIC competition: internal accelerator deployment, workload scope, software
  maturity, and whether customers still buy NVIDIA for flexible capacity.

## Analyst conclusion

NVIDIA is best analyzed as an AI infrastructure systems company sitting on top
of a semiconductor supply chain. Its upside comes from controlling the most
valuable customer-facing layer of AI compute. Its risk comes from needing many
upstream bottlenecks to clear at once while customers, competitors, and policy
makers all adapt.

## Recap

For NVIDIA, the question is not only "how many GPUs can be fabbed?" The better
question is "how many complete, qualified, powerable, networked AI systems can
be delivered to customers under current supply and policy constraints, and how
much of the cluster economics does NVIDIA keep?"
