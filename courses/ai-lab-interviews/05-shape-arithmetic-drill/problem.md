# Drill: Shapes and Gradient Arithmetic

In an ML coding interview you will be asked, mid-implementation, what shape something is. The right answer is instant. A pause while you mentally trace the tensor through three ops reads as uncertainty about the architecture, even when it is only uncertainty about arithmetic.

This drill makes that arithmetic automatic. Twenty prompts, 150 seconds, 85% to clear it. Type numbers only — the unit suffix is shown for you, and byte units are decimal (1 MB = $10^6$ bytes).

## What it covers

- Broadcasting rules
- Parameter counts for linear layers and MLP blocks
- Element counts for attention score matrices — the tensor that makes long context expensive
- Head splitting: model dimension into heads
- Matmul FLOPs, using the $2mkn$ convention
- Gradient tensor sizes

## The conventions used here

- **A matmul of $(m,k)$ by $(k,n)$ costs $2mkn$ FLOPs.** One multiply and one add per output element per inner step. Some people quote $mkn$ MACs instead; if an interviewer's number is half yours, that is why. Say which convention you are using and it never becomes a problem.
- **A linear layer $(d_{in} \to d_{out})$ has $d_{in}d_{out} + d_{out}$ parameters** — the bias is the second term. Modern LMs usually omit biases, and then it is just $d_{in}d_{out}$.
- **A gradient has exactly the same shape as its tensor.** Every gradient-size question here is really a parameter-size question.

Run it until you clear it twice. Then come back in a week.
