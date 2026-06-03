# Last-minute tips

## Do the units first

Many mistakes in optimization work are unit mistakes in costume. Convert:

- bits to bytes,
- parameters to storage,
- rank factors to trainable parameters,
- context length to cache growth,
- sequence length to pair-representation growth.

If a number feels too large or too small, check whether you multiplied by bits
instead of bytes.

## Separate mechanism from benefit

For each named technique, state both:

```text
Mechanism: what changes?
Benefit: which bottleneck improves?
```

Examples of mechanisms include tiling, caching, paging, low-rank adaptation,
quantization, greedy packing, and proposal-verification. The benefit might be
less memory traffic, lower memory capacity, better utilization, lower latency,
or reduced padding waste.

## Watch for category errors

- A serving-memory technique is not automatically a quality improvement.
- A compression technique is not automatically a scheduler.
- A protein confidence score is not automatically an affinity score.
- A monomer structure result is not automatically an interface result.
- A faster candidate screen is not useful if it discards the candidates the
  experiment needed.

## Review after the test

When the results appear, sort misses by cause:

- arithmetic or units,
- phase confusion,
- exactness vs approximation,
- serving resource confusion,
- protein workload confusion.

That review is more valuable than the raw score. The whole course is a toolbox;
the final test checks whether you can pick the right tool for the bottleneck in
front of you.
