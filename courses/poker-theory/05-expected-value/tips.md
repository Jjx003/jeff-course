# Expected Value — Hints & Going Deeper

## Incremental Hints

### Hint 1 — Confused about which pot figure to use?
In the EV formulas, $P$ is the pot *before* your action. Your action adds chips to the pot. So when you call $C$, the pot becomes $P + C$ and your share of it is $q(P+C)$. When you bluff $B$, the pot becomes $P + B$ if called, but you lose $B$ of it.

### Hint 2 — Why does break-even fold frequency equal $B/(P+B)$?
The same algebra that gives you pot odds for calling gives you break-even fold frequency for bluffing — they are symmetric. You are "investing" $B$ to potentially "win" $P$. The investment-to-total-stake ratio is $B/(P+B)$, same structure as $C/(P+C)$.

### Hint 3 — When is a value bet bad?
A value bet reduces EV compared to checking when: (a) villain folds all worse hands and (b) always calls with better. In practice, look for spots where villain has a range that both calls and is beat by your hand. If villain's calling range dominates yours, betting is −EV even with a good hand.

### Hint 4 — How to estimate fold frequency?
Start with population tendencies (typical players fold roughly X% to continuation bets on various board textures). Then adjust for reads: tight player → fold more; calling station → fold less. Exact percentages are less important than knowing whether your estimate is above or below $B/(P+B)$.

### Hint 5 — EV calculations feel overwhelming?
Work through the decision tree step by step on paper. Label each branch with its probability and outcome. The sum of (probability × outcome) across all branches is your EV. Once you build intuition for the formula, the mental arithmetic becomes automatic.

---

## Going Deeper

- [*The Theory of Poker* — David Sklansky](https://www.twoplustwo.com/books/poker/theory-of-poker/) — The Fundamental Theorem of Poker (Chapter 3) is the original statement of EV maximisation as the central goal of poker strategy.
- [*Applications of No-Limit Hold'em* — Matthew Janda](https://www.twoplustwo.com/books/poker/applications-of-nolimit-holdem/) — Rigorous multi-street EV trees, bluffing frequencies, and value-betting ranges derived from first principles.
- [*No-Limit Hold'em for Advanced Players* — Matthew Janda](https://www.twoplustwo.com/books/poker/no-limit-holdem-for-advanced-players/) — Extends EV thinking to range vs. range analysis.
- [Wikipedia — Expected Value](https://en.wikipedia.org/wiki/Expected_value) — Formal mathematical treatment of expectation with examples across domains.
- [Wikipedia — Kelly Criterion](https://en.wikipedia.org/wiki/Kelly_criterion) — When variance matters: the Kelly Criterion shows how to size bets to maximise long-run growth rate, not just EV, under bankroll constraints.
- [GTO Wizard Blog](https://gtowizard.com/blog/) — Modern GTO solver outputs interpreted through an EV lens; shows how EV trees translate to real solver strategies.
