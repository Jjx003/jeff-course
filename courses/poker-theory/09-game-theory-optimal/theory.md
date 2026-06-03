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

Let $b$ = fraction of hero's betting range that are bluffs.

### Villain's EV of calling

If villain calls:
- With probability $b$, hero is bluffing → villain wins the pot **plus** hero's bet: net gain $= +(P+B)$. (The pot $P$ and hero's bet $B$ both go to villain; villain's own call returns to them.)
- With probability $(1-b)$, hero has value → villain loses their call: net gain $= -B$

$$\text{EV}(\text{call}) = b \cdot (P+B) - (1-b) \cdot B = b(P+2B) - B$$

### Villain's EV of folding

$$\text{EV}(\text{fold}) = 0$$

### Indifference condition

$$b(P+2B) - B = 0$$

$$b = \frac{B}{P+2B}$$

This is the **GTO bluff fraction**: the share of betting combos that should be bluffs. It equals the pot odds villain is being laid — exactly the price that makes their bluff-catcher break even. Note it is **distinct** from $\alpha = B/(P+B)$, the defender's maximum fold frequency (derived in the MDF section below); conflating the two is a classic mistake.

### Value-to-bluff ratio

$$\frac{\text{value hands}}{\text{bluff hands}} = \frac{1-b}{b} = \frac{(P+B)/(P+2B)}{B/(P+2B)} = \frac{P+B}{B}$$

For a pot-sized bet ($B = P$): value:bluff ratio $= 2P/P = 2:1$. Two value hands per bluff.
For a half-pot bet ($B = P/2$): value:bluff ratio $= 1.5P/0.5P = 3:1$. Three value hands per bluff.

(Equivalently, the number of bluffs per value combo is $b/(1-b) = B/(P+B) = \alpha$ — so "bluffs $=$ value $\times \alpha$". The bluff *ratio* numerically equals $\alpha$, but the bluff *fraction* of the whole betting range, $B/(P+2B)$, does not.)

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

| Bet size (fraction of pot) | Bluff fraction $b = \frac{B}{P+2B}$ | Value:bluff $= \frac{P+B}{B}$ | MDF $= \frac{P}{P+B}$ | $\alpha = \frac{B}{P+B}$ (max fold) |
|---|---|---|---|---|
| 25% of pot ($B = 0.25P$) | $\frac{0.25}{1.5} \approx 17\%$ | 5:1 | 80% | 20% |
| 50% of pot ($B = 0.5P$) | $\frac{0.5}{2} = 25\%$ | 3:1 | 67% | 33% |
| 75% of pot ($B = 0.75P$) | $\frac{0.75}{2.5} = 30\%$ | 2.33:1 | 57% | 43% |
| 100% of pot ($B = P$) | $\frac{1}{3} \approx 33\%$ | 2:1 | 50% | 50% |
| 150% of pot ($B = 1.5P$) | $\frac{1.5}{3.5} \approx 43\%$ | 1.67:1 | 40% | 60% |

**Key insight:** Larger bets require a higher bluff fraction (more bluffs per value bet) and force villain to fold more (lower MDF). Note that the bluff fraction $b = B/(P+2B)$ and the maximum fold frequency $\alpha = B/(P+B)$ are different numbers — only for the defender do the fold and continue frequencies ($\alpha$ and MDF) sum to 1.

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
