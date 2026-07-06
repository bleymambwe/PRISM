# PRISM Decision Log

Last updated: 2026-07-06

## 2026-07-06: Initialize Git Repository at Project Root

Decision: Initialize a Git repository at the PRISM workspace root on branch
`main` and commit the visible project artifacts.

Context: The workspace had no `.git` directory at the root or in subdirectories.
The user requested a git repository with artifacts pushed to git.

Alternatives considered:

- Initialize Git inside `prism-research/` only.
- Initialize Git at the workspace root.

Evidence: Important artifacts are spread across the root, `docs/`,
`iterations/`, and `prism-research/`. A root repository preserves the complete
research context.

Rationale: A root repository best satisfies the requirement that all research
artifacts be tracked together.

Follow-up: Add a remote and push to it if no usable remote is configured after
the initial commit.

## 2026-07-06: Exclude Local Agent Settings and Cache Files

Decision: Add `.gitignore` and exclude `.claude/settings.local.json`, Python
bytecode caches, Jupyter checkpoints, LaTeX build byproducts, and OS/editor
noise.

Context: `.claude/settings.local.json` contains local tool permission state and
absolute machine-specific paths. Python `__pycache__` files were present under
`prism-research/`.

Rationale: These are not research artifacts and would reduce repository
portability.

Follow-up: If a future collaborator needs shared tool settings, add a sanitized
template rather than committing local state.

## 2026-07-05: Add Continuity Documentation Layer

Decision: Implement `instructions.md` as an additive documentation structure
with a workspace README, protocol, logs, artifact index, iteration note, and
current handover.

Context: The workspace contained substantial research documents and generated
artifacts, but no explicit continuity workflow, no current handover file, and no
version-control metadata in the working directory.

Alternatives considered:

- Move historical files into new directories immediately.
- Create a minimal single handover document only.
- Add a structured but lightweight documentation layer while leaving historical
  files in place.

Evidence: Existing documents reference root-level files and contain enough
research state to index them. `instructions.md` asks for continuous,
first-class documentation rather than end-only summaries.

Rationale: Additive documentation improves continuity without risking broken
references or accidental loss of context.

Follow-up: A later cleanup iteration may reorganize root artifacts after all
references are audited and updated.

## 2026-07-05: Treat PRISM as Workspace Umbrella While Preserving GNGN Context

Decision: Use PRISM as the workspace-level research name, while retaining GNGN
terminology where existing files use it.

Context: `research.md` describes PRISM, while `other.md`,
`GNGN_Toy_Problems.ipynb`, and `presentation.md` contain GNGN/NEAT terminology.

Rationale: Renaming concepts without a dedicated conceptual cleanup could
obscure historical provenance.

Follow-up: Clarify whether GNGN is an earlier name, a related framework, or a
subcomponent of PRISM.

## 2026-07-05: Keep Historical Root Files In Place

Decision: Do not move the existing notebook, PDFs, TeX sources, images, or
Markdown notes during continuity setup.

Context: The current task is to implement documentation continuity. Moving files
would require auditing all references in the existing documents and PDFs.

Rationale: Indexing gives immediate continuity with lower risk.

Follow-up: Consider a dedicated reorganization pass after reproduction scripts
or citations depend on stable paths.
