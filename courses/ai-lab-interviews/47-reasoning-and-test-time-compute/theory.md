# A Third Axis

Pretraining scaling says: to make the model better, make it bigger and feed it more. Test-time scaling says: leave the model alone and let it spend more compute on the question in front of it.

These are not interchangeable. Pretraining compute is paid once and amortized over every query forever. Test-time compute is paid on every single query, by every user, for as long as the model is deployed. A lab weighing them is comparing a capital cost against an operating cost, which is why the interesting deployments distil an expensively-trained reasoning model down into something cheap to run.

## RLVR: what actually changed

The recipe that produced this generation is simpler than the one it replaced.

| | RLHF (module 29) | RLVR |
|---|---|---|
| Reward source | learned reward model | a checker: does the answer match, do the tests pass |
| Hackable? | yes, and reliably so | not really — the checker is ground truth |
| Needs preference data | yes, at scale | no |
| Works where | anything humans can rank | anything you can verify |
| KL to reference | essential, or it collapses | much less load-bearing |

The whole difficulty of RLHF is that your reward is a *proxy*, so the policy learns to exploit the proxy and you spend your KL budget holding it back. A checker is not a proxy. You can push much harder against it, for much longer, which is what makes the long training runs in this regime possible.

The catch is scope. RLVR needs a verifier, so it applies cleanly to mathematics, code, and formal tasks, and awkwardly to everything else. Extending it — LLM judges, rubric rewards, unit tests generated on the fly — is one of the live research directions, and "how would you get verifiable rewards for *this* domain" is a good question to have opinions about.

## Why the outputs get longer

Nobody rewards length. Length emerges because, within an episode, spending more tokens raises the chance of hitting a correct answer, and the correct answer is the only thing being rewarded. Backtracking, restating the problem, and checking work are all instrumentally useful, so the policy finds them.

Two consequences worth being able to state:

- **Length is a symptom, not the mechanism.** Forcing a non-reasoning model to emit more tokens does not confer the capability. The tokens have to be doing work.
- **It biases the optimizer.** Because the loss is typically a mean over tokens, longer wrong answers get their per-token penalty diluted. This is a real, documented bias — it is the second half of the Dr. GRPO critique you met in module 29 — and it is why implementations pay attention to whether they normalize by token count or by sequence.

## Where the compute stops paying

![Two panels. Left: accuracy against samples drawn on a log axis, with pass@k curves for three per-sample accuracies rising steeply toward 100 percent while flat dashed lines mark much lower majority-vote ceilings. Right: accuracy against reasoning tokens spent per problem on a log axis, three curves rising roughly linearly in log compute before flattening at different ceilings.](/courses/ai-lab-interviews/test-time-compute.svg)

Both panels are models, not measurements — they are there to fix the *shape* in your head.

**Left: the pass@k illusion.** If you draw $k$ independent samples, the chance at least one is right is $1-(1-p)^k$, which climbs fast. Headline "pass@256" numbers are real but they answer a question you usually cannot ask in production: *which* of those 256 was right? With a verifier you can find out, and pass@k is a legitimate deployed metric. Without one you fall back to majority voting, which is capped by how often the modal answer is correct — a ceiling that does not move no matter how many samples you draw. This is exactly why verifiable domains and open-ended ones behave so differently, and it is the single most common place people overclaim.

**Right: diminishing returns, per problem.** Accuracy rises roughly linearly in log compute and then saturates at whatever that problem's ceiling is. The three curves are the three cases you should have ready:

- **Within reach** — thinking longer converts to accuracy. This is the case everyone pictures.
- **At the edge** — thinking longer helps, then plateaus below 100%.
- **Out of reach** — thinking longer produces long, confident, wrong reasoning. Compute spent here is pure loss, and it looks exactly like the productive case from the outside.

The practical corollary is that the interesting engineering is **adaptive**: decide how long to think based on the problem, not on a fixed budget. Getting that decision right is worth more than a larger fixed budget, because a fixed budget simultaneously overspends on easy problems and underspends on hard ones.

## Distillation

Supervised fine-tuning on reasoning traces from a strong model transfers a surprising amount of the capability, at a small fraction of the training cost. Distilled small models beat same-size models trained with RL directly.

What you should be careful about claiming: this transfers the *behaviour*, and it inherits the teacher's ceiling. The distilled model has not discovered anything; it has been shown what discovery looks like. Whether that difference matters is an open question and a good one to be thoughtful about rather than confident on.

## Faithfulness

The chain of thought is not a transcript of the computation. It is text the model generated, which influences later tokens through the context — genuinely causal, but not a window into the forward pass. Models can and do produce reasoning that does not reflect the actual reason for the answer.

This is why several labs deliberately do **not** train against the content of the chain of thought: optimizing the visible reasoning teaches the model to produce reasoning that scores well, which destroys whatever monitoring value it had. Keeping the CoT unoptimized so it stays usable for oversight is a real safety argument, and one worth being able to make in a research discussion.

## How this changes evaluation

- A single accuracy number is now meaningless without a compute budget attached. "83% on AIME" is not a claim until you say at what token budget and with how many samples.
- Contamination gets worse, not better: reasoning benchmarks are small, heavily discussed, and the traces themselves leak into training corpora.
- Comparing an RL-trained model against a distilled one at equal parameter count compares two different things.

If an interviewer shows you a benchmark table from a reasoning model, the first question to ask is what the inference budget was. Asking it is the signal.
