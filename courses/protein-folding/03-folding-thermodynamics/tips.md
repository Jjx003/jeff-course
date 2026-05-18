## Going deeper

- **Anfinsen, "Principles that govern the folding of protein chains"** (Science, 1973) — [https://www.science.org/doi/10.1126/science.181.4096.223](https://www.science.org/doi/10.1126/science.181.4096.223). Original Nobel-lecture-format paper. Surprisingly readable.
- **Dill & MacCallum, "The protein-folding problem, 50 years on"** (Science, 2012). State-of-the-art-as-of-2012 review of folding theory. Good context for *why* AlphaFold2 was such a shock.
- **Dobson, "Protein folding and misfolding"** (Nature, 2003). The classic introduction to the folding funnel.
- **Folding@home** — [https://foldingathome.org/](https://foldingathome.org/). Distributed-computing project that runs MD simulations of protein folding on volunteers' computers. Famous for collaborative work on Alzheimer's and (during COVID) on SARS-CoV-2.

## Mental shortcuts

- **Folded ≠ stable.** A protein can be folded but only marginally so. A
  10 °C temperature rise or a single bad mutation can easily unfold it.
- **Anfinsen's dogma is an approximation that almost always works.** Don't
  worry about the exceptions until you hit one — and when you do, the
  prediction tool's confidence score (pLDDT, etc.) usually catches it.
- **The hydrophobic effect is entropic, not enthalpic.** This trips a lot
  of people up. The favourable energy comes from *water disorder* released
  by burying greasy side chains, not from any direct attraction between
  the side chains themselves.
- **MD and ML predictions answer different questions.** MD: what does this
  protein *do over time*? ML: what is its native shape? Use both, in order.
