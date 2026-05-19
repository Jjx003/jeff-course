# Theory Reference: Game Theory Optimal Foundations

## Nash's Existence Theorem

**Theorem (Nash, 1950):** Every finite game with $n$ players has at least one Nash equilibrium in mixed strategies.

In a two-player zero-sum game, the Nash equilibrium is also the **minimax solution**: the strategy that minimises the maximum loss you can suffer (equivalently, maximises your worst-case EV).

$$\max_{s_1} \min_{s_2} \text{EV}(s_1, s_2) = \min_{s_2} \max_{s_1} \text{EV}(s_1, s_2)$$

This minimax equality is the **minimax theorem** (von Neumann, 1928). It tells us that in a two-player zero-sum game, the value of the game is unique — both players playing GTO achieves the same EV no matter which player we solve from.

## The Indifference Principle: Full Derivation

### Setup

River spot with:
- Pot before bet: $P$
- Hero bets $B$ with a range mixing value hands and bluffs
- Villain's choices: call $B$ or fold

Let $\alpha$ = fraction of hero's betting range that are bluffs.

### Villain's EV of calling

If villain calls:
- With probability $\alpha$, hero is bluffing → villain wins the pot $P$ (hero folds after losing the bet, or villain wins at showdown): net gain = $+P$
- With probability $(1-\alpha)$, hero has value → villain loses their call: net gain = $-B$

$$\text{EV}(\text{call}) = \alpha \cdot P + (1-\alpha) \cdot (-B) = \alpha P - B + \alpha B = \alpha(P+B) - B$$

### Villain's EV of folding

$$\text{EV}(\text{fold}) = 0$$

### Indifference condition

$$\alpha(P+B) - B = 0$$

$$\alpha = \frac{B}{P+B}$$

This is the GTO bluff frequency: the fraction of betting combos that should be bluffs.

### Value-to-bluff ratio

$$\frac{\text{value hands}}{\text{bluff hands}} = \frac{1-\alpha}{\alpha} = \frac{P+B-B}{B} = \frac{P}{B}$$

For a pot-sized bet ($B = P$): value:bluff ratio = $P/P = 1:1$. Equal parts value and bluff.
For a half-pot bet ($B = P/2$): ratio = $P/(P/2) = 2:1$. Two value hands per bluff.

## MDF: The Symmetric Derivation

Hero's bluff EV:

$$\text{EV}(\text{bluff}) = p_{\text{fold}} \cdot P - p_{\text{call}} \cdot B$$

Setting $\text{EV}(\text{bluff}) = 0$:

$$p_{\text{fold}} \cdot P = p_{\text{call}} \cdot B$$

$$(1 - p_{\text{call}}) \cdot P = p_{\text{call}} \cdot B$$

$$P = p_{\text{call}}(P + B)$$

$$\boxed{\text{MDF} = p_{\text{call}} = \frac{P}{P+B}}$$

Sanity check: $\alpha + \text{MDF} = \frac{B}{P+B} + \frac{P}{P+B} = 1$ ✓

## GTO Value for Different Bet Sizes

| Bet size (as fraction of pot) | Bluff % of betting range | MDF (villain's call %) |
|---|---|---|
| 25% of pot ($B = 0.25P$) | $\frac{0.25}{1.25} = 20\%$ | 80% |
| 50% of pot ($B = 0.5P$) | $\frac{0.5}{1.5} = 33\%$ | 67% |
| 75% of pot ($B = 0.75P$) | $\frac{0.75}{1.75} \approx 43\%$ | 57% |
| 100% of pot ($B = P$) | $\frac{P}{2P} = 50\%$ | 50% |
| 150% of pot ($B = 1.5P$) | $\frac{1.5}{2.5} = 60\%$ | 40% |

**Key insight:** Larger bets require a higher bluff frequency (more bluffs per value bet) and force villain to fold more. Smaller bets require a lower bluff frequency but villain can call more liberally.

## Rock-Paper-Scissors: Formal Analysis

Payoff matrix for player A (row player):

$$M = \begin{pmatrix} 0 & -1 & 1 \\ 1 & 0 & -1 \\ -1 & 1 & 0 \end{pmatrix}$$

Where rows/columns are (Rock, Paper, Scissors). Player A chooses a mixed strategy $\mathbf{p} = (p_R, p_P, p_S)$ to maximise their expected payoff against any $\mathbf{q}$ of player B.

The minimax solution requires $\mathbf{p}^* = \mathbf{q}^* = (1/3, 1/3, 1/3)$.

At this equilibrium, the game value is 0 for both players — neither can do better than break even against the Nash strategy.

## GTO in Extensive-Form Games

Poker is an **extensive-form game** (sequential decisions, private information). The GTO solution is computed as a **Nash Equilibrium in the extensive form**, which requires solving across the entire game tree simultaneously.

Modern solvers (PioSolver, GTO+, Solver Hub) compute this using iterative algorithms (Counterfactual Regret Minimisation, or CFR). CFR works by repeatedly playing the game against itself and nudging each decision toward the action that was most regretted being different from, until the strategy profile converges to Nash.

The key outputs:
- **Bet frequencies** at each node: what fraction of combos should bet vs. check
- **Calling frequencies**: what fraction of combos should call vs. fold vs. raise
- **Bluff ratios**: for any bet size, the value:bluff split in the betting range
- **EV per combo**: the expected value of each hand in each player's range

You don't need to run a solver to apply these ideas. The formulas above give you the analytical answers for simplified river spots with a fixed bet size. Real poker is more complex (multiple bet sizes, draws, future streets), but the same equilibrium logic applies.
