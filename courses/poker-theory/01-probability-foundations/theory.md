# Probability Foundations — Theory & Derivations

## Exact Flush-Draw Equity

The Rule of 4 gives a fast approximation. Here is the exact calculation for a flush draw (9 outs) on the flop with two cards to come.

After the flop you have seen 5 cards (2 hole + 3 board). There are 47 unseen cards, of which 9 are outs.

The probability of **missing** both the turn and river:

$$P(\text{miss both}) = \frac{38}{47} \times \frac{37}{46} = \frac{1{,}406}{2{,}162} \approx 65.03\%$$

So equity $\approx 1 - 0.6503 = 34.97\%$. The Rule of 4 gives $9 \times 4 = 36\%$ — an overestimate of about 1 percentage point, which is perfectly acceptable for in-game decisions.

**General formula (two cards to come):**

$$\text{Equity} = 1 - \frac{(47 - \text{outs})}{47} \times \frac{(46 - \text{outs})}{46}$$

**General formula (one card to come):**

$$\text{Equity} = \frac{\text{outs}}{46}$$

## Why the Rule of 4 Works (and Where It Breaks)

Let $x = \text{outs}$. The exact two-card equity is:

$$E = 1 - \frac{(47-x)(46-x)}{47 \times 46}$$

Expanding and simplifying:

$$E = \frac{47x + 46x - x^2}{47 \times 46} = \frac{93x - x^2}{2{,}162}$$

For small $x$ the $x^2$ term is negligible, and $93/2{,}162 \approx 0.043$, which rounds to 4%. The $x^2$ term grows as $x$ increases, causing the rule to overestimate for large out counts. At $x = 20$ outs, the rule gives $80\%$ while the exact answer is $\approx 67.5\%$.

| Outs | Rule of 4 | Exact |
|---|---|---|
| 4 | 16% | 16.5% |
| 8 | 32% | 31.5% |
| 9 | 36% | 35.0% |
| 12 | 48% | 45.0% |
| 15 | 60% | 54.1% |

<p align="center">
  <img src="/images/poker-theory/equity-chart.svg" alt="Rule of 4 vs Exact Equity Chart" />
</p>

For draws with ≤ 12 outs the error is at most 3 percentage points — far smaller than the typical uncertainty in opponent hand-reading.

## Counting Total Starting Hand Combos

A rigorous derivation of 1,326:

$$\binom{52}{2} = \frac{52!}{2! \cdot 50!} = \frac{52 \times 51}{2 \times 1} = 1{,}326$$

Of these:
- **Pocket pairs:** 13 ranks, each with $\binom{4}{2} = 6$ combos → $13 \times 6 = 78$
- **Non-paired suited:** $\binom{13}{2} = 78$ rank pairs, each with 4 suit combos → $78 \times 4 = 312$
- **Non-paired offsuit:** 78 rank pairs, each with 12 suit combos → $78 \times 12 = 936$
- **Total:** $78 + 312 + 936 = 1{,}326$ ✓

## Conditional Combo Counts (Blocker Math)

Suppose you hold one Ace. The remaining 51 cards include 3 Aces. How many pocket-Ace combos remain for opponents?

$$\binom{3}{2} = 3$$

More generally, if you hold one card of rank $R$, the remaining combos of $RR$ (pocket pair) drop from 6 to:

$$\binom{3}{2} = 3$$

If you hold **two** cards of rank $R$ (impossible for a pair, but imagine two-card blockers in Omaha), remaining combos would drop to $\binom{2}{2} = 1$.

For a non-paired hand $AB$ where you hold one $A$: the opponent can have $\binom{3}{1} \times \binom{4}{1} = 12$ combos of $AB$ remaining (3 remaining $A$s × 4 $B$s). Down from 16.

## The Hypergeometric Distribution

Out-counting is really sampling without replacement. The exact probability of hitting exactly $k$ of your $x$ outs across $n$ community cards drawn from $N$ remaining cards follows a **hypergeometric** distribution:

$$P(X = k) = \frac{\binom{x}{k}\binom{N-x}{n-k}}{\binom{N}{n}}$$

For a flush draw with $x=9$, $N=47$, $n=2$ (turn + river combined), the probability of hitting at least 1 out is:

$$1 - P(X=0) = 1 - \frac{\binom{9}{0}\binom{38}{2}}{\binom{47}{2}} = 1 - \frac{703}{1{,}081} \approx 34.97\%$$

This is the exact number we computed earlier by the sequential approach — both methods agree.
methods agree.
