# Semiconductor Pipeline Figure Sources

These local images are generated course diagrams and are served from
`static/courses/semiconductor-pipeline/`.

Use this attribution pattern in course prose or release notes:

> Course diagram generated for `jeff-course`.

| File | Used in | Notes |
|---|---|---|
| `semiconductor-value-chain.png` | Module 01 | Ecosystem map from EDA/IP through fabless design, foundry/IDM manufacturing, packaging, and systems buyers. |
| `fab-process-loop.png` | Module 02 | Simplified wafer fabrication loop: deposition, lithography, etch/implant, CMP, metrology, and back-end flow. |
| `cowos-hbm-stack.png` | Module 06 | Conceptual 2.5D AI accelerator package with compute die, HBM stacks, interposer, package substrate, and board. |
| `ai-accelerator-bom.png` | Module 09 | AI accelerator system bill-of-materials map: package, HBM, networking, power, cooling, board, and rack. |

The diagrams are intentionally conceptual rather than vendor-specific package
cross sections. They are meant to teach bottleneck reasoning and vocabulary, not
to represent exact product dimensions.

## Real-World Photo Sources

| File | Used in | Source / license / attribution |
|---|---|---|
| `silicon-wafer.jpg` | Module 02 | Wikimedia Commons, [File:Silicon wafer.jpg](https://commons.wikimedia.org/wiki/File:Silicon_wafer.jpg). Author: Inductiveload. Public domain / PD-self. Downloaded as a local resized copy. |
| `cleanroom-fab.jpg` | Modules 02 and 04 | Wikimedia Commons, [File:Clean room.jpg](https://commons.wikimedia.org/wiki/File:Clean_room.jpg), sourced from NASA Glenn Research Center image `GRC-1998-C-01261`. Public domain as NASA material. Downloaded as a local resized copy. |
| `nist-wafer-bonder.jpg` | Module 06 | NIST image page, [suss_wafer_bonder.jpg](https://www.nist.gov/image/susswaferbonderjpg). Credit: NIST. NIST public information may be distributed or copied unless marked copyrighted; attribution requested. |
| `nist-random-shaped-chips.jpg` | Module 06 | NIST image page, [Random Shaped Chips](https://www.nist.gov/image/chipsjpg). Credit: NIST. NIST public information may be distributed or copied unless marked copyrighted; attribution requested. |
| `nersc-server-racks.jpg` | Module 09 | Wikimedia Commons, [File:Front of server racks at NERSC.jpg](https://commons.wikimedia.org/wiki/File:Front_of_server_racks_at_NERSC.jpg), originally by Derrick Coetzee on Flickr. CC0 1.0 public domain dedication. Downloaded as a local copy from the source-hosted Flickr image. |

Wikimedia rate-limited direct media downloads during this pass, so the NIST and
Flickr-hosted originals were used where available. No course Markdown hotlinks
external images; all rendered images point to `/courses/semiconductor-pipeline/`.
