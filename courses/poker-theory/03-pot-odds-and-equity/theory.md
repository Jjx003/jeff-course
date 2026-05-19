# Pot Odds and Equity — Theory & Derivations

<p align="center">
  <img src="/images/poker-theory/poker-chips.svg" alt="Poker Chips" />
</p>

## Why Break-Even Equity Equals Pot Odds

Let $C$ be the call amount, $P$ be the pot before our call (including the opponent's bet), and $q$ be our equity. The final pot after calling is $P + C$.

The EV of calling is:

$$\text{EV(call)} = q \cdot (P + C) - C$$

Setting EV = 0 (break-even):

$$q \cdot (P + C) = C$$

$$q = \frac{C}{P + C}$$

This is precisely the pot-odds formula. Break-even equity and pot odds are the same quantity by algebraic necessity — not by convention.

**Corollary:** if equity $> C/(P+C)$, the call is +EV. If equity $< C/(P+C)$, the call is −EV. The crossover is exactly pot odds.

## EV of Calling as a Function of Equity

Rearranging the break-even formula:

$$\text{EV(call)} = q(P + C) - C = (P + C)\!\left(q - \frac{C}{P+C}\right) = (P+C)(q - \text{pot odds})$$

This tells us:
- The EV of a call scales linearly with the gap between equity and pot odds.
- A larger pot amplifies the impact of each percentage point of edge or deficit.
- When pot odds = 25% and equity = 35%, the EV gain per call is $(P+C) \times 0.10$. For a $200 final pot, that's $+\$20.

## Expressing EV in Terms of Win/Loss Amounts

Alternatively, split the equity into win and loss scenarios:

$$\text{EV(call)} = q \cdot W - (1-q) \cdot C$$

where $W$ = what we win net if we hit (the pot $P$ we didn't put in), and $C$ = what we lose if we miss. Rewriting $W = P + C - C = P$:

$$\text{EV(call)} = q \cdot P - (1-q) \cdot C$$

This is a cleaner form for intuition: we win the pot $P$ with probability $q$, and lose our call $C$ with probability $(1-q)$.

Break-even: $qP = (1-q)C$, giving $q/(1-q) = C/P$, i.e. the **odds ratio** form:

$$\text{Pot Odds (ratio form)} = \frac{C}{P}$$

Both the ratio form and the percentage form carry the same information. The percentage form ($C/(P+C)$) is more widely used because it's directly comparable to equity percentages.

## Implied Odds: Formal Treatment

Let $X$ be the additional amount we expect to win on future streets when we hit our draw. Treat this as increasing our effective winning amount. The EV of calling becomes:

$$\text{EV(call with implied odds)} = q(P + C + X) - C$$

The new break-even equity is:

$$q^* = \frac{C}{P + C + X}$$

Implied pot odds percentage = $C / (P + C + X)$. A large $X$ dramatically reduces the equity required to call.

**Example:** $P = 150$ (pot + bet), $C = 50$, $X = 200$ expected future profit.

$$q^* = \frac{50}{150 + 200} = \frac{50}{350} \approx 14.3\%$$

A hand with only 15% equity (≈ a gut-shot draw) now has a +EV call, despite raw pot odds of $50/200 = 25\%$ suggesting a fold. The key assumption is that $X$ is reliably collectable — this is where range-reading skill matters most.

## Reverse Implied Odds

Reverse implied odds apply when hitting your draw might not give you the best hand. Let $Y$ be the expected additional loss when you hit but still lose (e.g. hitting a second-best flush).

$$\text{EV(call)} = q(1-r)(P + C + X) - q \cdot r \cdot (C + Y) - (1-q) \cdot C$$

where $r$ = probability that you hit but are still beaten. This is complex, so in practice we reduce out counts by "discounting" for reverse-implied-odds situations rather than solving the full equation.

## Historical Note

The pot-odds concept was popularized in David Sklansky's *The Theory of Poker* (1987), where he introduced the Fundamental Theorem of Poker. The formal EV derivation shown here is the mathematical backbone of that theorem.
