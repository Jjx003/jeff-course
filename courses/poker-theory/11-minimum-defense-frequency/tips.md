# Tips & Hints

## Mental Shortcuts for MDF at the Table

**The pot-bet anchor:** For a pot-sized bet, MDF is exactly 50% — memorise this. Then adjust: smaller bets mean higher MDF (you must defend more), larger bets mean lower MDF (you need to defend less).

**Fraction form:** $\text{MDF} = \frac{P}{P + B}$. If the pot is \$100 and the bet is \$50, the denominator is \$150, so MDF = 100/150 = 2/3 ≈ 67%.

**Complement trick:** Once you know alpha ($B / (P+B)$), MDF is just the remainder: if alpha = 33%, MDF = 67%. You only need one calculation.

---

## Common Mistakes

**Confusing alpha and MDF:** Alpha is the fold % the defender *can* afford; MDF is the call % they *must* reach. Alpha tells you how many bluffs to include in your range; MDF tells you how often to defend. They are complementary, not the same number.

**Forgetting MDF applies to your whole *range*, not individual hands:** MDF doesn't say "call with hands above X equity." It says "your overall defense frequency across all hands must be at least MDF." In practice you defend with your best hands, but the *total fraction* must hit MDF.

**Treating multi-street MDF additively:** The three-street combined defense frequency is *multiplicative*, not additive. Three streets of 67% MDF gives $0.67^3 \approx 30\%$, not 67% × 3 = 201%.

---

## Going Deeper

- **"The Mathematics of Poker"** (Bill Chen & Jerrod Ankenman) — Chapter 9 gives the full game-theoretic derivation of optimal bluff and defense frequencies with rigorous proofs.
- **"Applications of No-Limit Hold'em"** (Matthew Janda) — Chapter 3 translates MDF into practical range-construction workflows for Texas Hold'em.
- **PioSolver / GTO+** — Solver outputs show actual defense frequencies by position and board texture. Run a simple river spot and check whether the solver's call frequency matches the MDF formula.
- **"Modern Poker Theory"** (Michael Acevedo) — covers bluff-to-value ratios in depth and includes worked examples for common river bet sizes.
