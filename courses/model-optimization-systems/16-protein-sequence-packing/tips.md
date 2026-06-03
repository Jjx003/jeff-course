# Hints

## Implementation hints

- Keep each item as a `(name, length)` pair so the printed bins remain readable.
- Sort by length descending before packing.
- Represent each pack as a list of pairs plus a running used-token count.
- Capacity is 1024 tokens per pack.
- For each sequence, scan packs in their current order and place it into the
  first pack with enough remaining capacity.
- If no pack has room, create a new pack.

## Naive baseline hints

For the naive padded-token count, do not sort first. Use the original list in
groups of 4. For each group:

1. find the maximum length,
2. multiply by the group size,
3. add that to the total.

This baseline represents a simple batching system before length bucketing or
packing.

## Common mistakes

- Sorting ascending instead of descending.
- Counting useful residues instead of allocated packed capacity.
- Applying batch size 4 after sorting instead of using the original order for
  the naive baseline.
- Forgetting that the last naive batch may have fewer than 4 sequences.
- Printing extra diagnostics that break expected output.

## Going deeper

After the lab, try comparing three policies:

- original-order naive batching,
- length-bucketed batching without packing,
- first-fit decreasing packing.

That comparison is close to what you would do before optimizing a real PLM
embedding job. First measure waste. Then choose the simplest policy that removes
most of it.
