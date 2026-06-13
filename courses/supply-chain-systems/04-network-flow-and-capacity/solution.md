# Solution Walkthrough

The residual graph records what can still be pushed forward and what can be undone through reverse arcs.

Breadth-first search finds an augmenting path from `source` to `demand`. For each path, compute the bottleneck residual capacity, then subtract that amount along the forward arcs and add it on the reverse arcs.

The final max flow is 60 units. Customer demand can receive 25 units through direct plant-to-demand arcs and 35 through the warehouse arc. The warehouse-to-demand lane is saturated, so extra plant-to-warehouse capacity would not increase fulfilled demand unless outbound capacity also improves.
