## Mini-model: HBM revenue

For a memory maker:

$$
\text{HBM revenue} =
\text{qualified stacks shipped} \times \text{ASP per stack}
$$

The word **qualified** is doing the work. A stack that is not approved by the
customer, cannot be packaged into the accelerator, or fails power/thermal
requirements does not create the same economics.

## Full-stack constraint model

AI module output is limited by the scarcest required input:

$$
\text{modules shipped} =
\min(\text{logic dies}, \text{qualified HBM sets}, \text{advanced packages}, \text{system capacity})
$$

This is why HBM suppliers should be analyzed with foundries, OSATs, substrate
vendors, and accelerator customers. A supplier can have strong HBM execution
while the revenue ramp is capped by packaging or customer data-center readiness.

## HBM attach rate

Accelerator demand pulls HBM demand through attach rate:

$$
\text{HBM stacks demanded} =
\text{accelerators shipped} \times \text{stacks per accelerator}
$$

The memory content per accelerator can rise through more stacks, taller stacks,
or higher density per die. The analyst must separate these:

- **More accelerators shipped**: system demand is growing.
- **More stacks per accelerator**: architecture is increasing bandwidth demand.
- **Higher capacity per stack**: memory value rises even if unit count does not.
- **Higher ASP per stack**: scarcity or complexity is improving price.

## Yield intuition

HBM yield is not just DRAM die yield. A simplified intuition is:

$$
\text{stack yield} \approx
\text{known-good-die yield}^{\text{die count}}
\times \text{bond yield}
\times \text{test/package yield}
$$

The exact formula is more complex, but the intuition matters: taller stacks can
raise selling value while adding more places for yield loss. A supplier's edge
may come from boring execution: test flow, thermal control, bonding quality,
materials, and learning rate.

## Leading versus lagging indicators

| Indicator | Usually leads or lags? | Why it matters |
|---|---|---|
| Customer qualification | Leading | Determines who can ship premium HBM later |
| Capex and tool orders | Leading | Shows capacity intent before revenue appears |
| HBM allocation commentary | Leading | Suggests customer urgency and scarcity |
| Revenue growth | Lagging | Confirms shipments after qualification and packaging |
| Gross margin | Mixed | Reflects ASP, yield, mix, depreciation, and utilization |
| Inventory build | Lagging warning | Can reveal demand or qualification mismatch |

## The memory-cycle twist

Classic memory cycles are driven by supply additions and end-market demand. HBM
adds qualification timing. A supplier can have wafer capacity but miss the
highest-margin demand if it is late to customer qualification. Conversely, a
supplier with qualified HBM can earn premium economics while commodity DRAM is
only beginning to recover.

## Disconfirming evidence checklist

A good HBM thesis should name what would break it:

- Qualified second sources reduce the leader's allocation power.
- HBM ASPs fall while capacity is still ramping.
- Packaging remains the binding constraint, so memory output cannot monetize.
- AI customers lower HBM content per accelerator generation.
- DDR/server DRAM pricing weakens despite HBM mix shift.
- Capex growth outruns verified customer commitments.
