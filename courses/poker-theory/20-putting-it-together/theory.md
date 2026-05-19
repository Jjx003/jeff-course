# The Unified Mathematical Framework

## A Single Objective, Multiple Tools

Every formula in this course is a specialised version of one objective function:

$$\max_{a \in \mathcal{A}} \; \mathbb{E}\bigl[V(a,\, R_h,\, R_o,\, B,\, S)\bigr]$$

Choose the action $a$ (fold, call, raise, bet size) that maximises expected value given the joint state: your range $R_h$, the opponent's range $R_o$, the board $B$, and the remaining stack depth $S$. Every tool introduced across the course is an efficient approximation or exact solution to this optimisation in a specific context.

## The Hierarchy of Approximations

| Situation | Approximation Used | Exact Criterion |
|---|---|---|
| Call vs fold decision | Pot odds: $e \geq c/(P+c)$, where $P$ is the pot already including villain's bet | EV(call) $\geq$ EV(fold) = 0 |
| Bet size selection | Geometric sizing: $g = \text{SPR}^{1/N}$, $b/P = (g-1)/2$ | Maximise EV over $N$ streets |
| Bluff calibration | MDF: bluffs $= \alpha \cdot$ value | Defender indifference at equilibrium |
| Range construction | GTO equilibrium (Nash) | No unilateral profitable deviation |
| Tournament decision | ICM: $\Delta$prize equity $> \Delta$chip EV | Maximise prize-equity, not chip EV |

Each row operates at a different scope — single bet, multi-street line, range composition, full strategy, or tournament chip valuation. The unifying thread is EV maximisation under incomplete information.

## GTO as Nash Equilibrium

GTO play is the Nash equilibrium of the extensive-form game of poker. In a two-player zero-sum game, the minimax theorem guarantees:

$$\max_{\sigma_1} \min_{\sigma_2} \mathbb{E}[V(\sigma_1, \sigma_2)] = \min_{\sigma_2} \max_{\sigma_1} \mathbb{E}[V(\sigma_1, \sigma_2)] = V^*$$

where $V^*$ is the game value. At equilibrium $(\sigma_1^*, \sigma_2^*)$, no player can improve their EV by unilaterally deviating. This gives GTO two properties:

1. **Unexploitability**: any deviation by the opponent from $\sigma_2^*$ weakly increases your EV
2. **Not profit-maximising against non-GTO opponents**: $\sigma_1^*$ mixes strategies to prevent exploitation, but against a player who systematically over-folds, a pure value strategy extracts more EV than $\sigma_1^*$

The exploitative adjustment is to modify $\sigma_1$ away from $\sigma_1^*$ in the direction that maximises EV against the specific $\sigma_2$ being played, accepting exploitability as a trade-off for higher EV against that fixed opponent strategy.

## Exploitative EV Gain

Quantify the exploitative gain as follows. Let $\text{EV}(\sigma_1, \sigma_2^*)$ be the GTO baseline, and let $\sigma_2^{\text{exploit}}$ be the opponent's actual (non-GTO) strategy. The exploitative EV gain from playing the optimal response $\sigma_1^{\text{best}}$ instead of $\sigma_1^*$ is:

$$\Delta\text{EV} = \text{EV}(\sigma_1^{\text{best}}, \sigma_2^{\text{exploit}}) - \text{EV}(\sigma_1^*, \sigma_2^{\text{exploit}}) \geq 0$$

The risk: if the opponent detects the exploit and adjusts, $\sigma_2^{\text{exploit}}$ shifts back toward $\sigma_2^*$, reducing $\Delta\text{EV}$ to zero. GTO provides the stable equilibrium to return to when the opponent adapts.

## The Study Loop as Iterative EV Optimisation

The four-part study framework (spot study → concept drilling → session review → leak identification) is an iterative approximation of gradient ascent on the EV landscape:

$$\sigma_{t+1} = \sigma_t + \eta \cdot \nabla_{\sigma} \mathbb{E}[V(\sigma_t,\, \sigma_{\text{opp}})]$$

where $\eta$ is the learning rate (determined by study intensity and quality) and $\sigma_{\text{opp}}$ is the distribution of opponents in your current player pool. Each cycle through the loop adjusts your strategy in the direction that increases EV against the pool you play.

This framing also explains why the loop must be continuous: $\sigma_{\text{opp}}$ evolves as you move up stakes, as the player pool adapts to common strategies, and as new solver solutions become public knowledge. The gradient is never permanently zero in a dynamic player pool.

## Connecting All Major Formulas

All major formulas are derived from the same consistency condition — **no action should be automatically more profitable than another at equilibrium** (the indifference principle):

$$\text{EV}(\text{call}) = 0 \implies e = \frac{C}{P + C} \quad\text{(pot odds — } P \text{ here is the pot already including villain's bet, } C \text{ is your call)}$$

$$\text{EV}(\text{bluff}) = 0 \implies f_{\text{fold}} = \frac{B}{P + B} = \alpha \quad\text{(aggressor indifference; } P \text{ is the pre-bet pot)}$$

$$\text{EV}(\text{fold}) = \text{EV}(\text{call}) \implies \text{MDF} = 1 - \alpha = \frac{P}{P + B} \quad\text{(defender)}$$

$$\frac{\text{bluffs}}{\text{value}} = \alpha \quad\text{(bluff ratio, derived from defender indifference)}$$

These four expressions are transformations of each other. Pot odds tells the defender when to call; MDF tells the defender how often to continue; the bluff ratio tells the aggressor how many bluffs to include. All three are consequences of the same indifference principle applied from different perspectives.

## What Lies Beyond This Course

The framework here covers the essential toolkit for heads-up and two-player thinking. Extensions for more advanced study:

- **Multi-way pot theory**: Nash equilibria for 3+ players are significantly harder to compute; pot odds and MDF formulas require modification because multiple opponents' ranges interact
- **Bayesian range updating**: Updating $R_o$ continuously as actions accumulate, using Bayes' theorem to compute posterior range distributions that tighten with each street
- **Solver fluency**: Moving from reading solver outputs to designing custom solve trees, adjusting bet size trees, and interpreting node-lock exploits
- **Population-adjusted GTO**: Weighting the GTO equilibrium by population tendencies at a given stake level to identify the highest-EV mixed strategy against a realistic opponent distribution

The framework in this course is not an endpoint — it is the foundation on which each of these extensions is built, and to which you return when the extensions become complex.
