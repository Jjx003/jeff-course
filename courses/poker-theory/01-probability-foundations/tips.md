# Probability Foundations — Hints & Going Deeper

## Incremental Hints

### Hint 1 — Struggling with $\binom{n}{k}$?
Start by just multiplying: $52 \times 51 = 2{,}652$. Then divide by 2 because order doesn't matter (AK is the same as KA). Result: 1,326. The division by $k!$ is always "correcting for overcounting orderings."

### Hint 2 — Why do pairs have 6 combos, not 12?
When you pick 2 cards from 4 suits for a pair, A♠A♥ is the same hand as A♥A♠. That's why we use $\binom{4}{2} = 6$ (unordered), not $4 \times 3 = 12$ (ordered). For offsuit hands like AKo the two ranks are *different*, so A♠K♥ ≠ K♥A♠ is not an issue — we just count all 4×3 suit combinations.

### Hint 3 — Confused about which rule to use?
Ask yourself: "How many more community cards will be dealt?" Two cards still to come (flop decision) → Rule of 4. One card still to come (turn decision) → Rule of 2.

### Hint 4 — Are all outs equally good?
Not always. An out that completes your flush might also complete a better flush for your opponent, or put a paired board that kills your straight. These are called **tainted outs** or **dirty outs**. When in doubt, discount your out count by 1–2 for safety.

### Hint 5 — How do blockers help in-game?
When you're considering a bluff, holding a card that blocks your opponent's strongest hands makes your bluff more likely to succeed. Example: bluffing the nut-flush blocker (A of the flush suit) means the opponent is less likely to have a flush to call with.

---

## Going Deeper

- [Wikipedia — Combinations](https://en.wikipedia.org/wiki/Combination) — The mathematical foundation for $\binom{n}{k}$, with proof and worked examples.
- [Wikipedia — Hypergeometric Distribution](https://en.wikipedia.org/wiki/Hypergeometric_distribution) — Exact distribution for drawing without replacement; underlies all precise equity calculations.
- [PokerStove / Equilab](https://www.pokerstrategy.com/poker-software/equilab-holdem/) — Free equity calculator; use it to verify your Rule of 2/4 approximations against exact numbers.
- [*The Mathematics of Poker* — Chen & Ankenman](https://www.conjelco.com/mop.html) — The definitive academic treatment; Chapter 2 covers combinatorics and hand frequencies rigorously.
- [*Poker's 1%* — Ed Miller](https://www.notedpokerauthority.com/) — Practical combo-counting drills at the table level, written for players rather than mathematicians.
- [Two Plus Two Forums — Probability FAQ](https://forumserver.twoplustwo.com/15/probability/) — Community-maintained reference for common probability questions with peer-reviewed answers.
