# Rapid-Fire: Reasoning and Test-Time Compute

**"What is RLVR?"**
> RL from verifiable rewards: replace the learned reward model with a checker — answer matching, unit tests, a proof checker. The reward is ground truth rather than a proxy, so there is almost nothing to hack and you can optimize far harder and longer than RLHF allows.

**"Why does the KL penalty matter less here?"**
> In RLHF the KL is what stops the policy exploiting a flawed reward model. A checker cannot be exploited that way, so the constraint is doing much less work.

**"Why do the outputs get long if nobody rewards length?"**
> More tokens raise the chance of reaching a correct answer, and correctness is the only thing rewarded, so backtracking and self-checking emerge instrumentally. Length is a symptom — forcing a non-reasoning model to emit more tokens does not confer the capability.

**"What is the catch with length?"**
> A token-mean loss dilutes the penalty on long wrong answers, biasing toward verbosity. Whether you normalize by tokens or by sequence is a real design decision.

**"pass@k looks amazing. What is wrong with it?"**
> It answers "was any sample right", which you can only use if a verifier tells you *which*. With a verifier it is legitimate. Without one you are majority voting, which is capped by how often the modal answer is correct — a ceiling that does not move with more samples.

**"When does more thinking stop helping?"**
> Immediately, on problems beyond the model's reach: you get long, confident, wrong reasoning. On problems within reach, accuracy is roughly linear in log compute and then saturates. So the win is adaptive budgeting, not a bigger fixed budget — a fixed budget overspends on easy problems and underspends on hard ones simultaneously.

**"Is the chain of thought faithful?"**
> Not reliably. It is causal — those tokens condition later ones — but it is not a transcript of the forward pass, and models produce reasoning that does not reflect the real reason for the answer.

**"So why not train on it to make it better?"**
> Because optimizing visible reasoning teaches the model to produce reasoning that *scores* well, which destroys its value for oversight. Several labs deliberately leave the CoT unoptimized for exactly this reason.

**"Why distil instead of running RL on the small model?"**
> SFT on traces from a strong model transfers most of the behaviour far more cheaply, and beats running RL on the small model directly. The caveat: it inherits the teacher's ceiling, and the student has been shown what discovery looks like rather than discovering anything.

**"How does this break evaluation?"**
> An accuracy number without a compute budget is not a claim. Always ask: how many tokens, how many samples, and was there a verifier in the loop?

## Going deeper

- [Let's Verify Step by Step](https://arxiv.org/abs/2305.20050) — process versus outcome supervision; the paper the whole line argues with.
- [DeepSeek-R1](https://arxiv.org/abs/2501.12948) — the public account of RL-from-a-checker producing reasoning behaviour, including the pure-RL variant and the distillation results.
- [Training Verifiers to Solve Math Word Problems](https://arxiv.org/abs/2110.14168) — where verifier-based sampling comes from, and the origin of GSM8K.
- [Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) — the useful corrective to "just ask it to check its work."
