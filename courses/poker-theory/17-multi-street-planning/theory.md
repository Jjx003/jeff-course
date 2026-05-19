# Multi-Street Planning: The Mathematics of Sequential Decisions

## Geometric Sizing Across Streets

Multi-street planning begins with geometric bet sizing (Module 13). For a starting stack-to-pot ratio SPR and $N$ streets of betting at a uniform per-street pot multiplier $g$, the condition to bring the pot up to the commitment point (pot equals one starting stack) is:

$$g^N = \text{SPR}, \quad \text{so} \quad g = \text{SPR}^{1/N}$$

Each bet of size $b$ grows the pot from $P$ to $P + 2b = g \cdot P$, so the per-street bet fraction is:

$$\frac{b}{P} = \frac{g - 1}{2} = \frac{\text{SPR}^{1/N} - 1}{2}$$

**Example:** SPR = 8, $N = 3$ streets:

$$g = 8^{1/3} = 2.0 \quad\Rightarrow\quad \frac{b}{P} = \frac{2 - 1}{2} = 0.5$$

Each street should bet 50% of the current pot — doubling the pot every street until the pot equals one starting stack, at which point the next pot-sized bet would shove. In practice, bet sizes are rounded (e.g. 50%, 50%, 50% jamming on the last street), but the geometric principle ensures consistency: if the flop bet is too small, the turn or river bet must be unrealistically large to reach the commitment point.

## Barrel Frequency and the MDF Constraint

On each street, the barrel frequency is constrained by the defender's MDF. Let $\alpha_s = b_s/(P_s + b_s)$ be the alpha on street $s$. For the defender to be indifferent between calling and folding:

$$f_{\text{bluff},s} \leq \alpha_s \cdot f_{\text{value},s}$$

where $f_{\text{bluff},s}$ and $f_{\text{value},s}$ are the frequencies at which the aggressor barrels with bluffs and value hands on street $s$.

**Why barrel frequency decreases across streets:** On the turn, the aggressor's range is a subset of their flop betting range (hands that didn't give up). The value hands that barred the flop remain (they improve or retain nut advantage), but the bluff hands that reached the turn must be more selective — over-barreling on the turn violates the bluff ratio constraint and becomes exploitable by over-calling.

**Turn barrel bluff calibration:**

$$\text{turn bluffs} \leq \alpha_T \times \text{turn value hands}$$

If the flop c-bet frequency was high, many bluffs reach the turn. Those bluffs must be trimmed to the $\alpha_T$ ratio, and the rest give up. Identifying which bluffs to continue with (equity, blockers, board narrative) vs. which to abandon (total air) is the practical skill that emerges from this constraint.

## Implied Odds: The Formal Model

A speculative hand's EV when calling on street $s$ is:

$$\text{EV}_{call,s} = e_{direct} \cdot (P + 2c) - c + P(\text{hit future}) \cdot I$$

where:
- $e_{direct}$ = probability of winning the pot at current stage with no further betting
- $c$ = cost to call
- $P(\text{hit future})$ = probability of completing the speculative hand on a future street
- $I$ = net additional chips won when hitting (implied odds)

The call is profitable when:

$$e_{direct} \cdot P + P(\text{hit}) \cdot I > c(1 - e_{direct})$$

Rearranging for the implied odds threshold:

$$I > \frac{c(1 - e_{direct}) - e_{direct} \cdot P}{P(\text{hit})}$$

**Example — turn flush draw:** $c = 60$, $P = 120$, $e_{direct} = 0.19$, $P(\text{hit}) = 0.19$:

$$I > \frac{60 \times 0.81 - 0.19 \times 120}{0.19} = \frac{48.6 - 22.8}{0.19} = \frac{25.8}{0.19} \approx 136$$

You need to win approximately 136 additional chips when hitting to make the turn call profitable on direct odds alone. Against a 200BB effective stack with many chips behind, this is comfortably achievable; in a short-stack situation, it may not be.

## River Polarisation: The Final Bluff Ratio

On the river, no future streets exist to compensate for errors. The optimal bluff-to-value ratio is exactly:

$$\frac{\text{river bluffs}}{\text{river value}} = \alpha_R = \frac{b_R}{P_R + b_R}$$

This is the same MDF-derived ratio, but now it must hold *precisely* — there is no next-street adjustment. If the aggressor over-bluffs (too many bluffs relative to value at size $b_R$), the caller profits by always calling. If the aggressor under-bluffs, the caller profits by always folding.

**Blocker effects at the river:** The best river bluff candidates are hands that reduce the probability of the opponent holding strong calling hands. If the opponent calls the river with nut flushes and the aggressor holds $A\spadesuit x$ (blocking the nut flush), the effective calling frequency is lower than expected — making the bluff more profitable than the raw MDF calculation suggests.

Formally, if the blocker removes $k$ combos from the opponent's calling range of size $N$, the effective fold frequency becomes:

$$f_{fold}^* = f_{fold} + \frac{k}{N} \cdot (1 - f_{fold})$$

A meaningful blocker effect can shift the bluff EV from marginally negative to positive.

## The Value of Hand Plans: EV Tree Calculation

When a hand is played with an explicit plan, each street's EV is maximised given the continuation plan for future streets. The full EV of a flop action is:

$$\text{EV}_{flop} = \sum_{t \in \text{turns}} P(t) \left[ f_{fold,t} \cdot P_t + f_{call,t} \cdot \sum_{r \in \text{rivers}} P(r|t) \cdot \text{EV}_{river}(r) \right]$$

Without a plan, $\text{EV}_{river}(r)$ is computed suboptimally — wrong sizing, wrong action — reducing the total. With a plan, each future EV term is maximised, and the full tree EV is the highest possible from the flop decision.

## Summary

| Concept | Formula | Key Insight |
|---|---|---|
| Geometric sizing | $b/P = (\text{SPR}^{1/N} - 1)/2$ | Consistent per-street fraction to grow pot to one stack |
| Turn bluff limit | bluffs $\leq \alpha_T \times$ value | MDF applies at every street |
| Implied odds threshold | $I > [c(1-e) - eP] / P(\text{hit})$ | Win enough on later streets to justify call |
| River bluff ratio | bluffs/value $= \alpha_R$ | Exact equilibrium; no future-street correction |
| Blocker EV boost | $f_{fold}^* = f_{fold} + k/N \cdot (1 - f_{fold})$ | Holding blockers increases effective fold frequency |
