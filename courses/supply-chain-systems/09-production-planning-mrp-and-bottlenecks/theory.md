# MRP Logic

Material requirements planning starts with a master production schedule and explodes it through the bill of materials.

For each component:

1. compute gross requirements
2. subtract projected available inventory
3. account for scheduled receipts
4. create planned order receipts
5. offset by lead time to create planned order releases

## Dependent demand

Component demand is dependent on parent production. If each finished unit uses 4 fasteners and the plan builds 1,000 units, gross fastener demand is 4,000 units before scrap, safety stock, and timing adjustments.

## Infinite versus finite capacity

Classic MRP can produce a material plan that assumes capacity exists. Finite-capacity planning asks whether machines, labor, tooling, and changeover windows can actually execute the plan.

## Bottleneck management

A bottleneck is the resource that constrains system throughput. Improving a non-bottleneck may improve local utilization while leaving total output unchanged.

The theory of constraints focuses attention on:

- identify the constraint
- exploit the constraint
- subordinate other decisions to the constraint
- elevate the constraint
- repeat when the constraint moves

## Changeovers and batch size

Large batches reduce changeover losses but increase inventory and delay. Small batches improve responsiveness but can starve capacity if setup times are large. The right batch size depends on the bottleneck, not only the local work center.
