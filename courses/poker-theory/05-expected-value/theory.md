# Expected Value — Theory & Derivations

## EV as a Linear Functional

Expected value is a linear operator over probability distributions. If $X$ is a random variable representing the outcome of a decision and $P$ is the probability measure over outcomes:

$$\mathbb{E}[X] = \int x \, dP(x) = \sum_{i} P_i V_i \quad (\text{discrete case})$$

Linearity means $\mathbb{E}[aX + bY] = a\mathbb{E}[X] + b\mathbb{E}[Y]$ for constants $a, b$ — a property we use constantly when computing the EV of multi-street decisions.

## Deriving Break-Even Fold Frequency for a Bluff

The bluff EV is:

$$\text{EV(bluff)} = f \cdot P - (1-f) \cdot B$$

Setting to zero:

$$fP = (1-f)B = B - fB$$

$$f(P + B) = B$$

$$f^* = \frac{B}{P + B}$$

This is symmetric to the pot-odds formula for calling: both are ratios of the "investment" to the "total stake". In a bluff, you invest $B$ to win $P$; in a call, you invest $C$ to win $P$.

**Key insight:** the break-even fold frequency depends only on the bet/pot ratio, not on your specific holding. This means any two hands with the same bet size have the same break-even fold frequency — a fundamental result that motivates range-balanced betting strategies (Module 07).

## EV of a Mixed Strategy

In game theory, players often randomise their actions. If you bluff with probability $\alpha$ and value bet with probability $1-\alpha$:

$$\text{EV(mixed)} = \alpha \cdot \text{EV(bluff)} + (1-\alpha) \cdot \text{EV(value bet)}$$

When the opponent plays optimally (correctly exploiting your mix), both actions have equal EV — this is the Nash Equilibrium condition. The equilibrium bluffing frequency that makes the opponent indifferent to calling or folding can be derived from the opponent's EV equations:

$$\text{EV(villain call)} = \alpha \cdot (-B) + (1-\alpha) \cdot (-B) = \text{EV(villain fold)} = 0$$

Solving: villain is indifferent when you bluff at the frequency that sets villain's call EV = 0. This gives the GTO bluffing frequency — covered in depth in Module 09 (Game Theory Optimal).

## Multi-Street EV: Backward Induction

When decisions span multiple streets, we compute EV by **backward induction** — solving the final street first, then working backwards.

**Example:** You have a nut draw with two streets left. On the river, if you hit, you can bet $R$ for value; if you miss, you check. Let $p$ = probability of hitting the draw.

- EV(hit) = $\text{EV(river value bet)} = c_R \cdot R$ (simplified)
- EV(miss) = 0 (check-fold)

Turn EV of calling $C_T$:

$$\text{EV(turn call)} = p \cdot (P_T + C_T + c_R \cdot R) - (1-p) \cdot C_T$$

The $c_R \cdot R$ term is the implied odds from the river street. This is a formal derivation of why implied odds increase the EV of calling on the turn.

## Variance and Risk

EV captures the long-run average but says nothing about variance — the spread of outcomes. Two decisions can have the same EV but very different variance:

- **Low variance:** call a small bet with 60% equity. EV ≈ +\$small per call; variance is low.
- **High variance:** call an all-in with 60% equity for a $10,000 pot. EV = +\$2,000 (same edge ratio); variance is enormous.

For a bankrolled professional, maximising EV ignoring variance is correct — variance cancels over large sample sizes. For a recreational player with a limited bankroll, some variance aversion is rational (Kelly Criterion territory). This course focuses on EV maximisation as the mathematically correct baseline.

## The Fundamental Theorem of Poker (Sklansky)

> Every time you play a hand differently from the way you would have played it if you could see all your opponents' cards, they gain; and every time you play your hand the same way you would have played it if you could see all their cards, they lose.

Formally, let $\sigma^*$ be the strategy you'd play with perfect information (all cards visible). The EV difference between your actual strategy $\sigma$ and $\sigma^*$ is:

$$\Delta\text{EV} = \text{EV}(\sigma^*) - \text{EV}(\sigma) \geq 0$$

The theorem says $\Delta\text{EV} \geq 0$ always — perfect information never hurts. Every imperfect decision (calling too much, not bluffing enough, value-betting too thin) corresponds to a positive $\Delta\text{EV}$ we are leaving on the table for our opponents. EV maximisation is the formal project of minimising $\Delta\text{EV}$.
