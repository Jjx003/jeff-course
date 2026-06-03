## Hints

- `arithmetic_intensity` is a one-line division after validating
  `bytes_moved`.
- In `roofline_tflops`, the bandwidth-limited number is
  `bandwidth_tb_s * intensity_flops_per_byte`.
- The HBM sizing helper receives parameter count in **billions**, so multiply by
  `1e9` before converting back to GB.
- The KV-cache helper has a factor of `2` because each layer stores keys and
  values.

## Going deeper

- Add batch size to the KV-cache estimate. Decode serving memory scales with the
  number of simultaneous token streams.
- Compare fp16, fp8, and int4 weight storage. Quantization changes capacity
  pressure before it changes bandwidth pressure.
- Try a larger context length and watch KV cache grow linearly.
