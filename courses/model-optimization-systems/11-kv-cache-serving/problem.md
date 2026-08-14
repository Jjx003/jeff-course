# KV-cache serving systems

During autoregressive decoding, every generated token attends to the tokens that came before it. Recomputing all previous keys and values at every step would be wasteful, so inference engines store them in a KV cache.

The cache is both the reason LLM serving works and one of the main reasons it is hard:

- useful because it avoids recomputing old keys and values,
- expensive because it grows with context length, layers, KV heads, and concurrency,
- awkward because requests have different prompt lengths and finish at different times.

This module is about the data structures and policies around that cache. Once attention kernels are efficient, the next serving bottleneck is often not the matrix multiply itself but the system that keeps the right K/V blocks resident, compact, reusable, and schedulable.

## The basic cache

For each layer, the model stores keys and values for previous tokens. On the next decode step, the new query attends over all cached keys and reads the corresponding values. The memory for one request is:

$$
\text{bytes} =
L_\text{layers}
\times H_\text{kv}
\times D_\text{head}
\times 2
\times T
\times B_\text{dtype}
$$

The factor of 2 is for K and V. $T$ is the number of cached tokens. With batch size $N$, multiply by $N$ unless prefixes or cache blocks are shared.

This linear growth is easy to underestimate. A model with many layers and a long context window can use more memory for KV cache than for quantized weights, especially under concurrent traffic.

## Why contiguous allocation fails

Imagine a server that gives every request one contiguous KV region sized for its maximum possible length. It sounds simple, but real traffic is not simple:

- one user sends a 200-token prompt,
- another sends 20,000 retrieved tokens,
- one request stops after 12 generated tokens,
- another streams for 1,000 tokens,
- some are cancelled,
- some share a system prompt,
- some use parallel sampling or tool schemas.

Static contiguous reservations waste memory and fragment the remaining space. Worse, they force the scheduler to be conservative because admitting a request requires enough contiguous space for its worst case, not just enough blocks for its current tokens.

## PagedAttention

PagedAttention, popularized by vLLM, borrows the idea of paging from operating systems. Instead of requiring one contiguous physical allocation per request, the KV cache is split into fixed-size blocks. A request sees a logical sequence of blocks, while the physical blocks may live wherever the allocator has space.

```mermaid
flowchart LR
    req["request logical tokens"] --> table["block table"]
    table --> b1["KV block 17"]
    table --> b2["KV block 4"]
    table --> b3["KV block 91"]
    table --> b4["KV block 23"]
```

This improves memory utilization because the server can allocate blocks as a sequence grows and free blocks as a sequence finishes. It also makes prefix sharing natural: two requests can point to the same immutable prefix blocks and diverge only after their prompts differ.

The tradeoff is that attention kernels and scheduler logic must understand block tables. That is an engineering cost, but it bought enough throughput and utilization that paged KV cache became a standard idea in LLM serving.

## Prefix reuse

Many production requests share prefixes:

- a system prompt,
- retrieved context boilerplate,
- tool or function schemas,
- policy text,
- a document template,
- an instruction scaffold for a specific workflow.

Prefix caching stores KV blocks for those repeated prefixes. If a later request has the same prefix under the same model state, the server can reuse the cached blocks and skip some prefill work. This is exact reuse when the tokens, model weights, positional treatment, and relevant cache metadata match.

The invalidation rules matter. A small prompt difference, tokenizer change, adapter change, or cache-salting policy can make reuse unsafe. Some serving stacks expose controls to prevent accidentally sharing cache entries across tenants or security boundaries.

## Virtualized cache alternatives

PagedAttention changes the attention implementation to gather from paged blocks. Another line of work asks whether the system can keep the KV cache virtually contiguous while relying on virtual memory mechanisms underneath to avoid physical fragmentation. vAttention is a representative example: preserve a contiguous virtual address view for kernels while managing physical memory dynamically.

The theme is the same even when the mechanism differs:

1. Requests need a logical sequence of K/V states.
2. Physical GPU memory is scarce and fragmented.
3. The serving engine needs dynamic allocation without destroying kernel performance.

## KV-cache compression

Cache compression asks whether all old keys and values need full precision or full length. Approaches include:

- low-bit KV quantization,
- retaining only important tokens,
- product-quantization-style compression,
- sliding windows with sink tokens,
- learned or training-free cache compression,
- layer-specific or head-specific retention policies.

Compression can be exact only in special lossless cases. Usually it is approximate, so evaluation must include long-context tasks where cache quality matters: retrieval, code, math, multi-document QA, and scientific workflows. A method that looks fine on short chat may fail when a single far-back token is decisive.

## Recap

For long-context LLM serving, the KV cache is often the system. Kernels decide how fast attention can read it; allocators decide how many requests fit; schedulers decide which requests get tokens next. The next coding lab builds all three against real tensors: a paged KV cache, a continuous-batching scheduler that admits and retires requests mid-flight, and real attention decode steps that read from the cache. The payoff is a correctness test — proving that a request batched alongside others produces the same output it would have produced alone, which is exactly the property that cache-indexing bugs silently break.
