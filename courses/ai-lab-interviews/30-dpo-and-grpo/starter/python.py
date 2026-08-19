"""
The DPO and GRPO losses, implemented from their paper descriptions and checked
against the properties they are supposed to have.

"Implement this loss from the paper" is a standard ML coding prompt, and these
two are the current favourites.

Graded output goes to stdout in float64 with seed 0. Diagnostics go to stderr.

Fill in the four TODO blocks. None is more than five lines.
"""

import sys

import torch
import torch.nn.functional as F

SEED = 0
BATCH = 4
SEQ = 12
VOCAB = 32
GROUP = 8
BETA = 0.1
CLIP_EPS = 0.2
TIGHT = 1e-9


def sequence_logprob(logits, labels, mask=None):
    """Sum of per-token log-probabilities for the given labels.

    logits: (B, S, V) already aligned with labels (no shift applied here).
    mask:   (B, S) of 1.0 for real tokens, 0.0 for padding or prompt tokens.

    TODO 1: log-softmax the logits, gather the log-probability of each label,
    zero out anything the mask excludes, and sum over the sequence.

    In a real implementation the mask excludes prompt tokens as well as
    padding - training on prompt tokens optimizes the model's likelihood of
    the instruction, which is not the job.
    """
    raise NotImplementedError


def dpo_loss(policy_chosen_logps, policy_rejected_logps,
             ref_chosen_logps, ref_rejected_logps, beta=BETA):
    """Direct Preference Optimization.

    Returns (loss, chosen_reward, rejected_reward). The implicit rewards are
    beta * log(policy / reference), which is what the DPO derivation says the
    reward must be for a KL-regularized optimum.

    TODO 2:
      chosen_reward   = beta * (policy_chosen  - ref_chosen)
      rejected_reward = beta * (policy_rejected - ref_rejected)
      loss = -logsigmoid(chosen_reward - rejected_reward), meaned

    Use F.logsigmoid, not log(sigmoid(x)) - the fused version is stable for
    large negative arguments where the naive form logs an underflowed zero.

    Sanity check before you run anything else: with policy == reference this
    must give exactly ln(2) = 0.6931.
    """
    raise NotImplementedError


def grpo_advantages(rewards, eps=1e-8):
    """Group-relative advantages: the group's own statistics as the baseline.

    rewards: (n_prompts, group_size). Returns the same shape.

    TODO 3: normalize each row by its own mean and standard deviation.

    Within each prompt's group, not across the whole batch. With binary
    verifiable rewards the group mean is the pass rate for that prompt, so an
    advantage is how a response did relative to the problem's difficulty.
    """
    raise NotImplementedError


def grpo_loss(policy_logps, old_logps, advantages, ref_logps=None,
              beta=0.0, clip_eps=CLIP_EPS):
    """GRPO's clipped surrogate with an optional KL penalty to the reference.

    All log-prob tensors are (n_prompts, group_size), one entry per sampled
    response. Returns a scalar to MINIMIZE, so the surrogate is negated.

    TODO 4:
      ratio     = exp(policy_logps - old_logps)
      surrogate = mean(min(ratio * A, clamp(ratio, 1-eps, 1+eps) * A))
      kl        = mean(exp(r) - r - 1)  with r = ref_logps - policy_logps
      return   -(surrogate - beta * kl)

    Two things to get right. The min makes this a pessimistic bound: it caps
    the gain at 1+eps for a positive advantage and caps the penalty at 1-eps
    for a negative one, so no single sample drags the policy far from the one
    that generated the rollouts.

    And the sign: the surrogate is MAXIMIZED, so the returned loss negates it.
    Getting that backwards trains confidently in the wrong direction.

    Use the k3 KL estimator exp(r) - r - 1, not the naive -r. The naive one is
    unbiased but high-variance and can come out negative on a finite sample,
    which would push the policy AWAY from the reference.
    """
    raise NotImplementedError


