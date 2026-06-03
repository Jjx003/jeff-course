## How to analyze a news item

When reading a supply-chain report, rewrite it into this template:

```text
The constrained step is ______.
New qualified capacity takes about ______.
Customers can/cannot substitute because ______.
The supplier with pricing power is ______.
The geopolitical exposure is ______.
```

If you cannot fill in those blanks, the claim is probably too vague to trade on
or build an operating plan around.

## Common traps

- Counting wafer starts when the real constraint is HBM attach.
- Counting HBM bits when the package cannot support the stack count.
- Treating announced capacity as qualified capacity.
- Assuming a second supplier is usable before reliability and customer
  qualification are complete.
- Ignoring export controls because the constrained item is "only software" or
  "only a component."

## Going deeper

- Build a bottleneck table for one AI accelerator: logic wafer, HBM, package,
  substrate, board, networking, power, and data-center deployment.
- For each row, estimate lead time and switching cost.
- Then ask which supplier could raise price without losing the order.
