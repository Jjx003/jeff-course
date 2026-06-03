# ICM & Tournament Theory — Derivations & Deeper Analysis

## Why Two-Player ICM Is Linear

Consider a two-player tournament with payouts $P_1 > P_2$. Player A holds $S$ chips out of $T$ total. Under Malmuth-Harville:

$$P_A(\text{1st}) = \frac{S}{T}, \qquad P_A(\text{2nd}) = 1 - \frac{S}{T} = \frac{T - S}{T}$$

So:

$$\text{ICM}(A) = \frac{S}{T} \cdot P_1 + \frac{T-S}{T} \cdot P_2 = P_2 + \frac{S}{T}(P_1 - P_2)$$

This is **linear in $S$**. In heads-up play, every chip is worth exactly $(P_1 - P_2)/T$ dollars. Doubling your stack doubles your additional equity above the guaranteed floor $P_2$. This is why ICM pressure is zero in heads-up: chip EV and dollar EV are perfectly aligned.

## Why Three-Plus Players Introduce Non-Linearity

With three players (A, B, C with chips $a$, $b$, $c$, total $T$), the second-place probability for A is:

$$P_A(\text{2nd}) = P_B(\text{1st}) \cdot \frac{a}{T - b} + P_C(\text{1st}) \cdot \frac{a}{T - c}$$

$$= \frac{b}{T} \cdot \frac{a}{T - b} + \frac{c}{T} \cdot \frac{a}{T - c}$$

$$= a \left( \frac{b}{T(T-b)} + \frac{c}{T(T-c)} \right)$$

This is linear in $a$ but the coefficient depends on $b$ and $c$ in a non-linear way. The ICM equity of A is therefore:

$$\text{ICM}(A) = \frac{a}{T} \cdot P_1 + a \left(\frac{b}{T(T-b)} + \frac{c}{T(T-c)}\right) P_2 + P_A(\text{3rd}) \cdot P_3$$

The curvature comes from the second-place term. Because $\frac{b}{T-b}$ is convex and increasing in $b$, a large stack B increases A's second-place probability less per chip than a small stack C would. **Large stacks are "harder to run through" for second-place finishes.** This is the mathematical source of the short-stack premium: their small $c_j$ in the denominator of the Malmuth-Harville fraction makes it relatively easy for other players to pass through them for second place.

## The ICM Chip Value Derivative

Define the marginal dollar value of an additional chip for player A as:

$$\frac{d[\text{ICM}(A)]}{da}$$

For two players this is constant: $(P_1 - P_2)/T$. For three or more players, it is a decreasing function of $a$ — each additional chip gained is worth fewer dollars than the previous one. This is the formal statement of **diminishing marginal chip value**.

The practical implication: if player A wins $k$ chips from player B, A's ICM equity increases by less than $k \cdot (P_1 - P_2)/T$, while B's ICM equity decreases by more. Chips transfer dollar value from the loser to the short stack (or to the prize structure generally), not dollar-for-dollar to the winner.

## ICM EV of an All-In

Suppose A and B are considering an all-in confrontation with A having equity $q$. Let:

- $\text{ICM}_A^+$ = A's ICM equity if A wins (stack $a + b$)
- $\text{ICM}_A^-$ = A's ICM equity if A loses (= 3rd-place prize in a 3-player scenario, or lower-place prize generally)
- $\text{ICM}_A^0$ = A's current ICM equity

Then:

$$\$\text{EV}(A\text{ calls}) = q \cdot \text{ICM}_A^+ + (1-q) \cdot \text{ICM}_A^- - \text{ICM}_A^0$$

Setting this to zero gives the **ICM break-even equity**:

$$q^* = \frac{\text{ICM}_A^0 - \text{ICM}_A^-}{\text{ICM}_A^+ - \text{ICM}_A^-}$$

Compare this to the chip-EV break-even (simple pot odds):

$$q_{\text{chip}}^* = \frac{C}{P + C}$$

Because $\text{ICM}_A^+$ is below the chip-proportional prize and $\text{ICM}_A^-$ is at or above the minimum payout, the ICM break-even equity $q^*$ is always **higher** than the chip-EV break-even $q^*_{\text{chip}}$. The ICM penalty quantifies exactly how much more equity a player needs to justify a call.

