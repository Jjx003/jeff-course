# The Linear Layer, Forwards and Backwards

## Forward

A layer with $n_{in}$ inputs and $n_{out}$ neurons, applied to a batch of $m$ examples arranged as rows:

$$Z = XW + b$$

with $X \in \mathbb{R}^{m \times n_{in}}$, $W \in \mathbb{R}^{n_{in} \times n_{out}}$, $b \in \mathbb{R}^{n_{out}}$ broadcast across rows, and $Z \in \mathbb{R}^{m \times n_{out}}$.

**The PyTorch wrinkle, which interviewers do ask about.** `nn.Linear` stores its weight as $(n_{out}, n_{in})$, not $(n_{in}, n_{out})$, and computes `x @ W.T`. The transpose is free — it only changes the stride, not the storage. The reason for the layout is that the gradient $\partial L / \partial W$ then comes out naturally shaped $(n_{out}, n_{in})$, matching the parameter, with no extra transpose in the hot path.

## Backward

Given the upstream gradient $\partial L / \partial Z \in \mathbb{R}^{m \times n_{out}}$:

$$\frac{\partial L}{\partial X} = \frac{\partial L}{\partial Z} W^{\top} \qquad (m, n_{out}) \times (n_{out}, n_{in}) = (m, n_{in})$$

$$\frac{\partial L}{\partial W} = X^{\top} \frac{\partial L}{\partial Z} \qquad (n_{in}, m) \times (m, n_{out}) = (n_{in}, n_{out})$$

$$\frac{\partial L}{\partial b} = \sum_{i=1}^{m} \frac{\partial L}{\partial Z_{i,:}}$$

Notice the pattern. $X$ is not shared across the batch, so the batch dimension survives — a stack. $W$ is shared, so the batch dimension is contracted away by the matmul — a sum. $b$ is shared and has no other index, so it is a plain sum over rows. That is Rule 2, in equations.

**How to derive this live without memorizing it.** Derive the Jacobian for a single example, where everything is clean and two-dimensional. Then ask, for each tensor, whether it is shared across the batch. Shared means contract; unshared means stack. You can reconstruct all three formulas in under a minute this way, which is what you want when an interviewer changes the setup on you.

# Activation Functions

## The ones you need to be able to differentiate cold

$$\sigma(x) = \frac{1}{1+e^{-x}}, \qquad \sigma'(x) = \sigma(x)(1 - \sigma(x))$$

$$\tanh(x) = 2\sigma(2x) - 1, \qquad \tanh'(x) = 1 - \tanh^2(x)$$

$$\mathrm{ReLU}(x) = \max(x, 0), \qquad \mathrm{ReLU}'(x) = \mathbb{1}[x > 0]$$

$$\mathrm{Swish}(x) = x \cdot \sigma(x), \qquad \mathrm{Swish}'(x) = \sigma(x) + \mathrm{Swish}(x)(1 - \sigma(x))$$

## Why sigmoid died in hidden layers

Two reasons, and interviewers want both.

**Vanishing gradients.** $\sigma'(x) \le 0.25$ everywhere. Stack ten sigmoid layers and the gradient reaching the first one has been multiplied by at most $0.25^{10} \approx 10^{-6}$. Training stalls.

**Not zero-centered.** $\sigma(x) \in (0,1)$, so all inputs to the next layer are positive. For a single neuron, every weight in a row then receives a gradient with the same sign, determined entirely by the upstream gradient. Updates zigzag rather than moving diagonally.

`tanh` fixes the centering — its derivative peaks at 1 — but still saturates and still shrinks gradients, since $\tanh'(z) \in (0, 1]$.

## Dying ReLU

If a neuron's pre-activation becomes negative for *every* input in the data distribution, its gradient is zero forever and it can never recover. A meaningful fraction of a network can go dead this way, usually after a too-large learning rate step. Leaky ReLU, $\alpha x$ for $x \le 0$, exists to keep a trickle of gradient flowing.

## GLU and SwiGLU

A gated linear unit uses one projection for content and a second for a multiplicative gate:

$$\mathrm{GLU}(x) = (xW_1) \odot \sigma(xW_2)$$

SwiGLU swaps the sigmoid gate for Swish:

$$\mathrm{SwiGLU}(x) = (xW_1) \odot \mathrm{Swish}(xW_2)$$

This is the FFN nonlinearity in essentially every modern open-weight LM. **The interview follow-up you should expect:** SwiGLU needs three weight matrices instead of two, so to hold the parameter count fixed against a standard `4d` FFN, implementations shrink the hidden dimension to roughly $\tfrac{8}{3}d$. Knowing that specific detail signals you have actually read an implementation rather than a summary.

## Why nonlinearities at all

Without them, a stack of linear layers collapses: $W_1 W_2 x = Wx$. Depth buys nothing. With them, the network becomes a universal approximator, and depth buys expressivity exponentially cheaper than width.

# Softmax and Cross-Entropy

The single most-asked derivation in this area. Let $z \in \mathbb{R}^V$ be logits, $p = \mathrm{softmax}(z)$, and $t$ the correct class, with $L = -\log p_t$.

The softmax Jacobian:

