# Intel Foundry: the turnaround case

Intel is the hardest company in this set because it is both a product company
and a manufacturing turnaround. The analyst question is not "can Intel make
chips?" It is:

> Can Intel turn internal manufacturing assets into a competitive external
> foundry business without burning too much cash before customer trust arrives?

As of May 2026, Intel's 2025 10-K says Intel ramped Intel 18A into high-volume
production and is seeking to establish it as the first significant node for
government and enterprise foundry customers. The same filing reports Intel
Foundry operating loss of $10.3 billion in 2025, compared with a $13.3 billion
loss in 2024. It also warns that if Intel cannot secure a significant external
customer and meet important milestones for Intel 14A, it may not be economical
to develop and manufacture 14A and successor leading-edge nodes.

That filing language is unusually important. It turns 14A from a normal roadmap
item into a test of whether Intel Foundry can earn enough external demand to
justify remaining at the leading edge.

## Controlled capability

Intel controls:

- U.S.-based leading-edge manufacturing assets.
- Internal CPU product volume to seed new nodes.
- Advanced packaging capabilities.
- Government and national-security relevance.
- A long history of process technology know-how.

But a foundry needs more than technology. It needs external customer trust,
predictable PDKs, design enablement, IP, EDA support, competitive cost, yield,
capacity assurance, and a customer-service culture. TSMC's moat is not only
transistors; it is the whole habit of customer success around the transistor.

## RibbonFET and PowerVia in plain English

Intel 18A is associated with two big process claims:

- **RibbonFET**: Intel's gate-all-around transistor. Instead of controlling the
  channel from a few sides, the gate wraps more fully around thin silicon
  ribbons. The intuitive goal is better control of current as transistors shrink.
- **PowerVia**: backside power delivery. Instead of routing power and signals
  through the same front-side metal congestion, power can be delivered from the
  back side of the wafer. The intuitive goal is cleaner routing, lower resistance,
  and more room for signal interconnect.

These are real architectural changes, not just marketing labels. The risk is
that new process features can create yield, design-rule, thermal, and EDA
complexity. A foundry customer does not only ask "is the feature elegant?" It
asks "can my design team close timing, get working silicon, and ship on time?"

## The 18A / 14A issue

Intel 18A is the proof point for the turnaround. If 18A ramps with acceptable
yield, Intel can support internal products and show external customers that its
process roadmap is credible.

Intel 14A is the larger strategic test. A future leading-edge node needs enough
volume to pay for R&D, high-NA EUV tools, process development, IP enablement,
and capacity. If Intel cannot land meaningful external customers for 14A-class
manufacturing, the economics of staying at the leading edge become harder.

Do not treat "18A works" and "Intel Foundry wins" as the same claim:

| Question | Why it matters |
|---|---|
| Can Intel ship internal products on 18A? | Proves process and product execution inside Intel |
| Can an external customer tape out smoothly on 18A/18A-P? | Tests foundry enablement and customer service |
| Can Intel land a major 14A external customer? | Tests whether future leading-edge economics can scale |
| Can 14A hit milestones without massive underutilization? | Tests capital intensity and return on invested capital |

## PDK, IP, and EDA ecosystem

Foundry customers need a design ecosystem before they risk a major chip:

- PDKs must be accurate, stable, and available early enough.
- EDA tools must support the process rules, extraction, timing, power, and
  physical verification.
- Standard cells, SRAM compilers, high-speed IO, SerDes, PCIe, HBM PHYs, and
  other IP must be proven.
- Packaging reference flows must connect die, interposer, substrate, thermals,
  and test.
- The support organization must help customers debug problems without exposing
  confidential information to Intel product groups.

This is why named customer volume matters more than generic "interest." A
customer can evaluate a PDK for years without committing a flagship product.

## Internal volume helps but does not solve it

Internal Intel products can seed a node, absorb early capacity, and help debug
process problems. That is valuable. But internal volume can also hide whether
the foundry is competitive with external customers.

Key distinction:

- **Internal volume** proves Intel can use its own factories for its own product
  roadmap.
- **External volume** proves other companies trust Intel with their roadmap,
  economics, IP, and schedule.

If Intel product groups outsource important tiles to TSMC while Intel Foundry
needs utilization, students should ask why. Sometimes outsourcing is a rational
product decision. Sometimes it is evidence that the internal foundry is not yet
the best option for Intel's own products.

## Product-versus-foundry conflicts