## The Malmuth-Harville Approximation: Strengths and Weaknesses

**Strengths:**
- Tractable: finish probabilities can be computed in $O(n \cdot n!)$ time (or approximated in $O(n^2)$).
- Chip-count-based: no assumptions about skill differences needed.
- Industry standard: all major ICM tools (ICMIZER, HoldemResources, GTO Wizard) use Malmuth-Harville as the baseline.

**Weaknesses:**
- **Path independence assumption:** Malmuth-Harville ignores the order of eliminations and the specific confrontations that lead to each stack evolving. Real tournament dynamics are path-dependent.
- **Skill-neutrality:** assumes all players have equal skill. If the big stack is a fish, their actual finish-position probabilities differ from chip-proportional.
- **Stack geometry:** ignores that players with very short stacks are likely to bust quickly, which affects second-place probabilities for all other players in ways the recursion does not fully capture.

Alternative models (e.g. the Weitzman "chip-chop" formula, or simulation-based ICM) can be more accurate but are harder to compute in real time.

## Push-Fold Game Theory: The Two-Player Nash Equilibrium

In a simplified two-player push-fold game (one player shoves or folds, the other calls or folds), the Nash equilibrium conditions are:

**Shover's indifference condition:** shove if and only if the EV of shoving ≥ EV of folding:

$$\text{EV(shove)} = (1 - c) \cdot P + c \cdot [q(P + S) - (1-q)S] \geq 0$$

where $c$ = caller's call frequency, $P$ = antes/blinds already in the pot, $S$ = shove size, $q$ = shover's equity when called.

Rearranging for the minimum equity to shove when called:

$$q > \frac{c \cdot S - (1-c) \cdot P}{c \cdot (P + S)}$$

For short stacks (small $S$ relative to $P$), this minimum equity is low — you can shove profitably with weak hands because the pot-to-stack ratio is high.

**Caller's indifference condition:** call if and only if:

$$q_{\text{caller}} > \frac{C}{P_{\text{total}}}$$

where $C$ is the call amount and $P_{\text{total}}$ is the total pot after calling.

In the Nash equilibrium, the shover pushes a range just wide enough that the caller is indifferent between calling and folding with marginal hands, and the caller calls just wide enough that the shover is indifferent between shoving and folding marginal hands. NASH charts tabulate these equilibrium ranges by stack depth and position.

## ICM vs. Chip EV: A Numerical Comparison

Using the worked example from the problem (P1 = P2 = 4,000 chips, P3 = 2,000 chips, payouts 500/300/200):

Win → P1 has 8,000 chips (ICM = $460); lose → P1 busts 3rd ($200); pass → P1 = $356.6. Dollar EV of taking the flip with win probability $q$ is $460q + 200(1-q) = 200 + 260q$.

| Scenario | P1 chip EV | P1 dollar EV | ICM penalty |
|---|---|---|---|
| Pass (no confrontation) | 4,000 chips | $356.6 | — |
| 50/50 flip vs P2 | 4,000 chips (unchanged) | $330.0 | −$26.6 |
| 55/45 edge vs P2 | +400 chips EV | $343.0 | −$13.6 |
| 60/40 edge vs P2 | +800 chips EV | $356.0 | −$0.6 |

To break even in dollar EV on a flip against P2, P1 needs $200 + 260q = 356.6$, i.e. $q \approx$ **60% equity**, not 50%. This roughly 10-percentage-point ICM penalty is purely structural — it has nothing to do with reads, skill, or hand strength.

## Variance Considerations in Tournament Play

ICM-based dollar EV is the correct *expected* value metric, but tournaments involve significant variance:

- A player making correct ICM folds every time will show lower chip accumulation but better long-run ROI (return on investment over many tournaments).
- Players who ignore ICM and always take +cEV spots will have higher variance and lower tournament ROI despite short-term chip gains.
- The Kelly Criterion applied to tournaments suggests a risk-tolerance adjustment that aligns with ICM: the non-linearity of prizes mechanically enforces a form of Kelly sizing on your chip decisions.

The practical implication: ICM discipline is most important for players who play many tournaments and care about long-run profitability. For recreational players playing one tournament for fun, the variance reduction from ICM folding matters less.
