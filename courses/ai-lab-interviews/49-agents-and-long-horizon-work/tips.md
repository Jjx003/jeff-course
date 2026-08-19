# Rapid-Fire: Agents

**"Why do agents fail at long tasks?"**
> Reliability compounds. 99% per step is a coin flip by step 70; a 100-step task at 90% end-to-end needs a per-step error budget near 0.1%. Steps also are not independent — errors poison later observations — so it is worse than the clean multiplication suggests.

**"So how do you fix it?"**
> Mostly not by making steps more accurate. Invest in recovery: checkpoint so a failure costs one segment, verify cheaply and often so errors surface immediately, make tools fail loudly with actionable errors, and gate irreversible actions. A model that recovers beats a slightly more accurate one that fails silently.

**"Agent versus a chain of prompts?"**
> The model chooses the next action based on observations it has not seen before, and the loop length is not known in advance. A fixed chain has neither property.

**"What breaks first at long horizons?"**
> Context. Dilution (the goal is crowded out by recent tool output), poisoning (a wrong observation becomes established fact), distraction (irrelevant retrieval pulls the model off-task). All three appear well before the window is actually full.

**"What do you do when context fills up?"**
> Compact, do not truncate — summarize completed segments to a short state description. Externalize state to files the model can re-read. Design tools to return less. Isolate sub-tasks in their own context and return only conclusions.

**"How would you train a model to use tools?"**
> SFT on demonstrations gets format and tool selection. Planning needs RL over whole trajectories, which is hard: sparse terminal reward, expensive stateful episodes, and an environment that is now part of your training loop. Reward comes from verifiable outcomes — tests pass, file exists — so it is RLVR with a longer horizon.

**"Why is agentic RL so much more expensive than single-turn?"**
> Each episode is long and mutates real state, so you need a sandbox per rollout and you cannot batch cheaply. A serious fraction of the engineering is environments, not algorithms.

**"How do you evaluate an agent?"**
> pass@1 with confidence intervals over many trials — single-run numbers are meaningless. Report cost alongside success. Inspect trajectories, because destructive or fabricated actions often occur inside runs that succeeded. And report the harness: scaffolding and retry policy move results as much as the model does.

**"What is the strongest thing you can say about agent evaluation?"**
> That the benchmark number and the harness are not separable, so cross-paper comparisons of agentic results are usually not comparisons at all.

## Going deeper

- [ReAct](https://arxiv.org/abs/2210.03629) — the interleaved reasoning-and-acting loop everything else builds on.
- [Toolformer](https://arxiv.org/abs/2302.04761) — self-supervised tool-call learning; a clean idea worth knowing even though practice moved past it.
- [SWE-bench](https://arxiv.org/abs/2310.06770) — the benchmark that made agentic evaluation concrete, and a good case study in harness sensitivity.
- [tau-bench](https://arxiv.org/abs/2406.12045) — multi-turn tool use with rule-following, and an explicit pass^k metric for consistency across trials.
