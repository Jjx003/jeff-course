# Deck: Scaling and Parallelism

Thirty-two cards on the systems side. This is the material that rapid-fire technical discussions lean on hardest, because it is broad, it is nameable, and it is easy to check whether someone has the reasoning or only the vocabulary.

Two things to watch for while grading yourself:

- **Every parallelism card should be answered with its communication cost.** "Tensor parallelism splits matrices within a layer" is half an answer. "...and costs two all-reduces per layer on both passes, which is why it stays inside a node" is the whole one.
- **Every scaling card should be answered with which cost is being optimized.** Training compute and serving cost give different answers to the same question.
