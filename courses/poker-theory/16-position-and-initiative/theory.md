# Position and Initiative: The Mathematics of Last Action

## Equity Realization: A Formal Model

Define a hand's raw equity as $e$ (its probability of winning at showdown if no further bets occur). The actual EV of playing the hand is:

$$\text{EV}(\text{hand}) = e \cdot \text{ER} \cdot P$$

where $P$ is the pot size and $\text{ER} \in [0, \infty)$ is the **equity realization coefficient**. ER captures the structural advantage (or disadvantage) of position and initiative.

**Why ER > 1 is possible for IP players:** When IP, a hand can build larger pots when it is ahead (by betting or calling bets) and smaller pots when it is behind (by checking back). This selective pot-size control means the IP player's EV is higher than raw equity alone would predict — they "over-realize" their equity.

**Why ER < 1 for OOP drawing hands:** When OOP with a draw, the IP player decides whether to give a free card. If they bet, the OOP player must pay equity price on top of the call cost. Over many instances, OOP drawing hands realize less equity than their raw percentage suggests.

## Free Card Quantification

Suppose you hold a flush draw with equity $e_d$ (approximately 0.35 with two cards left, 0.19 with one). When IP, you may take a free river card if the turn is checked through:

$$\Delta\text{EV}_{free card} = P(\text{opponent checks turn}) \times e_d \times \overline{P}_{river}$$

where $\overline{P}_{river}$ is the expected pot on the river. When OOP, you cannot unilaterally take this free card — the IP player chooses. The expected cost of losing the free card option is:

$$\Delta\text{EV}_{lost} = P(\text{IP bets turn}) \times \text{EV}_{fold\_draw}$$

Across all drawing hands in a session, this expected cost compounds. Position advantage on speculative hands is not a feel — it is a measurable EV difference.

## The Check-Raise: Polarisation Ratio Derivation

For the OOP check-raise to be unexploitable, the IP player must be indifferent between calling and folding when facing the raise. After a check-raise to total size $R$ into a pot of $P' = P + b$ (where $b$ is the IP player's bet), the IP player's MDF is:

$$\text{MDF}_{raise} = 1 - \frac{R - b}{P' + R} = \frac{P' + b}{P' + R}$$

For the check-raise to be balanced, the fraction of bluffs in the check-raising range satisfies:

$$\frac{\text{bluffs}}{\text{bluffs} + \text{value}} = \alpha_R = \frac{R - b}{P' + R}$$

**Example:** Pot is 100, IP bets 50. OOP check-raises to 200 (total). Then $P' = 150$, $R = 200$, $b = 50$:

$$\alpha_R = \frac{200 - 50}{150 + 200} = \frac{150}{350} \approx 0.43$$

The check-raising range should contain approximately 43% bluffs and 57% value to make the IP player indifferent. This is the composition: for every set or straight check-raised, there should be approximately 0.75 draw bluffs. The exact ratio depends on the specific check-raise sizing.

## Initiative and the C-bet Frequency Formula

Define the optimal c-bet frequency $f^*$ such that the caller is indifferent between always folding and always calling. For the caller to be indifferent, the c-bet must be exactly profitable at the margin — i.e. the aggressor's bluffs must be calibrated to win exactly enough to cover the losses when called by strong hands.

The aggressor's bluffing frequency among c-bets must satisfy:

$$\frac{\text{bluff combos}}{total\ bet\ combos} \leq \alpha = \frac{b}{P + b}$$

The total c-bet frequency $f^*$ at which this is satisfied while including all value bets is:

$$f^* = \text{value combos} \times \frac{1}{\alpha} + \text{bluff combos} = \text{value combos} + \frac{\text{bluff combos}}{\alpha} \cdot \alpha$$

More practically: the total number of c-bet combos is bounded by $\text{value} / \alpha$. Any additional combos beyond this are either too many bluffs (over-bluffing) or too many thin values (bluffcatcher-inducing). Initiative — the aggressor having more value combos — shifts the bound higher, allowing higher total c-bet frequency.

## Position and Pre-flop Calling Width

Because IP players realize more equity, pre-flop calling ranges from the button can be wider than from the big blind:

$$\text{EV}(\text{call from BTN}) = e \cdot \text{ER}_{IP} \cdot P - c$$
$$\text{EV}(\text{call from BB}) = e \cdot \text{ER}_{OOP} \cdot P - c$$

Since $\text{ER}_{IP} > \text{ER}_{OOP}$, the BTN can call with the same hand where the BB should fold. The EV breakeven equity thresholds are:

$$e^*_{BTN} = \frac{c}{\text{ER}_{IP} \cdot P}, \quad e^*_{BB} = \frac{c}{\text{ER}_{OOP} \cdot P}$$

Because $\text{ER}_{IP} > \text{ER}_{OOP}$, we have $e^*_{BTN} < e^*_{BB}$ — the button can call with lower raw equity and still be profitable.

## Donk Bet: The Asymmetric Information Problem

When the OOP player donk bets, they reveal information before the IP player has acted. The IP player gains a significant advantage: they now see the bet size and can narrow the OOP player's range before committing chips.

The EV of a donk bet vs. a check-raise depends on which generates more fold equity and pot building:

- **Donk bet EV** = $f_{\text{fold}} \cdot P + f_{\text{call}} \cdot \text{EV}_{call\text{-off}} + f_{\text{raise}} \cdot \text{EV}_{vs\text{-raise}}$
- **Check-raise EV** = $f_{bet} \cdot [f_{\text{fold}} \cdot (P + b) + f_{\text{call}} \cdot \text{EV}_{call\text{-off}}]$

Check-raises are generally higher EV for strong hands because they (a) guarantee a larger pot before applying pressure, (b) benefit from the IP player's initial bet contribution, and (c) apply more pressure per chip risked. Donk bets make more sense when the OOP player has reason to believe the IP player will check back (low c-bet frequency on this board), but wants to build the pot.

## Summary

| Concept | Formula | Key Insight |
|---|---|---|
| EV with position | $e \cdot \text{ER} \cdot P$ | ER > 1 possible IP; < 1 OOP with draws |
| Check-raise bluff ratio | $\alpha_R = (R-b)/(P'+R)$ | Derived from IP player's MDF facing raise |
| IP calling threshold | $e^* = c/(\text{ER}_{IP} \cdot P)$ | Lower threshold than OOP due to ER advantage |
| C-bet bluff limit | bluffs $\leq \alpha \cdot$ value | MDF-derived balance for aggressor |
