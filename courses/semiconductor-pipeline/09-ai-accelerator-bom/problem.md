# AI Accelerator Bill of Materials

An AI accelerator is often discussed as if it were one chip. In practice, a training or inference system is a stack of tightly coupled parts: a compute die, high-bandwidth memory, advanced package, board, network interface, optics, power delivery, cooling hardware, rack design, and cluster software. A bottleneck in any one layer can slow shipment of the whole system.

![AI accelerator system bill of materials](/courses/semiconductor-pipeline/ai-accelerator-bom.png)

*A bill-of-materials view of an AI accelerator system. The compute die is only
one dependency; HBM, packaging, boards, networking, optics, power, cooling, and
rack deployment can all become shipment constraints.*

![Front of server racks in a data center](/courses/semiconductor-pipeline/nersc-server-racks.jpg)

*Server racks in a real data center. This is where packaged accelerators become
usable compute: installed into boards, servers, racks, networks, power feeds,
cooling systems, and operations software.*

This module builds a bill-of-materials view of an accelerator system. The goal is not to memorize every vendor, but to see why semiconductor analysts trace dependencies across wafers, memory, substrates, connectors, power modules, thermal systems, and data-center networking.

## The accelerator is a system, not a die

At the center is the **compute die**: a large logic chip full of matrix engines, vector units, SRAM, interconnect, cache, and control logic. NVIDIA GPUs, Google TPUs, Amazon Trainium, AMD Instinct parts, and other custom ASICs differ in architecture, software stack, and deployment model. Yet they all face the same physical problem: move enormous tensors through a limited amount of silicon area, power, memory bandwidth, and network bandwidth.

A modern AI system therefore looks more like a miniature data center module than a single component:

| Layer | What it does | Common constraint |
|---|---|---|
| Compute die | Runs matrix and tensor operations | Advanced-node wafer supply, reticle-limited die size, yield |
| HBM stack | Feeds the die with high-bandwidth memory | HBM capacity, known-good-die matching, TSV process yield |
| Advanced package | Places compute and HBM close together | CoWoS-like capacity, interposer/substrate availability |
| PCB/baseboard | Routes power and signals | High-layer-count board complexity |
| NIC / scale-up link | Connects accelerators within a server or rack | SerDes, switch silicon, protocol ecosystem |
| Optics | Carries data across racks or clusters | Transceiver supply, lasers, packaging, power |
| Power delivery | Converts facility power to chip rails | VRMs, power stages, copper, efficiency |
| Cooling | Removes hundreds to thousands of watts | Cold plates, pumps, manifolds, facility water |
| Rack/cluster | Turns nodes into a usable machine | Scheduling, topology, reliability, deployment speed |

## Compute die

The compute die is usually manufactured on an advanced logic node because performance per watt matters. Training workloads reward dense tensor units and fast on-die memory; inference workloads often emphasize latency, cost, and power. A custom ASIC can remove flexibility that is not needed for a specific workload, but it still depends on the same upstream ecosystem: EDA tools, IP blocks, foundry process design kits, masks, wafers, packaging, test, and assembly.

For a large accelerator, the die may be close to the reticle limit. Larger dies can offer more compute and SRAM, but yield tends to fall as die area rises because a single defect can ruin a die. Designers manage this with redundancy, binning, chiplets, and packaging choices.

## HBM

High-bandwidth memory is the memory wall workaround. Instead of using only external DIMMs, HBM stacks DRAM dies vertically and connects them with through-silicon vias. The stack sits next to the compute die on an advanced package, giving the accelerator a very wide, short memory interface.

HBM changes the supply chain:

- DRAM makers must allocate wafer starts to HBM rather than commodity DRAM.
- The stack needs assembly, bonding, test, and known-good-die discipline.
- The accelerator vendor must match logic die, HBM stacks, interposer, and substrate into one working module.
- Capacity depends on both memory fabrication and advanced packaging throughput.

When AI demand spikes, HBM can become the gating item even if the logic die itself is available.

## Advanced package

The package is the bridge between compute and memory. In a conventional package, memory is farther away and the interface is narrower. In an AI accelerator package, the compute die and HBM stacks sit on an interposer or bridge structure with dense routing.

This is why analysts track advanced packaging capacity separately from wafer capacity. A foundry may have enough leading-edge wafers, while the packaging line that assembles large interposer modules is fully booked. The package also interacts with substrate supply, test equipment, thermal design, and final board assembly.

## Board, NIC, and networking

One accelerator rarely trains a frontier model alone. Systems scale by connecting many devices inside a server, then many servers inside a rack, then many racks inside a cluster. The board must route high-speed signals while delivering stable current to the package. The network interface card or embedded networking silicon connects the accelerator to the rest of the fabric.

Two networking ideas matter:

1. **Scale-up** connects accelerators that behave almost like one large machine. Latency and bandwidth are critical.
2. **Scale-out** connects servers and racks across the cluster. Ethernet, InfiniBand-like fabrics, switches, cables, and optics all become part of the accelerator story.

NVIDIA's advantage is not only GPU silicon. It also includes CUDA, libraries, networking, systems, and a deployment model. TPU-style systems and custom ASIC programs can be compelling when a hyperscaler controls the workload and data center, but they still require memory, packaging, networking, power, and cooling at scale.

## Optics

Electrical signaling works well over short distances, but clusters eventually need optical links. Transceivers convert electrical signals into light and back again. For AI clusters, optics can become a material part of capital cost and power draw because network traffic is intense.

Optics add their own dependency tree: lasers, modulators, DSPs, packaging, fiber management, test, and switch compatibility. If a cluster design requires a specific generation of high-speed optics, shortages there can delay deployments even when accelerator modules are ready.

## Power and cooling

Accelerators consume large amounts of power, and power must be delivered at low voltage with tight tolerances. Voltage regulator modules, power stages, inductors, capacitors, busbars, cables, and rack-level power distribution all matter. As power rises, copper and mechanical design become less boring than they look.

Cooling is equally central. Air cooling reaches limits as rack density rises. Liquid cooling adds cold plates, manifolds, pumps, quick disconnects, leak detection, and facility-side water loops. A cooler chip can hold boost clocks longer and fail less often, so thermal design becomes a performance feature rather than a housekeeping detail.

## Rack and cluster

At rack scale, the bill of materials becomes a topology. Accelerators, CPUs, NICs, switches, optics, storage, power shelves, and cooling loops must fit together. At cluster scale, software decides how well the hardware is used: schedulers place jobs, collective communication libraries move gradients, and reliability systems recover from failures.

This is where supply-chain analysis becomes systems analysis. A shipment forecast for AI accelerators needs more than "how many chips can the foundry make?" It may require answers to:

- How much HBM capacity is allocated to this vendor?
- Is advanced packaging capacity expanding fast enough?
- Are substrates, test sockets, and board assembly available?
- Does the networking bill require constrained switch silicon or optics?
- Can the data center deliver the power and cooling density?
- Does the software stack make the hardware useful enough to justify deployment?

## Recap

An AI accelerator system is a layered machine. The compute die is the visible center, but HBM, advanced packaging, boards, networking, optics, power delivery, cooling, racks, and cluster software determine whether that die becomes usable capacity. NVIDIA, TPU, and custom ASIC discussions all sit inside this broader ecosystem. The next module turns to policy: why export controls and domestic substitution show up in semiconductor analysis.
