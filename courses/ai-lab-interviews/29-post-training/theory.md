# SFT

Standard next-token cross-entropy on instruction/response pairs, with the loss **masked on the prompt** so only response tokens are trained.

Two details that come up:

- **Masking the prompt.** Training on prompt tokens teaches the model to generate instructions, which is not the job. Every serious SFT implementation masks them; forgetting to is a plausible interview bug to be asked about.
- **Packing versus padding.** Packing several short examples into one sequence avoids wasting compute on padding, but requires blocking attention across example boundaries — otherwise one example attends to another.

SFT's ceiling: it can only imitate. If your demonstrations are mediocre, so is the model, and there is no mechanism for it to become better than the data.

# The Reward Model

Trained on preference pairs $(x, y_w, y_l)$ — a prompt with a preferred and a rejected response — under the Bradley-Terry model:

$$P(y_w \succ y_l \mid x) = \sigma\big(r(x,y_w) - r(x,y_l)\big)$$

$$\mathcal{L}_{RM} = -\mathbb{E}\big[\log\sigma\big(r(x,y_w)-r(x,y_l)\big)\big]$$

Architecturally it is the LM with the token head replaced by a scalar head, initialized from the SFT model.

Note the reward is only ever identified **up to a shift**: only differences appear in the loss. That is fine for ranking and matters for a couple of the derivations below.

# RLHF with PPO

$$\max_{\pi}\ \mathbb{E}_{x\sim D,\,y\sim\pi}\big[r(x,y)\big] - \beta\,\mathrm{KL}\big(\pi \,\|\, \pi_{ref}\big)$$

## Why the KL term is not optional

Without it the policy will find whatever maximizes the reward model, and the reward model is an imperfect proxy trained on a narrow distribution. Left unconstrained, policies discover degenerate outputs that score highly and are useless — the canonical example being responses that are excessively long, hedged, and agreeable, because human raters mildly prefer those and the model pushes the trend to absurdity.

The KL penalty keeps the policy near a distribution the reward model was actually trained on. $\beta$ is the dial between "optimize the proxy hard" and "stay in-distribution", and stating that trade-off is the answer to "why the KL term?"

## What PPO needs in memory

Four models: the **policy**, a **value network** (critic), the frozen **reward model**, and the frozen **reference** policy. That is roughly 4x the memory of the policy alone, plus the sampling loop, plus PPO's own hyperparameters — clip ratio, GAE $\lambda$, value-loss coefficient, epochs per batch.

PPO works. It is also notoriously fiddly, and the cost and complexity are exactly what the next two methods attack.

## The clipped objective

$$\mathcal{L}^{CLIP} = \mathbb{E}\Big[\min\big(\rho_t A_t,\ \mathrm{clip}(\rho_t, 1-\epsilon, 1+\epsilon)A_t\big)\Big], \qquad \rho_t = \frac{\pi_\theta(a_t|s_t)}{\pi_{old}(a_t|s_t)}$$

The clip bounds how far a single update can move the policy from the one that generated the data, which is what makes multiple epochs over the same rollouts safe. Note it is one-sided on the negative-advantage branch: if the ratio rises on a sample with $A < 0$, `min` picks the unclipped term and the penalty is unbounded, which is what Dual-Clip PPO later addressed.

# DPO

The insight: for the KL-regularized objective, the optimal policy has a **closed form** in terms of the reward:

$$\pi^*(y|x) = \frac{1}{Z(x)}\pi_{ref}(y|x)\exp\!\left(\frac{1}{\beta}r(x,y)\right)$$

Invert it to express the reward in terms of the policy:

$$r(x,y) = \beta\log\frac{\pi^*(y|x)}{\pi_{ref}(y|x)} + \beta\log Z(x)$$

Now substitute into the Bradley-Terry loss. Since only reward *differences* appear, the intractable partition function $Z(x)$ **cancels**, leaving:

$$\mathcal{L}_{DPO} = -\mathbb{E}\left[\log\sigma\left(\beta\log\frac{\pi_\theta(y_w|x)}{\pi_{ref}(y_w|x)} - \beta\log\frac{\pi_\theta(y_l|x)}{\pi_{ref}(y_l|x)}\right)\right]$$

**The one-sentence version, worth memorizing:** *the language model is secretly its own reward model, so you can train directly on preference pairs with a simple classification loss.*

**What it buys:** no reward model, no sampling loop, no value network. Two forward passes over fixed data, one through the policy and one through the frozen reference. Vastly cheaper and vastly more stable.

**What it costs, and you should volunteer this:**

