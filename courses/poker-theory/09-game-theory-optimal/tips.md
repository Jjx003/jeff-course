# Tips and Going Deeper

## Thinking Prompts

**Before making a river decision, run this quick GTO sanity check:**

1. *If I always do X here, can villain exploit me?* — If yes, you need to mix.
2. *What is my bluff frequency telling villain?* — If you bluff every missed draw, observant villains will always call. Are you bluffing at $B/(P+B)$?
3. *Am I balanced?* — Does your betting range contain both value combos and bluffs? A range that only ever contains the nuts when it bets is obviously exploitable.
4. *Should I deviate?* — Do I have a reliable read that villain folds too much (→ bluff more) or calls too much (→ bluff less)? Without a read, default toward balance.

## Common Misconceptions

- **"GTO means I should call all river bets."** No — GTO requires calling exactly MDF = $P/(P+B)$ of your range. Against a pot-sized bet, call 50%; against a half-pot bet, call 67%.
- **"GTO is only for high-stakes players."** The conceptual framework — indifference, bluff ratios, MDF — is useful at any level as a framework for reasoning. You don't need to execute it precisely to benefit from understanding it.
- **"Exploitative play is better than GTO."** Against predictable opponents who make systematic mistakes, yes. Against unknown or strong opponents, GTO is safer. The right answer is: use both, switching based on the quality of your reads.
- **"If I play GTO I'll never lose."** GTO minimises *exploitation* not variance. You can run deep into negative variance while playing perfectly balanced frequencies.

## A Simple Live Test

The next time you face a river decision, before acting ask: "if villain always [calls/folds], what should I do?" If the answer is clearly "bluff more" or "bluff less," that's a signal your play is already tilting exploitative — and probably rightly so if you have a solid read.

## Going Deeper

- *The Mathematics of Poker* by Bill Chen and Jerrod Ankenman — the rigorous mathematical foundation for GTO poker; starts from first principles in game theory
- *GTO Poker Simplified* by Dara O'Kearney and Barry Carter — accessible introduction to applying GTO concepts at the table without a solver
- [Solving Poker with CFR (blog post by Marc Lanctot)](https://scholar.google.com/scholar?q=marc+lanctot+cfr+poker) — excellent technical overview of Counterfactual Regret Minimisation
- [PioSolver Free](https://piosolver.com) — the industry standard solver; the free version lets you experiment with river spots and see GTO frequencies hands-on
- *Lectures on Game Theory* by Robert Aumann — accessible introduction to Nash equilibrium from a Nobel laureate; goes well beyond poker but is worth reading

## Connecting the Dots

| Module | Concept | How it connects to GTO |
|---|---|---|
| 03 (Pot Odds) | Pot odds % | MDF = pot odds % of villain's call |
| 05 (EV) | EV = equity × pot | GTO maximises worst-case EV |
| 07 (Ranges) | Range construction | GTO ranges are balanced across all boards |
| 11 (MDF) | Minimum defense frequency | $P/(P+B)$ — the defender's GTO call frequency |
| 13 (Bet Sizing) | Why different bet sizes exist | Larger bets are polar; smaller bets are linear |
