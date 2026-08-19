# Preparing the Core Story

Pick **one** project to be your primary. It should be the one where you had the most ownership, not necessarily the one with the best venue or the most citations. Ownership is what lets you answer follow-ups three levels deep, and follow-ups three levels deep are where the interview is decided.

Prepare it at four depths, and be able to switch between them on cue:

| Depth | Length | Use when |
|---|---|---|
| One sentence | 10 seconds | in the CV walkthrough |
| The pitch | 2 minutes | "tell me about a project" |
| The deep dive | 10 minutes | when they engage |
| Total recall | unbounded | when they push on a specific choice |

## The two-minute pitch

A structure that works:

1. **The problem, and why anyone should care.** One or two sentences, in terms a person outside your subfield understands.
2. **Why it was hard.** What made the obvious approach fail. This is the sentence that earns their attention.
3. **The key idea.** One sentence. If you cannot say it in one sentence you do not yet understand what you did.
4. **The evidence.** The single most convincing result, with a number.
5. **What it means.** The implication that outlives the paper.

Then stop and let them steer. Talking for eight minutes uninterrupted is a failure mode, not thoroughness — it means you did not give them a place to engage.

## The four questions to over-prepare

**"Why this problem?"** — The bad answer is "my advisor suggested it" or "it was an open problem". The good answer shows *taste*: you noticed something that did not fit, or a gap between what people assumed and what was actually true, or a capability that had just become possible. Taste is the thing being measured.

**"What surprised you?"** — This is the highest-signal question in the whole format, and the most commonly fumbled. A real answer proves you engaged with reality rather than executing a plan. Have a specific one: a result that came out backwards, an assumption that turned out to be load-bearing, a baseline that was much stronger than expected.

**"What is wrong with this work?"** — Interviewers ask this to see whether you can be honest about your own output. Naming a real limitation makes everything else you have said more credible. Naming a fake one ("it could be scaled up more") makes everything else less credible. Have a genuine weakness, and have the reason you shipped anyway.

**"What would you do next?"** — This is the closest proxy for what you would be like as a colleague. Have two or three concrete directions, with a sense of which is most promising and why. "I would extend it to more languages" is weak. "The result only holds when the tokenizer and the model share a training corpus, and I would test whether that is what actually drives it, because if so it changes how people should build tokenizers" is strong.

## Handling the hard follow-ups

**"Why didn't you try X?"** — Often they are right, and saying so is fine. "We considered it; we ruled it out because Y, and in hindsight that reasoning was weaker than I thought" is a strong answer. Defending a decision you no longer believe is a weak one.

**"How do you know it wasn't just Z?"** — They are asking about a confound. Either you controlled for it (say how) or you did not (say so, and say what experiment would settle it). Inventing a control you did not run is the one genuinely fatal move, because they will keep pulling.

**"What if I told you the result doesn't replicate?"** — Sometimes a stress test rather than a real claim. The good response is curiosity: what setup, what differences, which direction. Defensiveness scores badly; so does immediate capitulation.

**Something you genuinely do not know.** Say so, then say how you would find out. "I do not know — I would check whether the effect survives when you control for sequence length, because that is the most likely confound" is a good answer, and pretending is not.

# The Job Talk

For scientist roles at larger labs. Shorter and narrower than an academic job talk: typically 30–45 minutes on **one paper or one direction**, not a survey.

The structure that works:

- **2 minutes:** who you are and the through-line. What is the question you keep coming back to?
- **25 minutes:** the main work, in depth.
- **5 minutes:** adjacent work, briefly, showing breadth.
- **5 minutes:** where you are going, and why it connects to what this lab does.

Practical notes:

- **Expect interruptions**, and welcome them. Unlike an academic talk, engagement is a good sign. Budget for it: plan 30 minutes of content for a 45-minute slot.
- **The through-line matters more than the completeness.** A talk that shows one coherent research direction reads better than a survey of five unrelated projects, even if the survey represents more work.
- **Land the "why here".** The last five minutes should make it obvious why your next direction is one *this lab* should want. That requires actually knowing what they work on.

# The CV Walkthrough

Before the deep dive, many interviews open with "walk me through your background". Two to three minutes, and it is worth scripting because it is the frame everything else hangs on.

Structure it as a **narrative with a direction**, not a chronology. The version that works:

> "I started in X because of Y. That led me to notice Z, which is what most of my recent work has been about. The thread through it is [one sentence]. Which is why I am interested in what you are doing on [their thing]."

The two things to get right: the through-line, and the ending that points at *them*. A chronological list of projects is the default, and it is the version that leaves the interviewer having to do the synthesis themselves.
