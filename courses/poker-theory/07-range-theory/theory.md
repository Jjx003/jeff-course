# Theory Reference: Range Construction and Combinatorics

<p align="center">
  <img src="/images/poker-theory/hand-matrix.svg" alt="Starting Hand Matrix" />
</p>

## Total Combos from a 52-Card Deck

The number of two-card starting hands in a 52-card deck:

$$\binom{52}{2} = \frac{52!}{2! \cdot 50!} = 1326$$

Of these 1326, there are 169 distinct **hand types** (ignoring suits for categorisation purposes):

- 13 pocket pairs (one per rank)
- 78 suited hand types ($\binom{13}{2} = 78$)
- 78 offsuit hand types ($\binom{13}{2} = 78$)

## Combo Counts by Hand Type

| Hand type | Formula | Count |
|---|---|---|
| Pocket pair (e.g. KK) | $\binom{4}{2}$ | **6** |
| Suited hand (e.g. AKs) | $\binom{4}{1} = 4$ (one per suit pair) | **4** |
| Offsuit hand (e.g. AKo) | $4 \times 3 = 12$ (choose suit for each card, no same suit) | **12** |

Total check: $13 \times 6 + 78 \times 4 + 78 \times 12 = 78 + 312 + 936 = 1326$ ✓

## Range Size Calculation

If a player opens $p\%$ of hands, the approximate combo count is:

$$\text{combos in range} \approx \left\lfloor 1326 \times \frac{p}{100} \right\rfloor$$

For common opening frequencies:

| Position | Open% | Approx combos |
|---|---|---|
| UTG | 12% | 159 |
| MP | 18% | 239 |
| CO | 27% | 358 |
| BTN | 40% | 530 |

## Blocker Math

### Reducing pocket pair combos

Before seeing your hand, rank X has $\binom{4}{2} = 6$ combos in villain's range.

- If you hold **one** X: $\binom{3}{2} = 3$ combos remain
- If you hold **two** X (impossible for a different pair): N/A
- If the board shows **one** X: $\binom{3}{2} = 3$ combos remain
- If the board shows **two** X: $\binom{2}{2} = 1$ combo remains

### Reducing suited hand combos

AKs has 4 combos. If you hold A♠ (or K♠), the A♠K♠ combo is removed → **3 suited AK combos** remain.

### Reducing offsuit hand combos

AKo has 12 combos. If you hold A♠:
- All combos with A♠ are removed: A♠K♥, A♠K♦, A♠K♣ → **3 combos removed**
- Remaining offsuit AK combos: $12 - 3 = 9$

If you hold A♠ and K♦:
- A♠ removes 3 combos (as above)
- K♦ removes a further 2 combos from the remaining set (A♥K♦, A♦K♦ — but A♠K♦ was already removed)
- Net: $12 - 3 - 2 = 7$ offsuit AK combos remain

In general, when you hold **one card of rank X**, the total AXo combos for any rank Y reduce by 3 (from 12 to 9); total AXs reduce by 1 (from 4 to 3).

## Range Equity Estimation

The equity of a range $R_1$ against a range $R_2$ on board $B$ is:

$$\text{Equity}(R_1) = \frac{\sum_{h \in R_1} w(h) \cdot \text{eq}(h, R_2, B)}{\sum_{h \in R_1} w(h)}$$

Where $w(h)$ is the combo weight (often 1, but reduced for blocked combos) and $\text{eq}(h, R_2, B)$ is the all-in equity of hand $h$ against the full range $R_2$ on board $B$.

In practice, solvers compute this numerically. But conceptually:
- Count the number of combos in each category (made hand, draw, weak)
- Weight by equity (top pair~60%, flush draw~35%, nothing~15%)
- Sum and divide by total combos

## Nut Advantage: A Formal Intuition

Define the **nut-advantage threshold** as the top $N\%$ of hands on a given board by equity. Nut advantage belongs to the player whose range contains a higher *fraction* of those top-$N$ hands.

For a pot-sized bet to be credible (not immediately exploitable by check-raising or calling too wide), the bettor typically needs nut advantage — otherwise villain can call more liberally knowing bettor rarely holds the best hands.

## Polarisation Ratio

A useful informal metric is the **polarisation ratio**: the fraction of a betting range that is either very strong (>70% equity vs. a random hand) or very weak (<30% equity). A polarisation ratio above ~80% indicates a polar range; below ~50% is a merged/linear range.

Polar bettors use large bet sizes (100%+ of pot); linear bettors use smaller sizes (25–50% of pot) to charge draws without folding out too many calling hands. More on bet sizing in Module 13.

## The Value of Position for Ranges

Being **in position** (acting last) has a direct effect on range realisation:

$$\text{Realised equity} = \text{Raw equity} \times \text{IP multiplier}$$

The IP multiplier exceeds 1 for speculative hands (they realise more than their raw equity) and is below 1 for out-of-position hands (they leak equity through suboptimal bluffing and calling frequencies). This is why the BTN can profitably call with hands that the UTG would fold — the positional edge makes speculative hands more valuable.
