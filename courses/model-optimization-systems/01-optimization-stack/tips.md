# Reading strategy

Do not try to memorize every named optimization in this first module. Build a
sorting habit instead. Whenever you see a technique, place it in one of four
boxes:

| Technique | First question to ask |
|---|---|
| Quantization | Which tensor gets fewer bits? |
| Kernel optimization | Which memory traffic or launch disappears? |
| Serving scheduler | Which request pattern becomes easier? |
| Adapter method | Which trainable weights are avoided? |

That habit will keep the rest of the course from becoming a pile of acronyms.

## Hints for the next module

The roofline estimator intentionally ignores many real-world details. That is
not a flaw. A lower-bound calculation is useful precisely because it tells you
what cannot be beaten even by perfect software.

As you work through the next exercise, check these units carefully:

- decimal GB for weight bandwidth, because hardware bandwidth is usually
  marketed in decimal units;
- GiB for memory capacity, because cache capacity is usually easier to reason
  about with powers of two;
- TFLOP/s to GFLOP/s conversion, because the model's per-token work is printed
  in GFLOP;
- the factor of 2 in KV cache, because each layer stores both keys and values.

## Practical caveats

A rough estimate can still be wrong in direction if you apply it to the wrong
phase. Prefill, decode, training, and evaluation are different workloads. A
benchmark that says "FP8 is 1.8x faster" may be talking about prefill on a
large batch. A product complaint that says "generation feels slow" may be about
small-batch decode latency. Those are not the same claim.

Also be suspicious of quality-free speedups. A quantized model that is faster
but loses the task you care about is not optimized; it is degraded. For protein
models, random train/test splits can hide this problem because related proteins
share family structure. A biological benchmark should ask whether the method
generalizes across families, time, species, or assay conditions.

## Going deeper

When reading optimization papers, write one sentence for each of these:

1. The bottleneck targeted was...
2. The hardware target was...
3. The workload phase was...
4. The quality metric was...
5. The hidden cost was...

If you cannot fill in those sentences, pause before accepting the headline
speedup. The rest of this course is practice filling them in from first
principles.
