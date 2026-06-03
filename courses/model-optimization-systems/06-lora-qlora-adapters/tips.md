# Practical hints

Use LoRA when you need task adaptation without touching every base weight. Use
QLoRA when base-model memory dominates your fine-tuning setup.

The basic decision table is:

| Need | Likely choice |
|---|---|
| one fixed task, lowest latency | merge the adapter |
| many tasks sharing one base | dynamic adapter serving |
| limited fine-tuning memory | QLoRA |
| fragile quantized quality | consider LoftQ-style initialization or higher precision |
| biology task with small labels | adapter plus careful family-aware validation |

## Things to tune

- **Rank `r`:** higher rank increases capacity and memory.
- **Target modules:** attention-only is cheaper; attention plus MLP is more
  expressive.
- **Alpha:** controls update scale.
- **Dropout:** can regularize small datasets.
- **Base precision:** affects memory and the numerical environment the adapter
  learns against.
- **Merge policy:** affects serving latency, storage, and batching.

## Common mistakes

- Comparing LoRA and full fine-tuning without matching data and evaluation.
- Forgetting that optimizer state, activations, and gradients matter during
  training, not only weight storage.
- Training an adapter on one quantized base and deploying it on a differently
  quantized or merged base without rechecking quality.
- Assuming adapters from different tasks compose cleanly.
- Evaluating protein adapters on random splits that leak close homologs.

## Going deeper

- LoRA paper: https://arxiv.org/abs/2106.09685
- QLoRA paper: https://arxiv.org/abs/2305.14314
- Hugging Face PEFT LoRA docs: https://huggingface.co/docs/peft/developer_guides/lora
- Protein language model efficiency paper: https://www.sciencedirect.com/science/article/pii/S2589004225017560

Next, the course moves from model weights and adapters toward kernels. Keep the
same question in mind: what bottleneck is the technique actually attacking?
