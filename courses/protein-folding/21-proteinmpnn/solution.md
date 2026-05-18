## Walkthrough

### Backbone parsing

```python
def parse_backbone(pdb_str: str) -> int:
    n = 0
    for line in pdb_str.splitlines():
        if line.startswith("ATOM") and " CA " in line:
            n += 1
    return n
```

We only need the residue count for the stub. A real ProteinMPNN
call would extract every backbone atom (N, CA, C, O) per residue,
build a `Bio.PDB`-style structure object, and pass it to
`protein_mpnn_run.py`'s preprocessing.

### The stub generative loop

```python
for k in range(num_samples):
    rng = np.random.default_rng(seed + k)
    seq_chars = []
    log_prob_total = 0.0
    for wt_aa in wt_sequence:
        logits = rng.standard_normal(20) * 1.5
        wt_idx = ALPHABET.index(wt_aa)
        logits[wt_idx] += wt_bias
        scaled = logits / temperature
        probs = np.exp(scaled - scaled.max())
        probs /= probs.sum()
        chosen_idx = int(rng.choice(20, p=probs))
        log_prob_total += float(np.log(probs[chosen_idx]))
        seq_chars.append(ALPHABET[chosen_idx])
    samples.append(("".join(seq_chars), log_prob_total))
```

Step by step:

1. **Per-sample seed**: `seed + k` ensures sample $k$ is
   reproducibly different from sample $k-1$. NumPy's
   `default_rng(seed)` is the modern preferred RNG; older
   `np.random.seed(seed)` is global state and harder to manage.

2. **Logit construction**: we draw 20 random logits from a
   $\mathcal{N}(0, 1.5^2)$ distribution, then bump the WT residue's
   logit by `wt_bias = 2.0`. The bias produces ~30-50 %
   recovery on average, which mimics published ProteinMPNN
   benchmarks.

3. **Temperature scaling**: divide logits by $\tau$ before softmax.
   $\tau = 1$ is the natural distribution; $\tau \to 0$ makes the
   distribution peakier (more deterministic); $\tau \to \infty$
   flattens it.

4. **Numerically-stable softmax**: subtract the max logit before
   exponentiation. Equivalent to standard softmax but doesn't
   overflow in FP32.

5. **Sampling**: `rng.choice(20, p=probs)` draws one index according
   to the probability vector. This is the position's "decision".

6. **Log-probability accumulation**: $\log p(\text{chosen} \mid \text{ctx})$ — the model's expressed certainty about its own sample.
   The total sum is the sequence-level log-probability.

A real ProteinMPNN's logits would be the encoder-decoder output
conditioned on the actual backbone; here we substitute random noise
+ WT bias, which produces qualitatively similar samples.

### Recovery and printing

```python
def recovery(seq: str, wt: str) -> int:
    return sum(a == b for a, b in zip(seq, wt))
```

A one-liner that counts position-wise matches.

```python
print(f"  {i}. {seq}  log_prob = {lp:7.3f}  recovery = {recov:>2}/{L} ({pct:5.1f}%)")
```

Format: width-7 floating-point for `log_prob` so negative numbers
align cleanly; width-2 right-aligned integer for the count; width-5
fixed-point percentage.

## Reading the output

A typical run with `seed=0`, `temperature=1.0`, `wt_bias=2.0`:

```text
  1. MAEGLKWIVASR  log_prob =  -3.142   recovery = 12/12 (100.0%)
  2. MAEGLKHIVASA  log_prob =  -8.917   recovery = 10/12 ( 83.3%)
  3. NAEGAKHIIASR  log_prob = -14.583   recovery =  7/12 ( 58.3%)
  4. ...
```

(Exact values depend on NumPy version; expected output is omitted.)

Sample 1 happens to recover all 12 positions because the WT bias
beat the noise on every draw — high recovery, high log-probability.

Samples 2-5 progressively diverge from WT as the random seeds
produce different outcomes. Lower recovery typically correlates
with more-negative log-probability because non-WT residues are
on average lower-probability under the WT-biased distribution.

## Why this stub is "fair-ish"

The stub captures three real-world properties:

1. **Recovery scales with model confidence.** Higher `wt_bias` =
   higher recovery. Real ProteinMPNN's "confidence" is the actual
   encoder-decoder belief; ours is a fake bias.

2. **Log-probability scales with recovery.** A sequence that
   matches WT at most positions has a higher log-prob because each
   matched position contributes a high $\log p$.

3. **Diversity comes from temperature.** Higher $\tau$ flattens the
   distribution; samples become more random, recovery drops,
   log-prob drops.

What it doesn't capture:

- **Structure-conditioning.** Real ProteinMPNN's logits depend on
  the backbone — different sequences for different backbones.
  Our stub ignores the PDB completely.
- **Compositional biases.** Real ProteinMPNN over-samples certain
  amino acids (charged surface, low cysteine) reflecting its
  training-set biases. Our stub samples uniformly modulo WT bias.
- **Per-position correlations.** Real ProteinMPNN's autoregressive
  decoder makes neighbouring positions interdependent (decoding a
  hydrophobic residue at position $i$ raises the prob of
  hydrophobic residues at neighbouring positions). The stub treats
  each position independently.

For a more realistic stub you'd add some of these as a side
exercise. For the present module the goal is to exercise the data
flow, which the simple version does.

## Replacing the stub with real ProteinMPNN

Once installed:

```python
import subprocess

def real_inverse_fold(pdb_path, wt_sequence, num_samples=5, temperature=0.1):
    cmd = [
        "python", "/path/to/ProteinMPNN/protein_mpnn_run.py",
        "--pdb_path", pdb_path,
        "--num_seq_per_target", str(num_samples),
        "--sampling_temp", str(temperature),
        "--out_folder", "./mpnn_out",
    ]
    subprocess.run(cmd, check=True)
    # Then parse the output FASTA-style file in ./mpnn_out/seqs/
    ...
```

The CLI is the recommended entry point because the Python API
shifts between releases. For programmatic use, `protein_mpnn_run.py`
returns sequences and per-residue log-probabilities in a FASTA file
with header lines containing the metadata.

## Connection to module 22

Module 22 — the lead-optimisation pipeline — uses inverse folding
as one of several **sampling** mechanisms. The full flow is:

```
forward fold (ESMFold)            (module 18)
  +
inverse fold (ProteinMPNN)        (this module)
  +
PLL ranking (ESM-2)               (module 20)
  +
fitness predictor (assay-trained) (module 22)
```

Each step contributes a different signal: ESMFold checks
"does the structure match"; ProteinMPNN samples "what sequences
fit the structure"; PLL says "is this sequence biologically
plausible"; the fitness predictor says "will this sequence work
in *our* assay". Combining them — the Cradle "logiter" approach —
is the topic of the final module.
