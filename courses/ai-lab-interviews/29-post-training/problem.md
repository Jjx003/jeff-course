# Post-Training: SFT, RLHF, DPO, GRPO

"What is the difference between PPO and GRPO?" is a real, current rapid-fire question. So is "why does DPO work without a reward model?" This is the fastest-moving area in the course, and it is where interviewers most often check whether you have read the last two years of papers or only the first.

The organizing idea makes it much easier to hold:

> **Each method after RLHF is defined by what it deletes.** DPO deletes the reward model and the sampling loop. GRPO deletes the value network. Knowing what was removed, and what that costs, is the whole conversation.

![A flow diagram of the RLHF pipeline — base model, SFT, reward model, PPO — with DPO and GRPO branching off, annotated with what each removes and where each is used.](/courses/ai-lab-interviews/posttraining-map.svg)

## What gets asked

- Walk me through the RLHF pipeline.
- Why is a KL penalty to the reference model necessary?
- Derive DPO, or at least explain why it works without a reward model.
- PPO versus GRPO — what did GRPO remove, and why could it?
- What is reward hacking and how would you detect it?
- Why does verifiable-reward RL work so well for maths and code?
- What does RL actually add over SFT?

## The pipeline

| Stage | Data | What it does |
|---|---|---|
| Pretraining | trillions of tokens of text | learns the distribution of language |
| SFT | 10k–1M instruction/response pairs | learns the *format* of being an assistant |
| Reward modeling | preference pairs | learns to score responses |
| RL (PPO/GRPO) | prompts + the reward signal | optimizes the policy against that score |

Or, skipping the middle two: **DPO** goes straight from preference pairs to a policy.

## What RL actually adds

The most interesting question in this module, and the one worth having a real opinion about.

SFT teaches the model to imitate good responses. It can only ever push toward the training distribution, and it treats every token in a good response as equally correct.

RL optimizes a *scalar objective*. It can learn that a response is bad without ever being shown a better one, it can explore beyond the demonstration distribution, and — critically — it provides signal at the level of the whole response rather than per token. That is why RL, not SFT, is what makes long-form reasoning work: there is no per-token supervision available for "did this chain of thought reach the right answer".
