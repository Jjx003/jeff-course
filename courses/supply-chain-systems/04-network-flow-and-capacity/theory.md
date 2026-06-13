# Flow Networks

A flow network has directed arcs with capacities. The question is how much material can move from a source to a sink without exceeding any arc capacity.

For each arc $(u,v)$:

$$
0 \le f(u,v) \le c(u,v)
$$

At every intermediate node, flow conservation holds:

$$
\sum_i f(i,v) = \sum_j f(v,j)
$$

## Residual capacity

If an arc has capacity 20 and current flow 13, it has 7 units of forward residual capacity. The residual graph also includes reverse capacity, allowing an algorithm to undo earlier choices.

## Edmonds-Karp

Edmonds-Karp repeatedly finds the shortest augmenting path in the residual graph using breadth-first search. It augments by the smallest residual capacity on that path. The algorithm is not the fastest max-flow method, but it is transparent and good for small planning models.

## Supply-chain interpretation

The final max flow is not just a number. The binding arcs explain what investment or recovery action matters. If warehouse outbound capacity binds, adding supplier output will not improve customer fill until the warehouse lane is fixed.
