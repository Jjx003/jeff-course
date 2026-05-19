# Board Texture: The Mathematics of Range Interaction

## Combo Counting as a Texture Metric

The formal basis of board texture analysis is **combo counting**: for any board, count how many combinations in each player's range reach specific strength tiers. Define:

- $N_V^A$ = number of value combos (two pair or better) in the aggressor's range on this board
- $N_V^C$ = same for the caller's range
- **Nut advantage ratio** $= N_V^A / N_V^C$

A ratio $> 1$ favours the aggressor; $< 1$ favours the caller.

**Example — $A\heartsuit 7\clubsuit 2\diamondsuit$:**

A UTG opener has approximately:
- Sets: $AA$ (3 combos with one ace on board), $77$ (3 combos), $22$ (3 combos) → 9 set combos
- Two pair: $A7s/A7o$ (roughly 4 combos), $A2s/A2o$ (roughly 4 combos), $72s/72o$ (roughly 4 combos) → ~12 two-pair combos

A big blind caller (facing a UTG raise) has approximately:
- Sets: $77$ (3 combos, but many fold pre-flop), $22$ (3 combos) → 4–6 set combos
- Two pair: fewer $Ax$ combos since many are 3-bet pre-flop

A rough ratio of $2:1$ or greater nut combos for the aggressor confirms the range-bet strategy: the aggressor's nut advantage is so large that even small bets extract positive EV across the entire range.

## The Relationship Between Nut Advantage and Bet Size

From Module 13, the value:bluff ratio at equilibrium must satisfy:

$$\frac{\text{value combos}}{\text{bluff combos}} = \frac{1}{\alpha} = \frac{P + b}{b}$$

Where $\alpha = b/(P+b)$ is the pot fraction the defender risks. When the aggressor has massive nut advantage (many strong combos), they can achieve the required value:bluff ratio at *large* bet sizes — there are enough value combos to support a large bluff-to-value ratio at high stakes.

On wet boards where the caller has more strong combos, the aggressor attempting a large polarised bet runs out of value combos to fill the required ratio. They must either bluff more (risking over-bluffing) or bet smaller (accepting lower EV per bet). This is the mathematical reason why **nut advantage → large size** and **range advantage without nut advantage → small size**.

## Range Betting: The Small-Size Justification

A range bet is profitable when the EV of betting a small size with every hand exceeds the EV of checking with every hand. Let $f_f$ be the opponent's fold frequency on the flop. The EV of a small bet $b$ with a weak bluff hand is:

$$\text{EV}_{bet} = f_f \cdot P - (1 - f_f) \cdot b + (1 - f_f) \cdot e_{\text{bluff}} \cdot (P + 2b)$$

where $e_{\text{bluff}}$ is the bluff hand's equity if called. On a dry board, the fold frequency $f_f$ is higher because the caller's range has fewer strong hands. Even a hand with $e_{\text{bluff}} = 0$ can profit from a small bet when $f_f \cdot P > (1 - f_f) \cdot b$, i.e. when:

$$f_f > \frac{b}{P + b} = \alpha$$

This is the standard fold-equity threshold, and dry boards regularly provide sufficient fold frequency for small bets to profit even with air.

## Static vs Dynamic: The Turn EV Chain

The multi-street EV of a flop c-bet depends on the turn card distribution. Define $T = \{t_1, t_2, \ldots, t_{45}\}$ as the set of possible turn cards. The full EV of a flop c-bet is:

$$\text{EV}_{flop} = \sum_{t \in T} P(t) \cdot \text{EV}_{turn}(t | \text{flop bet called})$$

On a **static board**, most turn cards $t$ preserve the aggressor's range advantage, so $\text{EV}_{turn}(t)$ is positive for most $t$. The expected value of the flop c-bet is therefore robustly positive.

On a **dynamic board**, a large fraction of turn cards shift the range advantage — flush completions, straight completions — making $\text{EV}_{turn}(t)$ negative for many $t$. The expected value of the flop c-bet is lower, and may not justify high-frequency betting.

This formalises the intuition: high c-bet frequency on dry boards, lower frequency on wet boards.

## Equity Denial on Dynamic Boards

On wet boards, the caller's draws have theoretical equity. The aggressor can deny this equity by betting large, forcing a marginal call-or-fold decision. The condition under which a draw cannot profitably call is:

$$e_{\text{draw}} < \frac{b}{P + 2b}$$

For a flush draw with $e_{\text{draw}} \approx 0.19$ on the turn (one card left), the minimum bet that denies profitable continuation is:

$$b > \frac{e_{\text{draw}} \cdot P}{1 - 2 \cdot e_{\text{draw}}} = \frac{0.19P}{0.62} \approx 0.31P$$

A bet of 33% pot or more denies a pure flush draw profitable continuation — without any implied odds. Combined with implied odds (the draw must also consider future streets), slightly larger sizes are often required.

## Summary Table

| Concept | Formula | Application |
|---|---|---|
| Nut advantage ratio | $N_V^A / N_V^C$ | Ratio > 1 → aggressor bets large |
| Bluff:value at equilibrium | $\text{bluffs} = \alpha \cdot \text{value}$ | Calibrate polarised range at any size |
| Fold equity threshold | $f_f > b/(P+b)$ | Min fold rate for bluff profitability |
| Equity denial condition | $b > e \cdot P / (1 - 2e)$ | Min size to price out a draw |
| Range bet EV | $f_f \cdot P - (1-f_f) \cdot b + (1-f_f) \cdot e \cdot (P+2b)$ | Per-hand EV of a range bet |
