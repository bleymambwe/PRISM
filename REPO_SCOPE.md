# Repository scope — what is public, what stays private

PRISM is split across two repositories. This one is the **artifact repository**: the code and
reproducibility artifacts the paper points to. A separate **private workspace** holds everything
that supports the work but is not part of the published record.

The rule is one sentence: **if a reader needs it to check a claim in the paper, it is public;
if it only helped produce the work, it is private.**

## Public — this repository

| Kept | Why |
| --- | --- |
| `experiments/**` | Pre-registered plans, hypotheses, runner code and results. This is what "reproducibility artifacts" means. |
| `docs/` research record | Experiment log, decision log, literature log, risk register, audit report. A reader checking a claim needs the trail. |
| `scripts/**` | Code that generates the figures, reports and dashboards. |
| `deliverables/book_figures/**` | Figures, which are outputs of the published scripts. |
| `deliverables/PRISM_Framework_Research_Paper.md` | Long-form framework write-up in source form. |
| `GNGN_Toy_Problems.ipynb` | Early validation notebook. |

## Private — the workspace repository

| Excluded | Why |
| --- | --- |
| `deliverables/audio/**` (~83 MB of MP3s and narration scripts) | A personal study aid, not a reproducibility artifact. It was 86% of the repository size and nothing in the paper depends on it. The generator, `scripts/generate_audio_lessons.py`, **is** public — the code is the artifact, the audio is the output. |
| `Approximate Neural Architecture Search via Operation Distribution Learning.pdf` | A third-party paper. Redistributing someone else's PDF is a copyright question with no upside; cite it instead. |
| Draft PDFs — `main.pdf`, `PRISM Algorithm.pdf`, `Prism Comphersive Algorithm.pdf`, `prism vt.pdf`, `PRISM_Book*.pdf` | Superseded drafts. Publishing several divergent versions of the paper alongside the arXiv version invites the question of which one is authoritative. arXiv is authoritative. |
| Slide decks and briefings — `*.pptx`, `PRISM_TEAM_BRIEFING.txt`, presentation `.tex` | Presentation material, not evidence. |
| Working notes — `research.md`, `research-v2.md`, `other.md`, `instructions.md`, `presentation.md`, `skills.md` | Drafting scaffolding. Some of it contradicts the final paper, which is normal for notes and unhelpful in public. |
| Assistant working directories — `codex review/`, `codex experment opportunities/`, `codex prism benchmark reccomendation/`, `claude prism benchmark recomendation/`, `review/` | Tool-assisted working notes. Not artifacts. |
| Planning docs — `PUBLICATION_PLAN.md`, `PUBLICATION_GUIDE_*.md`, `ICML_READINESS_AUDIT.md`, `NEXT_STEPS_ONE_PAGER_*.md`, `HANDOVER.md`, `CONTINUITY_PROTOCOL.md`, `RESEARCH_STATUS_COMPREHENSIVE_*.md`, `RECENT_DEVELOPMENTS_*.md`, `BENCHMARK_DISCOVERY_*.md` | Venue strategy and project management. Private by choice, not by necessity. |
| `research-opportunity-mapping-*/`, `prism-research/`, `iterations/` | Exploratory mapping and superseded iteration notes. |

## How the split is enforced

The private paths were removed from **the entire git history**, not just the current commit, so
they are not recoverable from this repository's objects. `.gitignore` blocks the same paths from
being reintroduced. Before adding anything to this repository, apply the rule above; if it is a
study aid, a draft, a deck, or someone else's copyrighted file, it belongs in the workspace.

## Note on `docs/ARTIFACT_INDEX.md`

That index was written to describe the full workspace and therefore lists files that are private
and not present here. It is kept because it documents the project's structure, but its rows about
root drafts, `.tex` sources, and historical PDFs refer to the private workspace.
