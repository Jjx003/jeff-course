# Solution walkthrough

First-fit decreasing is a simple greedy packing heuristic. It is not perfect, but it is often good enough to reduce padding waste sharply.

For pure PLM embedding, packed batches can increase GPU utilization. For folding models, use this idea carefully because pair representations and chain boundaries add constraints.

