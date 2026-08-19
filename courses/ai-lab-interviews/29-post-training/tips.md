# Rapid-Fire Answers

**"Walk me through RLHF."**
> Pretrain, SFT on instruction data, train a reward model on preference pairs under a Bradley-Terry loss, then optimize the policy with PPO against that reward plus a KL penalty to the SFT reference. Four models in memory: policy, value network, reward model, reference.

**"Why the KL penalty?"**
> The reward model is a proxy trained on a narrow distribution. Without a constraint the policy finds degenerate outputs that score highly and are useless. The KL keeps the policy where the reward model is still meaningful, and beta is the dial between optimizing the proxy and staying in distribution.

**"Why does DPO not need a reward model?"**
> The KL-regularized objective has a closed-form optimal policy, which you can invert to express the reward in terms of the policy and reference. Substituting into the Bradley-Terry loss makes the partition function cancel, because only reward differences appear. The model is secretly its own reward model.

**"What does DPO give up?"**
> It is off-policy — it only sees the responses in your dataset, so it cannot discover anything better than what is there. It also tends to push down the rejected response more than it pushes up the chosen one, which can drag both down.

**"PPO versus GRPO?"**
> GRPO removes the value network. Instead of a learned critic for the baseline, it samples a group of G responses per prompt and normalizes rewards within the group. Cheaper and more stable, at the cost of G samples per prompt — and if all G get the same reward the advantage is zero and the prompt contributes nothing.

**"Why does GRPO suit maths and code?"**
> Verifiable rewards. A checker gives a clean binary signal instead of a learned proxy, so there is almost nothing to hack — and with a binary reward the group mean is exactly the prompt's pass rate, so an advantage measures how a response did relative to the problem's difficulty. That self-normalizes.

**"What does RL add over SFT?"**
> SFT can only imitate, and treats every token in a good response as equally correct. RL optimizes a scalar objective, so it can learn a response is bad without being shown a better one, explore past the demonstration distribution, and give credit at the level of the whole response — which is the only way to supervise a chain of thought.

**"How would you detect reward hacking?"**
> Watch KL from the reference alongside the reward: reward climbing while KL grows fast is the signature. Hold out prompts the reward model never saw. And read samples — a lot of reward hacking is obvious to a human and invisible in every metric.

# Traps

- **Saying DPO is "just simpler RLHF".** It is a different objective with a different failure mode, and being off-policy is a real limitation worth naming.
- **Forgetting to mask the prompt in SFT.** You would be training the model to generate instructions.
- **Not knowing PPO holds four models.** That memory cost is the reason the other methods exist.
- **Claiming GRPO is strictly better.** It needs G samples per prompt and gives zero gradient when a group is uniform.
- **Ignoring reward hacking entirely.** Volunteering it signals you have thought about deployment, not just the loss.

# Further Reading

- [Training language models to follow instructions with human feedback](https://arxiv.org/abs/2203.02155) — InstructGPT, the canonical RLHF pipeline.
- [Direct Preference Optimization](https://arxiv.org/abs/2305.18290) — the DPO derivation is four pages and worth working through by hand.
- [DeepSeekMath](https://arxiv.org/abs/2402.03300) — where GRPO was introduced.
- [DeepSeek-R1](https://arxiv.org/abs/2501.12948) — large-scale verifiable-reward RL for reasoning.
- [Illustrating Reinforcement Learning from Human Feedback](https://huggingface.co/blog/rlhf) — the best short visual explanation.
- [Nathan Lambert's RLHF Book](https://rlhfbook.com/) — the most complete current treatment.
