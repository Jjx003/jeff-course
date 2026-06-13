# Network Flow and Capacity

Supply-chain capacity questions often reduce to flow through a constrained network. A supplier may have enough output, but the port, lane, warehouse, or final assembly line can still bind.

![Supply network capacity map with a binding outbound lane](/courses/supply-chain-systems/network-capacity-map.svg)

Implement a small max-flow solver using the Edmonds-Karp algorithm. Your program should compute the maximum weekly flow from raw-material suppliers to customer demand through intermediate capacity constraints.

The starter code defines a network with these arcs:

- source to two suppliers
- suppliers to two plants
- plants to a warehouse and direct demand
- warehouse to demand

Submit when your output matches the expected maximum flow and the flows on selected arcs.
