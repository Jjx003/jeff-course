# Before You Start

## Get the loop breakdown from your recruiter

Ask, on the first call, in roughly these words: *"Which interview formats are in this loop, and what should I expect the coding interview to focus on?"* Recruiters answer this. The information reshapes weeks of preparation, and not asking is the most common unforced error in the whole process.

## Set up an interview-honest practice environment

- **Autocomplete off.** Disable Copilot, editor tab-completion, and any inline model. If your editor is suggesting `nn.Linear(` parameters, you are not practicing the thing being tested.
- **A blank file.** Most ML coding interviews start from nothing, not from a scaffold.
- **A visible timer.** Fifteen minutes for attention, forty-five for a full LM.
- **Out loud.** Narrate as you type. It is a separate skill from typing, and it degrades under load unless you have practiced it.

## Keep an interview log

One file. After every interview, within an hour: the questions asked, where you hesitated, what you got wrong, what the interviewer seemed to care about. After three loops this document is more useful than any generic prep list, because it is calibrated to the companies you are actually talking to.

# Further Reading

The sources this course is calibrated against, and where each one is best used.

- **[Notes on the Industry Job Search](https://alisawuffles.github.io/blog/job-search/)** — Alisa Liu's account of a 57-interview, 11-company search out of an NLP PhD. The taxonomy of interview formats used throughout this course comes from here. Read it once at the start, and again in week 7 when the process gets emotionally expensive.
- **[Alisa's book of LLMs](https://alisawuffles.notion.site/alisa-s-book-of-llms)** — the notes she kept while preparing. An excellent map of the territory and a good cross-check against this course's unit structure.
- **[Alisa's math notes](https://alisawuffles.notion.site/math-notes)** — built for a single math interview. Unit 9 covers the same ground.
- **[Stanford CS336: Language Modeling from Scratch](https://stanford-cs336.github.io/)** — the best single source for the breadth these interviews assume. Assignment 1, implementing a transformer and a BPE tokenizer, is the highest-value public homework for this purpose.
- **[NeetCode Blind 75](https://neetcode.io/practice)** — general coding.
- **[How to Scale Your Model](https://jax-ml.github.io/scaling-book/)** — the systems-and-parallelism reference. Unit 5 is a compressed version of it.
- **[The Illustrated GPT-2](https://jalammar.github.io/illustrated-gpt2/)** — worth a pass if the transformer diagram is not yet automatic in your head.

## A note on scope

This course does not cover distributed training operations at production scale, CUDA kernel authoring, or the specifics of any one lab's internal stack. Those come up in senior infrastructure loops and are their own study project.

If you are targeting a performance or kernels role, treat the **Model Optimization Systems** track in this library as the required companion — it goes considerably deeper on quantization, fused kernels, KV-cache serving, speculative decoding, and tensor parallelism than Units 5 and 6 do here.