Intel wants to be both a chip designer and a merchant foundry. That creates
trust questions:

- Will an external CPU, GPU, AI accelerator, or networking customer trust a
  supplier that may compete with it?
- Can Intel separate customer confidential information from internal product
  teams?
- Will manufacturing decisions prioritize Intel products or external foundry
  customers during shortage?
- Can Intel offer neutral IP, EDA, and packaging support without steering the
  roadmap toward internal needs?

This is not impossible. Samsung also runs both product and foundry businesses.
But TSMC's pure-play model is a customer-trust advantage, and Intel has to earn
its way around that objection.

## Advanced packaging

Intel's packaging assets can be a real differentiator. AI accelerators and HPC
chips increasingly need chiplets, high-bandwidth memory, interposers, bridge
technologies, high-density substrates, thermal solutions, and system-level test.

The packaging bull case is that a customer may not need Intel to beat TSMC on
every wafer metric if Intel can offer a compelling secure package, domestic
manufacturing path, or chiplet assembly solution. The caveat is that packaging
does not fully rescue wafer economics if leading-edge fabs are underutilized.

## CHIPS and government support

Intel's U.S. manufacturing footprint makes it strategically important. CHIPS Act
support and secure-enclave programs can help bridge the economics of domestic
capacity. Government demand can also create non-price reasons to use Intel.

But subsidies do not create foundry competitiveness by themselves. Customers
still need cost, yield, reliability, capacity, confidentiality, and design
support. Government money can buy time; it cannot replace execution.

## Operating losses, depreciation, and utilization

The foundry loss is not automatically bad. A foundry ramp can lose money before
it scales. Depreciation, startup costs, underutilized tools, R&D, and yield
learning can hit the income statement before revenue arrives.

The question is whether losses are buying future customer trust or merely
funding underutilized capacity.

Drill-down questions:

- Are losses narrowing because utilization is improving, or because one-time
  impairments and accelerated depreciation are rolling off?
- Is gross margin improving after adjusting for restructuring and unusual
  charges?
- Are capex cuts preserving cash but weakening the future roadmap?
- Is internal product volume enough to fill the fabs during customer ramp?
- Are external customers committing wafer starts or only evaluating technology?

## Bull/base/bear setup

| Case | What has to be true | Evidence to seek | Main risk |
|---|---|---|---|
| Bull | 18A ramps well, 18A-P/14A milestones hold, Intel wins at least one meaningful external 14A-class customer, and packaging plus government demand create differentiated volume | Named customer commitments, stable PDKs, successful external tapeouts, narrowing losses from utilization, internal products using Intel nodes confidently | Technical success still may not overcome TSMC ecosystem inertia |
| Base | Intel uses 18A for internal products and select government/enterprise foundry work, but broad merchant foundry adoption is slow; 14A remains conditional | Internal product ramps, limited external wins, losses narrow but stay large, CHIPS support extends runway | The business consumes capital without proving scale |
| Bear | 18A execution disappoints or remains mostly internal, 14A lacks a major external customer, product teams outsource more key tiles, and foundry losses persist | Delays, vague customer language, underutilization, roadmap pauses, restructuring that removes technical depth | Government support delays recognition of weak commercial demand |

## What to watch

- 18A yield, product launch timing, and whether ramps are described with hard
  volume evidence rather than adjectives.
- 18A-P and 14A milestones, including whether 14A remains economically justified.
- Named external customers, tapeouts, and wafer-volume commitments.
- PDK maturity, EDA support, and availability of critical IP.
- Intel product tiles: which are internal versus external foundry?
- Foundry operating loss, depreciation, utilization, and one-time charges.
- Advanced packaging wins that include real system volume.
- CHIPS/government awards, but only as one part of the economics.
- Customer-trust signals: confidentiality structure, service model, and repeat
  engagements.

## Source-aware caveats

Intel disclosures mix hard facts, roadmap goals, and risk factors. Treat SEC
filings as more important than launch-event language, but remember filings are
still written by the company and often lag operating reality. Third-party yield
reports can be useful disconfirming evidence, but they are often sourced
indirectly and may not map cleanly to final product yield.

## Analyst conclusion

Intel Foundry is a high-upside, high-execution-risk turnaround. The bullish case
is strategic U.S. leading-edge capacity plus recovered process credibility. The
bearish case is that foundry economics require customer trust and utilization
faster than Intel can earn them. The student move is to separate process
technology milestones from foundry business proof.