$$\frac{\partial p_j}{\partial z_i} = \begin{cases} p_j(1 - p_j) & i = j \\ -p_j p_i & i \ne j\end{cases}$$

The loss gradient is nonzero only at $t$: $\partial L / \partial p_t = -1/p_t$. Composing, for the true token:

$$\frac{\partial L}{\partial z_t} = -\frac{1}{p_t} \cdot p_t(1 - p_t) = p_t - 1$$

and for every other token:

$$\frac{\partial L}{\partial z_i} = -\frac{1}{p_t}\cdot(-p_t p_i) = p_i$$

Which collapses to one of the cleanest results in machine learning:

$$\frac{\partial L}{\partial z} = p - \mathrm{onehot}(t)$$

**Why this matters practically.** Because the composed gradient is this simple, frameworks fuse softmax and cross-entropy into a single op. `F.cross_entropy` takes *logits*, not probabilities. Passing it softmax output is a classic interview trap and a classic real bug: you get a double softmax, a much flatter distribution, and a model that trains but badly.

# Backpropagation

## The algorithm

1. Run the forward pass, caching every intermediate the backward pass will need.
2. Seed the output gradient with $\partial L / \partial L = 1$.
3. Visit nodes in reverse topological order. At each node: downstream gradient = upstream gradient times local gradient.
4. Where a tensor was used by more than one consumer, sum the incoming gradients.

Done correctly, forward and backward have the same big-$O$ cost. In practice backward is about twice the FLOPs of forward, because each layer computes two gradient matmuls (one for the input, one for the parameters) against the forward pass's one.

## Node intuitions worth stating out loud

- **Add** distributes the upstream gradient unchanged to each summand.
- **Max** routes the entire gradient to the argmax and zero elsewhere.
- **Multiply** swaps the forward coefficients: the gradient to $a$ is upstream times $b$.
- **Branching sums.** If $y$ feeds both $a$ and $b$, then $\partial L/\partial y$ is the sum of both paths. Forgetting this is the most common hand-written-backprop bug, and it is exactly why weight tying between the embedding and the output head needs care.

## Why backward needs a scalar

`backward()` computes $\partial L/\partial \theta$ for every parameter — one number per parameter. That only makes sense when $L$ is a scalar; for a vector output you would need a full Jacobian. PyTorch seeds a scalar backward with $\partial L/\partial L = 1$ implicitly, which is why `loss.backward()` works but `logits.backward()` demands an explicit `gradient=` argument.

A related fact worth having ready: with mean reduction, $L = \frac{1}{N}\sum_i \ell_i$, linearity gives

$$\frac{\partial L}{\partial \theta} = \frac{1}{N}\sum_{i=1}^{N} \frac{\partial \ell_i}{\partial \theta}$$

so the gradient of the mean loss is exactly the mean of the per-example gradients. This is the justification for gradient accumulation being mathematically equivalent to a larger batch — provided you divide correctly, which is the bug people actually ship.

## Activation memory and checkpointing

The backward pass needs forward-pass intermediates, so a standard training step stores all of them. That is why training memory dwarfs inference memory even at the same batch size.

**Gradient checkpointing** trades compute for memory: store only a subset of activations, and recompute the rest on the fly from the nearest checkpoint. For $N$ layers split into $K$ segments:

- memory: $O(N) \to O(K + N/K)$
- backward compute: $O(N) \to O(N + N(K-1)/K)$

Optimizing over $K$ gives $K = \sqrt{N}$: memory $O(\sqrt{N})$ for roughly $1.33\times$ the total training compute. Being able to produce the $\sqrt{N}$ result and the rough overhead figure is a strong signal in a systems-flavored discussion.

## Gradient checking

For each parameter, compare the analytic gradient to a central finite difference:

$$f'(x) \approx \frac{f(x+h) - f(x-h)}{2h}$$

Use the *central* difference, not the forward one — its error is $O(h^2)$ rather than $O(h)$. Use `float64`. Pick $h$ around $10^{-5}$: too large and truncation error dominates, too small and floating-point cancellation does. Compare with relative error, not absolute.

This is the technique the next module makes you use, and it is the correct answer to "how would you know your hand-written backward pass is right?"

# Autograd

Autograd builds the computation graph as the forward pass runs (define-by-run). Each op knows how to compute its output and how to convert an output gradient into input gradients. The framework handles the topological ordering and the accumulation.

Details that come up:

- **Gradients accumulate.** `.grad` is added to, not overwritten, which is why `optimizer.zero_grad()` exists and why forgetting it produces the classic "loss goes strange after a few steps" bug.
- **Leaf tensors** are the ones you created, typically parameters. Only leaves keep `.grad` by default; intermediate activation gradients are computed, used, and discarded.
- **`detach()` vs `no_grad()`.** `detach()` cuts one tensor out of the graph; `torch.no_grad()` disables graph construction entirely for a block. Use `no_grad` for evaluation and generation; use `detach` for a stop-gradient inside a loss, such as the reference-model term in DPO or the target in a distillation objective.
- **In-place ops** can corrupt values autograd cached for backward. When PyTorch raises "a variable needed for gradient computation has been modified by an inplace operation", this is what happened.