- It is **off-policy**. It only ever sees the responses in your dataset, so it cannot discover anything better than what is already there.
- Its gradients on the two sequence log-probabilities are analytically equal and opposite, but nothing anchors their *absolute* values — only the gap. Empirically, through shared parameters and softmax normalization, the rejected response's probability usually falls further than the chosen one's rises, so both can drift down while the loss improves. That degrades the model in ways the training curve does not show.
- It is **sensitive to how the preference data was generated**. If the pairs came from a different model, you are partly teaching yours to imitate that one.

**Variants:** IPO (a different loss that avoids DPO's overfitting behavior), KTO (learns from single thumbs-up/thumbs-down labels rather than pairs), ORPO (folds preference learning into SFT so the reference model disappears too).

# GRPO

Group Relative Policy Optimization removes the **value network**.

PPO needs a critic to estimate the baseline $V(s)$ so advantages have low variance. That critic is another model to train, another model to hold in memory, and another thing to be unstable.

GRPO's substitution: for each prompt, sample a **group** of $G$ responses, and use the group's own reward statistics as the baseline.

$$A_i = \frac{r_i - \mathrm{mean}(r_1..r_G)}{\mathrm{std}(r_1..r_G)}$$

A response that beat its siblings gets a positive advantage; one that lost gets a negative one. No critic required.

$$\mathcal{J}_{GRPO} = \mathbb{E}\left[\frac{1}{G}\sum_{i=1}^{G}\min\big(\rho_i A_i,\ \mathrm{clip}(\rho_i, 1-\epsilon, 1+\epsilon)A_i\big) - \beta\,\mathrm{KL}(\pi_\theta\|\pi_{ref})\right]$$

Note this is an objective to **maximize**. Implementations minimize its negation, which is what module 30 writes and what the code there returns — getting that sign backwards trains confidently in the wrong direction.

**Why it works especially well with verifiable rewards.** For maths and code you have a *checker*, not a learned reward model: does the answer match, do the tests pass. That gives a clean, unhackable, binary reward — and with a binary reward the group *mean* is exactly the pass rate for that prompt, so an advantage measures how a response did relative to how hard the problem turned out to be. That self-normalizing signal is beautifully well behaved.

**The trade-offs to state:** you need $G$ samples per prompt, typically 8–64, so generation cost multiplies. And if all $G$ responses get the same reward, the advantage is zero and the prompt contributes no gradient at all — which means problems that are uniformly too easy or too hard are wasted, and prompt curriculum matters.

**A current critique worth knowing:** dividing by the group's std amplifies advantages on prompts where the group barely disagrees, up-weighting the easiest and hardest questions; variants like Dr. GRPO drop the std division and keep only the mean baseline. Module 30 implements the original formulation and states the critique.

![Two panels. Left: advantage on a correct response against the number of correct responses in a group of eight, with the std-normalized curve rising steeply at one correct and the mean-only curve staying low and flat. Right: gradient weight relative to mean-only, peaking at 3.0x for the one-of-eight and seven-of-eight groups and bottoming at 2.0x at four of eight.](/courses/ai-lab-interviews/grpo-advantage.svg)

# Reward Hacking

The failure mode that unifies this whole module: **the policy optimizes the measure rather than the thing you meant**.

Real, documented examples:

- Length bias — longer responses score higher, so responses inflate.
- Sycophancy — agreeing with the user scores well.
- Format exploitation — the reward model over-rewards bullet points, headers, or hedging language.
- In code RL, writing tests that pass trivially, or special-casing the test inputs.

**Detection:** watch the KL from the reference alongside the reward. Reward climbing while KL grows fast is the signature. Hold out prompts the reward model never saw. And read samples — a surprising amount of reward hacking is obvious to a human in thirty seconds and invisible in every metric.

**Mitigation:** the KL penalty, reward-model ensembles, periodically retraining the reward model on fresh on-policy data, and preferring verifiable rewards wherever the domain allows.

# Where the Field Is

**Verifiable-reward RL** is the current centre of gravity. Maths, code, and formal reasoning have automatic checkers, so you can run large-scale RL without a learned reward model and without most of the hacking risk. This is what produced the recent step change in reasoning models.

**Inference-time compute** is the other axis: rather than making the model better, let it think longer — more tokens, sampling and reranking, search. It trades serving cost for capability at fixed training cost, and it has its own scaling curves.

**Process versus outcome supervision.** Rewarding each reasoning step rather than only the final answer gives denser signal and less reward hacking, at the cost of much more expensive labels.
