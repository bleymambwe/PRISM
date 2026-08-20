# PRISM scientific QA checklist

- [ ] Every scene has a source, claim status, sample size, finding, limitation, downstream decision, and caveat.
- [ ] Experiments A–R are present in the main film.
- [ ] Post-paper studies are separated by the dated epilogue boundary.
- [ ] All 12 paper figures, eight paper tables, and three algorithms are present.
- [ ] Raw artifact values drive available charts; summary reconstructions are labeled.
- [ ] Censored points are marked at the cap and are not treated as measured hitting times.
- [ ] Sampled landscapes leave unobserved permutations blank.
- [ ] The six-module LLM comparison states 9.9 [7, 13] versus 10.8 [8, 14] and retracts the earlier speed claim.
- [ ] The n=7 parity boundary result and failed plain-stack redesign are narrated.
- [ ] Almost-sure convergence is not described as universal fast convergence.
- [ ] Main narration measures 90–120 minutes; epilogue measures 15–25 minutes.
- [ ] Every narration file is mono PCM WAV at 24 kHz with consistent normalization.
- [ ] SRT and WebVTT exports stay within two lines and approximately 42 characters per line.
- [ ] Representative frames and short clips pass 4K and 1080p legibility checks.
- [ ] The complete master is watched once at normal speed and once at 1.5×.

Automated evidence is written to public/data/content-audit.json, public/data/audio-qc.json, and public/data/graph-manifest.json.
