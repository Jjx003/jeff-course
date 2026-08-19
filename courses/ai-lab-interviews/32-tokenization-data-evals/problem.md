# Tokenization, Data, and Evaluation

Three topics that look like plumbing and are not. They are where a surprising number of model behaviours come from, and they are the topics where a candidate with hands-on experience is most obviously distinguishable from one without.

## What gets asked

- Explain BPE. Train one on a small corpus.
- Why can models not count the letters in a word?
- What does vocabulary size trade off?
- Walk me through a pretraining data pipeline.
- How would you detect that your eval set is contaminated?
- Your model scores 85% on a benchmark. How much do you believe it?
- Why is a bigger vocabulary not free?

## Tokenization: the trade

![Two panels. Left: bytes per token against vocabulary size, rising with sharply diminishing returns. Right: embedding plus output-head parameters against vocabulary size for three model dimensions, on a log scale.](/courses/ai-lab-interviews/tokenizer-tradeoff.svg)

A larger vocabulary means **fewer tokens per document** — cheaper training and inference per character of text, and more content inside a fixed context window. It also means **more embedding parameters** and a larger, slower softmax.

Most models land between 32k and 256k, and the trend is upward as models get large enough that the embedding term stops mattering.

## Why this matters more than it looks

Tokenization is the source of a whole class of model behaviours that get blamed on reasoning:

- Character-level tasks fail because the model never sees characters.
- Arithmetic depends on how numbers happen to split.
- Some languages cost 2–4x more tokens than English, which is a real cost and quality asymmetry.
- Rare token sequences produce genuinely strange behavior.

Being able to attribute a failure to tokenization rather than to "the model cannot reason" is a specific, valued diagnostic skill.
