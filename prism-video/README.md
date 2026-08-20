# PRISM Paper Explained

Data-driven Remotion production for the long-form scientific documentary specified by PRISM_Remotion_Kokoro_Production_Brief.md.

The main film preserves the Iteration-18 paper cut. Later Gemma, cross-family, SciML-suite, NAS-Bench, rho-one ablation, MATH-500, and prompt-optimizer results appear only in PRISM-Experiment-Epilogue.

## Setup

Requires Node.js 20+, Python 3.10+, and the packages pinned in requirements-narration.txt.

~~~powershell
npm install
python -m pip install -r requirements-narration.txt
npm run data
~~~

## Kokoro narration

The production uses official Kokoro-82M through KPipeline with American English, the af_heart voice, mono 24 kHz PCM WAV, semantic paragraph chunks, 340 ms between chunks, and 620 ms after each scene.

~~~powershell
npm run narration:audition
npm run narration
npm run audio:qc
~~~

The measured WAV duration controls each Remotion scene. Visual lead is 12 frames and visual tail is 18 frames at 30 fps.

## Preview and validation

~~~powershell
npm run lint
npm run content:validate
npm run dev
~~~

Registered compositions include the 4K and 1080p masters, one per chapter, the experiment epilogue, and three thumbnails.

## Render

~~~powershell
npm run render:thumbnails
npm run render:1080p
npm run render:4k
npm run render:epilogue
npm run render:chapters
~~~

All rendered masters, chapter files, and thumbnail candidates are written under `renders/`.

## Reproducibility outputs

- src/data/film.json: scenes, narration, claims, decisions, sources, and alt descriptions
- src/data/graphExtracts.json: chart-ready data extracted from committed artifacts
- public/data/graph-manifest.json: artifacts, row counts, transforms, axes, and summaries
- src/data/audioManifest.json: measured audio, frame durations, peaks, and captions
- public/data/final-narration.md and JSON: final spoken script
- public/captions: scene JSON, SRT, and WebVTT
- public/data/content-audit.json: scientific completeness audit
- public/data/audio-qc.json: WAV consistency check
- SCIENTIFIC_QA.md: final human sign-off checklist

No experiment curve is invented. If numeric data are unavailable, the visual uses only explicitly reported summary values and is labeled as a summary reconstruction.