def main():
    torch.manual_seed(SEED)
    torch.set_default_dtype(torch.float64)

    print("=== DPO and GRPO ===")
    print(f"beta {BETA}  clip eps {CLIP_EPS}  group size {GROUP}  dtype float64")

    print()
    print("--- 1. sequence log-probabilities ---")
    logits = torch.randn(BATCH, SEQ, VOCAB)
    labels = torch.randint(0, VOCAB, (BATCH, SEQ))
    total = sequence_logprob(logits, labels)
    print(f"shape: {tuple(total.shape)}  (one scalar per sequence)")
    print(f"all log-probs are negative: {bool((total < 0).all())}")

    mask = torch.ones(BATCH, SEQ)
    mask[:, : SEQ // 2] = 0.0
    masked = sequence_logprob(logits, labels, mask)
    print(f"masking the prompt half raises the sum: {bool((masked > total).all())}")
    print("(masking the prompt is mandatory in SFT and preference training -")
    print(" otherwise you train the model to generate instructions)")

    print()
    print("--- 2. DPO ---")
    ref_chosen = torch.tensor([-10.0, -12.0, -8.0, -15.0])
    ref_rejected = torch.tensor([-11.0, -11.0, -9.0, -14.0])

    identical = dpo_loss(ref_chosen, ref_rejected, ref_chosen, ref_rejected)[0]
    print(f"policy == reference gives loss ln(2) = {float(identical):.6f}")
    print(f"matches -log(0.5): {abs(float(identical) - 0.6931471805599453) < TIGHT}")
    print("(at initialization the implicit rewards are equal, so the model is")
    print(" exactly indifferent between chosen and rejected)")

    better = dpo_loss(ref_chosen + 1.0, ref_rejected - 1.0, ref_chosen, ref_rejected)[0]
    worse = dpo_loss(ref_chosen - 1.0, ref_rejected + 1.0, ref_chosen, ref_rejected)[0]
    print(f"loss when the policy prefers the chosen response: {float(better):.6f}")
    print(f"loss when the policy prefers the rejected one: {float(worse):.6f}")
    print(f"preferring the chosen response lowers the loss: {better < identical < worse}")

    shift = 5.0
    shifted = dpo_loss(ref_chosen + shift, ref_rejected + shift, ref_chosen, ref_rejected)[0]
    print(f"loss is unchanged by a constant shift to both log-probs: "
          f"{abs(float(shifted) - float(identical)) < TIGHT}")
    print("(only the reward DIFFERENCE enters the loss - the same fact that")
    print(" makes the partition function cancel in the derivation)")

    _, cr, rr = dpo_loss(ref_chosen + 2.0, ref_rejected, ref_chosen, ref_rejected)
    print(f"implicit reward = beta * log(policy/reference): {float(cr[0]):.4f} for a +2.0 log-prob gap")
    print(f"equals beta * 2.0: {abs(float(cr[0]) - BETA * 2.0) < TIGHT}")
    print(f"unchanged responses have zero implicit reward: {bool((rr.abs() < TIGHT).all())}")

    print()
    print("--- 3. DPO gradient direction ---")
    policy_c = (ref_chosen.clone() + 0.5).requires_grad_(True)
    policy_r = (ref_rejected.clone() + 0.5).requires_grad_(True)
    loss, _, _ = dpo_loss(policy_c, policy_r, ref_chosen, ref_rejected)
    loss.backward()
    print(f"gradient pushes the chosen log-prob UP: {bool((policy_c.grad < 0).all())}")
    print(f"gradient pushes the rejected log-prob DOWN: {bool((policy_r.grad > 0).all())}")
    print(f"magnitudes are equal and opposite: "
          f"{bool(torch.allclose(policy_c.grad, -policy_r.grad, atol=TIGHT))}")
    print("(equal and opposite means the loss constrains only the GAP - nothing")
    print(" anchors the absolute values, which is how both log-probs can drift")
    print(" down together in real DPO runs while the loss improves)")

    print()
    print("--- 4. GRPO advantages ---")
    rewards = torch.tensor([[1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0, 0.0]])
    adv = grpo_advantages(rewards)
    print(f"binary rewards: {rewards.tolist()[0]}")
    print(f"advantages: {[round(a, 4) for a in adv.tolist()[0]]}")
    print(f"advantages are zero-mean: {abs(float(adv.mean())) < 1e-8}")
    print(f"correct responses get positive advantage: {bool((adv[rewards > 0] > 0).all())}")
    print(f"incorrect responses get negative advantage: {bool((adv[rewards == 0] < 0).all())}")
    print(f"pass rate for this prompt: {float(rewards.mean()):.3f}")

    uniform = torch.ones(1, GROUP)
    uniform_adv = grpo_advantages(uniform)
    print(f"a group where every response scores the same gives zero advantage: "
          f"{bool((uniform_adv.abs() < 1e-6).all())}")
    print("(so a prompt that is uniformly too easy or too hard contributes no")
    print(" gradient at all - which is why prompt curriculum matters in GRPO)")

    print()
    print("--- 5. GRPO clipped surrogate ---")
    # Deliberately not unit magnitude: with all |A| = 1, clipping the ratio
    # and clipping the whole surrogate product give identical numbers, so a
    # student who clips the wrong quantity would slip through.
    advantages = torch.tensor([[2.0, -1.0, 1.0, -2.0]])
    old = torch.zeros(1, 4)

    on_policy = grpo_loss(old.clone(), old, advantages)
    print(f"loss when the policy has not moved: {float(on_policy):.6f}")
    print(f"equals -mean(advantage) = 0 for a zero-mean group: {abs(float(on_policy)) < TIGHT}")

    # A large positive move on a positive-advantage sample must be clipped.
    moved = torch.tensor([[2.0, 0.0, 0.0, 0.0]])
    clipped_loss = grpo_loss(moved, old, advantages)
    unclipped_ratio = float(torch.exp(moved - old)[0, 0])
    print(f"ratio for the moved sample: {unclipped_ratio:.4f} (clip bound {1 + CLIP_EPS})")
    # If the loss clips correctly, sample 0 contributes (1+eps)*A, not ratio*A.
    expected_clipped = -((1 + CLIP_EPS) * 2.0 + (-1.0) + 1.0 + (-2.0)) / 4
    clip_ok = abs(float(clipped_loss) - expected_clipped) < TIGHT
    print(f"loss with the move clipped: {float(clipped_loss):.6f}  (expected {expected_clipped:.6f})")
    print(f"the sample's gain is capped at 1 + eps: {clip_ok}")

    # The same move on a NEGATIVE-advantage sample must NOT be clipped: min
    # keeps the full, unbounded penalty. That asymmetry is deliberate, and it
    # is the gap Dual-Clip PPO later bounded.
    moved_neg = torch.tensor([[0.0, 2.0, 0.0, 0.0]])
    neg_loss = grpo_loss(moved_neg, old, advantages)
    expected_neg = -(2.0 + unclipped_ratio * (-1.0) + 1.0 + (-2.0)) / 4
    one_sided_ok = abs(float(neg_loss) - expected_neg) < TIGHT
    print(f"raising the ratio on a negative advantage is NOT clipped: {one_sided_ok}")
    print(f"  (the penalty keeps growing with the ratio: loss {float(neg_loss):.6f})")

    print()
    print("--- 6. the KL estimator ---")
    policy = torch.randn(1, 64) * 0.1
    ref_same = policy.clone()
    zero_kl = grpo_loss(policy, policy, torch.zeros(1, 64), ref_logps=ref_same, beta=1.0)
    print(f"KL is exactly 0 when policy == reference: {abs(float(zero_kl)) < TIGHT}")

    ref_far = policy + 0.5
    far_kl = grpo_loss(policy, policy, torch.zeros(1, 64), ref_logps=ref_far, beta=1.0)
    print(f"KL is positive when they differ: {float(far_kl) > 0}")
    print(f"  estimated KL: {float(far_kl):.6f}", file=sys.stderr)

    ref_below = policy - 0.5
    below_kl = grpo_loss(policy, policy, torch.zeros(1, 64), ref_logps=ref_below, beta=1.0)
    print(f"KL is positive in both directions: {float(below_kl) > 0}")
    print("(the k3 estimator exp(r) - r - 1 is unbiased and never negative,")
    print(" unlike the naive log-ratio estimator, which can go below zero)")

    print()
    all_ok = (
        bool((total < 0).all())
        and bool((masked > total).all())
        and abs(float(identical) - 0.6931471805599453) < TIGHT
        and better < identical < worse
        and abs(float(shifted) - float(identical)) < TIGHT
        and abs(float(cr[0]) - BETA * 2.0) < TIGHT
        and bool((rr.abs() < TIGHT).all())
        and bool((policy_c.grad < 0).all())
        and bool((policy_r.grad > 0).all())
        and bool(torch.allclose(policy_c.grad, -policy_r.grad, atol=TIGHT))
        and abs(float(adv.mean())) < 1e-8
        and bool((adv[rewards > 0] > 0).all())
        and bool((adv[rewards == 0] < 0).all())
        and bool((uniform_adv.abs() < 1e-6).all())
        and abs(float(on_policy)) < TIGHT
        and clip_ok
        and one_sided_ok
        and abs(float(zero_kl)) < TIGHT
        and float(far_kl) > 0
        and float(below_kl) > 0
    )
    print(f"ALL CHECKS PASS: {all_ok}")


if __name__ == "__main__":
    main()
