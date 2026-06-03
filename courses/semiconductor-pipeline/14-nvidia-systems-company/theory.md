## Mini-model: from chip to system

Think of NVIDIA shipments as the minimum of several capacities:

$$
\text{systems shipped} =
\min(C_\text{logic}, C_\text{HBM}, C_\text{package}, C_\text{network}, C_\text{power}, C_\text{customer readiness})
$$

That expression is not a financial forecast. It is a discipline: never forecast
the finished system from compute die supply alone.

You can extend the model to economics:

$$
\text{gross profit dollars} =
\text{systems shipped} \times \text{ASP per system} \times \text{gross margin}
$$

The three terms can fight each other. A full rack system can increase ASP and
strategic control while lowering percentage margin. A constrained HBM supply can
limit systems shipped while supporting pricing. A policy charge can reduce gross
margin even if demand remains strong.

## The system bottleneck stack

For each product generation, build a bottleneck table:

| Layer | NVIDIA-controlled? | Constraint question |
|---|---|---|
| GPU architecture | Mostly yes | Is the new generation delivering enough performance per watt and per dollar? |
| Foundry process | No | Does NVIDIA have sufficient wafer allocation and yield? |
| HBM | No | Are enough qualified stacks available at the required generation and density? |
| Advanced packaging | No, but deeply coordinated | Can logic and HBM be packaged at the needed volume and yield? |
| Board / rack design | Partly | Are thermal, power, and serviceability problems solved? |
| Networking | More yes after Mellanox | Does NVIDIA attach enough scale-up and scale-out fabric value? |
| Software | Mostly yes | Do customers stay inside CUDA and NVIDIA deployment tooling? |
| Customer data center | No | Can sites power, cool, network, and operate the systems? |
| Policy | No | Are products legal to ship to the intended customers and geographies? |

This table keeps the thesis honest. NVIDIA can control the highest-value layer
and still be gated by suppliers or customer infrastructure.

## Attach-rate thinking

SemiAnalysis-style company work often asks "what attaches to the scarce thing?"
For NVIDIA, the scarce thing is not only a GPU. It can be a validated AI cluster
slot. Attach can include:

- HBM per accelerator.
- NVLink and NVSwitch inside the node or rack.
- InfiniBand or Ethernet networking across nodes.
- DPUs or NICs.
- Software subscriptions, support, and enterprise runtimes.
- Reference designs and validated system partners.

The more content NVIDIA attaches to each deployment, the more it behaves like a
systems company. The risk is that customers may accept the accelerator while
substituting networking, software, or integration layers.

## Why custom ASICs do not automatically kill NVIDIA

Hyperscalers build internal accelerators because they control workloads and
want cost, power, and supply-chain leverage. But custom ASICs still need:

- Process-node access.
- HBM allocation.
- Packaging capacity.
- Compilers and kernels.
- Cluster networking.
- Deployment operations.
- Enough stable workload volume to justify the design cycle.

NVIDIA can lose share in some workloads and still keep pricing power where
customers value time-to-train, software maturity, flexible capacity, and cluster
integration. The more fragmented the workload, the more valuable the general
platform. The more stable and massive the workload, the more attractive the
custom path.

## Why export controls matter financially

Export controls do not only reduce revenue opportunity. They can create charges
when a company has inventory or purchase commitments for products that can no
longer ship as planned. They can also force a company to design lower-capability
regional products, reroute supply, or exclude a geography from guidance.

That is why policy analysis belongs in a semiconductor company model. A strong
technical product can still become a weak commercial product if its reachable
market changes.

## Red flags and counter-signals

| Signal | Why it matters |
|---|---|
| Gross margin down without a one-time explanation | Could mean system mix, pricing, charge, or transition friction |
| Inventory or purchase obligations rising faster than revenue | Could indicate confidence, but also write-down risk |
| Hyperscaler capex pauses | Demand may be digesting prior purchases |
| Networking attach weakens | NVIDIA may capture less cluster value |
| HBM suppliers guide to oversupply | Accelerator scarcity may ease |
| Customers emphasize internal ASICs | Some workloads may be moving away from general GPUs |
| Export rules change again | Product eligibility and guidance can move abruptly |

None of these is automatically fatal. They are places where the thesis should
be re-underwritten.
