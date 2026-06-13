# A Supply Chain Is a Feedback System

The naive picture is linear:

```mermaid
flowchart LR
  S[Supplier] --> F[Factory] --> W[Warehouse] --> R[Retailer] --> C[Customer]
```

Real supply chains are feedback systems. Demand signals travel upstream, capacity and inventory decisions travel across time, and disruptions can create second-order effects far away from the original event.

## Four flows

Every rigorous supply-chain model separates at least four flows.

| Flow | What moves | Common failure mode |
|---|---|---|
| Physical | parts, products, containers, returns | late, damaged, blocked, misallocated |
| Information | forecasts, orders, inventory records, status | delayed, distorted, stale, incompatible |
| Financial | payments, credit, working capital, penalties | cash tied in inventory, supplier distress |
| Risk | exposure to shortages, quality, policy, weather, labor | hidden concentration or correlated failure |

The physical flow cannot be fixed by transportation alone if the information flow is poor. A perfect forecast cannot help if the supplier contract has no flexibility. A resilient sourcing plan can still fail if working capital is exhausted before recovery.

## State variables

A useful model tracks state variables instead of only events:

- on-hand inventory
- on-order inventory
- backlog
- available capacity
- supplier commitments
- transportation slots
- cash tied in inventory

The state at time $t$ determines what decisions are feasible at time $t+1$.

## Buffers and decoupling

Buffers absorb variability. Inventory is the visible buffer, but not the only one. Capacity slack, lead-time slack, supplier options, alternate routings, and cash reserves are also buffers.

A decoupling point is where the system switches from forecast-driven to order-driven behavior. A make-to-stock snack brand decouples at finished goods inventory. A custom industrial equipment maker may decouple at raw materials or even engineering capacity.

## Local objectives can damage the system

A purchasing team rewarded only for unit price may choose a distant low-cost supplier, raising lead time, pipeline inventory, minimum order quantities, and disruption exposure. A factory rewarded only for utilization may run large batches that overload warehouses and hide demand changes.

The course repeatedly asks:

1. What is the system objective?
2. Which constraint is binding?
3. Which uncertainty matters?
4. Which local incentive could make the global outcome worse?
