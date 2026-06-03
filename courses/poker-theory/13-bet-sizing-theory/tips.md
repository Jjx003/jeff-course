# Tips & Hints

## Remembering Geometric Sizing

**Step 1 — Find SPR:** Divide effective stacks by the current pot. SPR = stacks / pot.

**Step 2 — Find g:** Take the $n$th root of SPR, where $n$ = streets remaining. On a calculator: $g = \text{SPR}^{1/n}$.

**Step 3 — Find the bet:** Bet = $(g - 1) / 2 \times$ current pot. This gives the fraction of pot to bet on *this* street.

**Mental check:** If $g = 2$, you bet 50% of pot each street. If $g = 3$, you bet pot-sized. If $g = 1.5$, you bet 25% of pot. Memorise these three anchors.

---

## Common Mistakes

**Not adjusting for position:** A 75% pot OOP bet is much harder to balance than the same bet IP. Start with conservative sizes OOP until you can find solver-level balancing.

**Using geometric sizing on non-all-in lines:** Geometric sizing is designed specifically for building to an all-in. If you are not planning to commit stacks, use range-based sizing instead.

**Forgetting the bluff requirement for overbets:** If you cannot supply enough bluffs (a 2× pot overbet needs a bluff fraction of B/(P+2B) ≈ 40% of your betting range, a 3:2 value-to-bluff ratio), do not overbet. Your value hands need protection from villain's exploitative always-fold.

**Conflating protection and value:** A protection bet is not the same as a value bet. Protection bets charge draws; value bets extract money from worse made hands. On some boards you need both — a merged range bet does double duty. But if you label every small bet "protection," you are probably betting hands you should check.

---

## Going Deeper

- **"Applications of No-Limit Hold'em"** (Matthew Janda) — Chapters 6–9 cover sizing theory with worked examples for every common spot.
- **"Play Optimal Poker"** (Andrew Brokos) — Accessible treatment of merged vs polarised ranges with practical exploitative adjustments.
- **PioSolver / GTO+ node locking** — Run a flop spot and compare solver bet sizes on different board textures. Notice how the solver uses larger sizes when it has a range advantage.
- **"The Grinder's Manual"** (Peter Clarke) — Chapter on bet sizing discusses IP vs OOP asymmetries in detail with hand histories.
- **Modern Poker Theory** (Michael Acevedo) — Geometric sizing derivation and SPR tables across common stack depths.
