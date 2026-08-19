# Reliability Compounds

Start with the arithmetic, because it drives every design decision that follows.

If a task takes $n$ steps and each succeeds independently with probability $p$, the task succeeds with probability $p^n$.

![Two panels. Left: end-to-end success against number of steps, for per-step reliability 90, 95, 99 and 99.9 percent, with a dashed line at 50 percent that the 99 percent curve crosses near step 70. Right: the per-step error budget required to hit 50, 90 and 99 percent end-to-end success, against task horizon on log axes, falling to about 0.1 percent for a 100-step task at 90 percent.](/courses/ai-lab-interviews/agent-horizon.svg)

99% per step is a coin flip by step 70. To finish a 100-step task nine times in ten you need a per-step error budget around 0.1%. No amount of prompt engineering closes a gap of that size.

**The honest caveat, which is also the interesting part:** steps are not independent. Errors correlate — one bad decision poisons the observations that follow — which makes it worse than the model suggests. But a model that *notices and recovers* converts some failures back into successes, which makes it better. Those two effects are why the real question is not "how accurate is each step" but "what happens after a step goes wrong."

That reframing is the single most useful thing in this module. It says the engineering effort should go into **recovery**, not accuracy:

- **Checkpoint** so a failure costs one segment rather than the whole run.
- **Verify** cheaply and often — a test suite, a type checker, a schema — so errors surface one step after they happen rather than forty.
- **Make failure legible.** A tool that returns a clear error the model can act on is worth more than one that silently returns something plausible.
- **Bound the blast radius.** Actions that cannot be undone deserve a confirmation step, for the same reason you would want one.

A model that fails loudly and recovers beats a model that is slightly more accurate and fails silently.

# Context Is the Scarce Resource

Every step appends observations. Tool outputs are verbose — a file listing, a stack trace, an HTTP response — and they arrive whether or not they turn out to matter. A long-running agent will exhaust any context window, and the interesting failures happen well before it is full.

**The failure modes have names worth knowing:**

- **Dilution.** The goal stated 200k tokens ago competes with a wall of recent tool output. Attention is finite; the original instruction gets crowded out.
- **Poisoning.** A wrong observation or a hallucinated fact enters the context and is then treated as established for the rest of the run.
- **Distraction.** Irrelevant retrieved material pulls the model off-task in a direction it would never have chosen unprompted.

**What actually helps:**

- **Compact rather than truncate.** Summarize completed segments into a short state description and drop the raw transcript. Truncation from the front deletes the goal; truncation from the back deletes what just happened.
- **Externalize state.** A file, a scratchpad, a task list. Anything the model can re-read on demand does not have to occupy context permanently, and it survives a compaction.
- **Return less.** The largest wins are usually in tool design: return the twenty relevant lines, not the whole file. This is unglamorous and it is where most of the improvement lives.
- **Isolate.** Give a sub-task its own fresh context and return only its conclusion. The parent never sees the sub-task's noise.

"Context engineering" is a fashionable phrase for an ordinary engineering discipline: deciding what information is in front of the model at each step, and paying attention to the fact that this is a budget.

# Training for It

**Tool use as a token problem.** Tool calls are just structured tokens. The base capability comes from pretraining data containing code and structured output; SFT on demonstrations teaches the format and when to reach for which tool. This gets you a model that calls tools competently and plans badly.

**RL over trajectories** is what improves the planning, and it is much harder than single-turn RL:

- The reward arrives at the end of a long trajectory, so credit assignment across steps is genuinely hard — the classic sparse-reward problem, at a scale where each episode is expensive.
- Episodes are slow and stateful. You cannot batch 512 rollouts of a task that mutates a real filesystem without 512 sandboxes.
- The environment is part of the training loop, so environment engineering *is* research engineering. A meaningful share of the work at labs doing this is building and maintaining sandboxes.

**Where the reward comes from** is the same question as module 47, and the same answer: verifiable outcomes. Did the tests pass, does the file exist, did the transaction reconcile. Agentic RL is largely RLVR with a longer horizon and a much more expensive environment, and the domains where it works best — software engineering above all — are exactly the ones with cheap, trustworthy checkers.

# Evaluating It

Every property that makes single-turn evaluation tractable is absent here.

- **Stateful.** Runs are not independent; the environment must be reset, and reset is often incomplete.
- **Long.** A task may take hours, so you can afford far fewer samples, and variance is high exactly when you can least afford it.
- **Path-dependent.** Two runs that both succeed may have done completely different things, one of them fine and one of them appalling.
- **Contaminable in a new way.** Public agentic benchmarks leak, and their environments get scraped along with their solutions.

The practical consequences:

- Report **pass@1 with confidence intervals over many trials**, not a single run. Single-run agentic numbers are close to meaningless and treating them as meaningful is a red flag.
- Measure **cost alongside success**: an agent that succeeds by spending 4M tokens is a different product from one that succeeds in 200k, and the raw success rate hides that entirely.
- **Look at trajectories, not just outcomes.** The failure modes you care about — a destructive action, a fabricated result — often occur inside runs that succeeded.
- **Report the harness.** Scaffolding, tool set, retry policy, and context strategy affect results as much as the model does, which is why cross-paper agentic comparisons are so unreliable.

If someone shows you an agentic benchmark result, the questions that mark you out are: how many trials, what was the harness, and what did the failures look like.
