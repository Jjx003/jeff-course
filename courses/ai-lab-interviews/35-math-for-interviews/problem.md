# Math for ML Interviews

Not every company has a math interview. If yours does, it is worth a dedicated day, and this module is that day.

The format ranges from logic puzzles to genuine pen-and-paper derivations. Probability dominates by a wide margin; linear algebra and calculus turn up as supporting material, and occasionally as the whole interview.

## The single most useful thing in this module

Probability questions are much easier when you can classify them. Almost every question is a member of a small number of families, and each family has a technique that solves it:

| The question says... | Reach for |
|---|---|
| memoryless, waiting for something | geometric (discrete), exponential (continuous) |
| trials with success and failure | Bernoulli, binomial |
| how many events in a fixed window | Poisson |
| large sample, an average | CLT, approximately Gaussian |
| a bound given only mean and variance | Markov, Chebyshev |
| estimate a parameter from data | MLE, MAP, Bayesian update |
| update a belief from evidence | Bayes' rule |
| a function of a random variable | Jensen's inequality |
| expected count of things | linearity of expectation with indicators |
| expected hitting time, return probability | first-step analysis, solve the recurrence |
| the future depends only on the present | first-step analysis |

Memorize that table. Under pressure, the hardest part of a probability question is knowing which tool applies, and reading the question against this list makes that mechanical.

## The distribution grid

| | Discrete trials | Continuous time |
|---|---|---|
| **Counting** | binomial: how many successes in $n$ trials? | Poisson: how many events in a fixed window? |
| **Waiting** | geometric: how many trials until the first success? | exponential: how long until the first event? |

Four distributions, two questions, two settings. (The columns are about what indexes the process, not what the variable's support is — Poisson counts are discrete, but they arise from events in continuous time.) Almost every basic probability question is one of these four wearing a costume.

## What gets asked

- Expectation and variance of the standard distributions, with derivations.
- Linearity of expectation problems (coupon collector, expected number of fixed points).
- Conditioning and first-step analysis (random walks, gambler's ruin).
- Bayes' rule with a base-rate trap.
- Eigenvalues, rank, positive definiteness.
- Derivatives you should produce cold: sigmoid, softmax, cross-entropy with respect to logits.
- Occasionally: the multivariate Gaussian, or the SVD and what it means.
