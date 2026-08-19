# Debugging Guide

**Relative error is around 1.0 for one parameter.** That gradient is wrong in a structural way — usually a transpose or a missing term. Check the shape first: if it needed a transpose to even assemble, you assembled it wrong.

**Relative error is around `1e-3` for everything.** You are in float32, or `h` is badly chosen. Central differences in float64 with `h = 1e-5` should reach `1e-9` or better on a small model.

**Relative error is fine but the loss will not go down.** Look for a sign error in the update (`-=` versus `+=`), or a learning rate three orders of magnitude off.

**Autograd disagrees but finite differences agree.** A convention mismatch, not a math error. Common causes: `nn.Linear` stores weights transposed, so a numpy `W` of shape `(D, H)` corresponds to `linear.weight` of shape `(H, D)`; and `F.cross_entropy` defaults to mean reduction, not sum.

**Everything is `nan`.** You exponentiated unshifted logits, or took `log` of a zero probability. Use the max-subtracted softmax and the log-sum-exp loss.

# Formula for relative error

$$\mathrm{relerr}(a, b) = \frac{|a - b|}{\max(|a| + |b|,\ \varepsilon)}$$

Plain absolute difference is wrong here: a gradient of magnitude `1e4` and one of magnitude `1e-4` cannot be judged by the same absolute threshold.

# What to say in the room

When you finish the implementation, do not wait to be asked how you would test it. Say:

> "I would check this against central finite differences in float64 — that catches an actual math error — and separately against autograd, which catches convention mismatches like the `nn.Linear` weight layout. Finite differences alone are `O(P)` forward passes, so on a real model you would only do it on a small slice."

That answer is often worth more than the implementation.

# Further Reading

- [CS231n gradient-check notes](https://cs231n.github.io/neural-networks-3/) — including the kink problem: ReLU at exactly zero makes finite differences unreliable, which is why the starter perturbs away from the boundary.
- [micrograd](https://github.com/karpathy/micrograd) — a hundred-line autograd engine. Reading it end to end is a good use of an evening.
