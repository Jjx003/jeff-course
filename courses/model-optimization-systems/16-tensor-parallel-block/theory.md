# Theory notes: what the simulation abstracts away

## Why the certificate works

The exact-arithmetic test rests on three facts worth stating precisely.

1. **Integer closure.** IEEE-754 float64 represents every integer with
   magnitude below $2^{53}$ exactly, and addition/multiplication of exactly
   represented integers whose true results stay below $2^{53}$ round to the
   true result (no rounding occurs at all). The starter's magnitudes are
   bounded by $1024 \times 4096 \times 4 \approx 1.7 \times 10^7$, with six
   orders of magnitude of headroom.
2. **ReLU preserves the domain.** $\max(0, n)$ maps integers to integers, so
   exactness survives the nonlinearity. GELU would not — $\text{gelu}(3)$ is
   irrational — which is why the certificate swaps activations. The certificate
   therefore proves the *sharding* exact, and combined with "GELU is a
   deterministic function applied to identical inputs," the fp32 path's
   residual is pinned on the one place the two paths differ: the order of the
   final summation.
3. **`torch.equal` is unforgiving.** On exact integers, any wrong chunk
   boundary, transposed shard, or dropped partial produces an integer-sized
   discrepancy that no tolerance can absorb.

The general lesson transfers beyond TP: when a refactor is supposed to be
algebraically neutral, testing it on a domain where arithmetic is exact turns
"close enough" into "equal," and that is a much stronger statement than any
epsilon.

## The fp32 residual, quantified

In fp32, the reference computes each output element as one long dot product
over 1024 terms; the TP path computes four dot products over 256 terms and
adds the four results. Both are correctly rounded per operation, but the
rounding points differ. The standard error model for summing $n$ terms gives a
relative error bound of $O(n \cdot u)$ with unit roundoff
$u = 2^{-24} \approx 6 \times 10^{-8}$, and pairwise regrouping typically
*improves* accuracy — the TP result is often closer to the float64 truth than
the reference is. The `1e-5` tolerance is therefore generous by two orders of
magnitude, and the point of Part 3 is that you never had to reason about any
of this to know the cut was correct.

## What NCCL adds that the list of tensors does not

The simulation's `all_reduce` is synchronous, ordered, and free. Real
collectives differ in ways that matter operationally but not algebraically:

- **Overlap.** Production TP kernels overlap the all-reduce with the next
  matmul's early work or fuse it into the GEMM epilogue; the 10 µs the table
  charges per collective is partly hideable at prefill, barely at decode.
- **Determinism.** NCCL ring reductions are deterministic for a fixed
  topology and chunk schedule, but changing TP degree, NCCL version, or
  algorithm (ring to tree) changes summation order and therefore the low bits.
  Two "identical" deployments at TP 4 and TP 8 produce different logits at the
  rounding level — module 12's batch-invariance lesson, now caused by the
  fabric. Greedy decode can visibly diverge after enough tokens; the fix, as
  there, is to compare distributions and tolerances, not token strings.
- **Failure modes.** A rank that misses a collective deadlocks the group;
  real stacks wrap collectives in watchdogs. The ledger's `assert len(partials)
  == tp` is the toy version of that watchdog.

## Sharding the KV cache, concretely

This lab runs a single cacheless forward pass, but the head-sharded attention
implies the cache layout: rank $r$ stores K/V only for its own KV heads, so
module 12's paged pool exists once per rank at $1/p$ size, and block tables
are replicated (they are indices, not tensors). Two consequences:

- Cache capacity scales with $\min(p, H_{kv})$ — the GQA ceiling from the
  reading — because past that point ranks hold copies of the same heads.
- Prefix-cache hits must agree across ranks. The hash-to-block mapping is
  computed from token IDs, which every rank sees identically, so agreement is
  automatic — unless an engine salts cache keys per rank, which is the kind of
  bug the module-12 equivalence test would catch immediately.

## Choosing the parallelism, a decision table

For a model of total weight bytes $M$, per-GPU memory $C$, intra-node
bandwidth/latency $(\beta_\text{nv}, \alpha_\text{nv})$ and inter-node
$(\beta_\text{ib}, \alpha_\text{ib})$:

| Question | If yes | If no |
|---|---|---|
| Does $M$ + peak cache fit on one GPU? | TP 1; replicate for throughput | keep going |
| Does it fit in one node at TP $\le H_{kv}$? | TP within the node | add PP across nodes |
| Is inter-token latency the binding SLO? | prefer TP (and quantization) over PP | PP is fine; buy bubble-filling concurrency |
| Is the model MoE with $E/k \gg$ achievable batch? | EP across the fleet, all-to-all budget | treat experts as dense TP shards |

Quantization enters the first row, which is why the course taught it first: a
4× byte reduction can delete an entire tier of this table, and INT4-on-one-GPU
versus BF16-at-TP-8 is a real cost-quality-latency triangle, not a strictly
ordered choice.
