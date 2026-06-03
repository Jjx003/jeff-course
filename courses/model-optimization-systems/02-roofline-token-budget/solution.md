# Solution walkthrough

The key move is keeping units straight.

Weights use decimal GB because bandwidth is usually reported in GB/s. Cache capacity is printed in GiB because GPU memory capacity is usually closer to binary units.

GQA changes only the KV-head count in this estimate. The difference between 8 KV heads and 64 KV heads is an 8x cache reduction.

