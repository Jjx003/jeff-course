# The Formats in Detail

## ML coding

**Shape.** 45 minutes, a shared editor, sometimes with execution and sometimes without. You are asked to implement something: an architecture component, a decoding strategy, a loss function, a classical ML algorithm, or occasionally something odd that tests whether you can think in tensors at all.

**What is actually being scored:**

- **Correctness under a clock.** Does it run, and produce the right shapes and the right numbers?
- **Tensor fluency.** Do you reach for the right operation, or do you write a Python loop over the batch dimension? Do you know what `view` vs `reshape` vs `permute` do to strides, and when `.contiguous()` is required?
- **Debugging method.** Something will be wrong. The interviewer is watching how you find it. Printing shapes is not embarrassing; guessing is.
- **Narration.** You are expected to talk. Eight silent minutes reads as being stuck even when you are not.

**Frequent prompts, roughly in order of how often they appear:**

- Multi-head causal self-attention from scratch.
- A full transformer block, then a full decoder-only LM.
- Debug this transformer — a working implementation with three to six seeded bugs.
- Sampling: temperature, top-k, top-p, and why each exists.
- KV-cached generation.
- A loss function from a paper description. DPO and GRPO are the current favorites.
- Byte-pair encoding: train it, or encode with it.
- Something classical: k-means, logistic regression with hand-written gradients, a decision-tree split.

**The numpy exception.** Occasionally you are asked for numpy rather than PyTorch, usually when the point is writing a backward pass by hand. You are not expected to be fluent in numpy API quirks; you are expected to know the chain rule and the shapes.

## General coding

Ordinary data-structures-and-algorithms work, frequently wearing an ML costume: merge these overlapping token spans, find the top-k logits without sorting, run a sliding window over a token stream. LeetCode 75 or Blind 75 is the right preparation surface, and it is not optional — the same primitives show up inside ML coding interviews, and being slow at them costs you the time you needed for the actual problem.

## Technical discussion

This format splits into two very different interviews that share a name.

**Rapid-fire breadth.** A list of questions, thirty seconds to three minutes each. *Name the ways of encoding position. Why RMSNorm instead of LayerNorm? What is 5D parallelism? PPO versus GRPO? What breaks first when you scale context to 128k?* The goal is to signal that you have the field loaded. Hedging and half-answers score badly; so does bluffing, because the follow-up will catch it. "I do not know that one" costs you almost nothing when the other twelve answers were crisp.

**Experiment design.** An extended conversation about one problem: *How would you find out whether this model memorized the eval set?* or *You want to know if a bigger vocabulary helps. Design the experiment.* You will be pushed on your choices, handed hypothetical results, and asked what you would run next. This is the interview that most resembles the job. It rewards saying explicitly what would change your mind.

## Research discussion

Start with a project, follow the conversation wherever it goes, including into other papers on your CV. Prepare by stepping back from the work: why did you choose it, what do you now believe that you did not before, what would you do differently, what is the promising next direction. Tailor the framing to the role — interviewers are tired, and hitting the keywords that make your profile obviously relevant is a kindness to them and to you.

If you do not have publications, this format becomes "tell me about the hardest technical thing you have built," and the same preparation applies: motivation, choices, evidence, what you learned, what is next.

## Math

Ranges from logic puzzles to genuine pen-and-paper derivations. Probability is the most common by a wide margin — expectation, variance, conditioning, memorylessness, the standard distributions and when each applies. Linear algebra appears as eigenvalues, rank, projections, and norms. Calculus appears as derivatives you should be able to produce cold: sigmoid, softmax, cross-entropy with respect to logits.

Not every company has this interview. If yours does, it is worth a dedicated day of preparation, and modules 35–38 are that day.

## Behavioral

Textbook behavioral questions, occasionally with an AI-safety or societal-impact question attached. This is the format that most often surprises technically strong candidates, because it feels like it needs no preparation and then does. Reconstructing a hazy memory while simultaneously narrating it is a genuinely hard cognitive task, and it is why a collaborative, well-liked person can fail a behavioral interview outright.

The fix is mechanical: build a story bank in advance. Eight to twelve concrete episodes, mapped onto the standard question shapes, so that during the interview you are *retrieving*, not *reconstructing*. Module 42 walks through it.

## Job talk

Shorter and narrower than an academic talk — typically 30 to 45 minutes on one paper or one direction, rather than a survey of everything you have done. Depth on the first-author work, brief coverage of adjacent work, and a through-line. Expect interruptions; they are engagement, not hostility.

# What They Are Really Deciding

Under all six formats, a debrief comes down to three questions.

**Can they do the work?** This is what the coding and math formats measure. It is the most heavily weighted axis and the one you have the most control over.

**Will they figure out what to work on?** This is the experiment-design and research-discussion axis: taste, judgment, knowing which experiment settles a question. Hard to fake, and the reason "what would you do next" comes up so often.

**Do I want them in the room at 11pm before a launch?** The behavioral axis, plus every incidental interaction across the loop. Being pleasant to work with, taking a hint gracefully, and being honest about what you do not know all count here.

A strong loop is not one where you knew everything. It is one where the interviewer could picture you on the team.
