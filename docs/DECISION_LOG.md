# PRISM Decision Log

Last updated: 2026-07-06

## 2026-07-06: Apply PRISM to RL Through Ordering Surfaces

Decision: Treat PRISM-RL as a wrapper pattern where the genome is an ordering of
RL options, curriculum tasks, or modules, and the fitness function is an
episodic-return or learning-performance evaluator.

Context: The user asked whether PRISM's core principles - ordering, tournament
selection, swap mutation, elitism, and theoretical finite-state convergence
work - can be applied to reinforcement work.

Alternatives considered:

- Implement a full RL algorithm from scratch.
- Depend on a Gym/Gymnasium benchmark suite.
- Keep the PRISM algorithm unchanged and build lightweight RL evaluators around
  it.

Rationale: The third option tests the framework claim directly while preserving
PRISM's theoretical surface: finite permutations, mutation with nonzero
probability, tournament selection, and elitism.

Evidence: The PRISM-RL lightweight run found exact or near-exact orderings on a
grid option-ordering semi-MDP and a tabular Q-learning curriculum benchmark.

Follow-up: Scale to less toy RL surfaces, such as MiniGrid-style option
ordering, curriculum ordering across multiple small control tasks, or module
ordering in a reasoning/action pipeline.

## 2026-07-06 (Iteration 3): Operator Study Over LLM Application

Decision: Spend Iteration 3 on mutation-operator/landscape matching and
extended scaling rather than the LLM reasoning-chain application.

Context: The Iteration-2 handover listed benchmark redesign, LLM
application, and extended scaling as priorities. `other.md` contains a
directly testable literature prediction (operator-landscape matching,
Cicirello 2022) that plugs into the existing hitting-time framework.

Alternatives considered: LLM reasoning-chain optimization (deferred —
needs an API budget decision and eval-set selection); CIFAR-10 supernet
(infeasible locally, no GPU).

Evidence: Iteration-2 scaling framework is in place and cheap to extend;
operator study runs locally in about an hour.

Expected impact: If confirmed, operator selection guidance becomes part
of the PRISM method and strengthens the paper's experimental section.

Reversal condition: If operator effects are negligible, drop the
`mutation=` parameter surface and revert to fixed swap.

## 2026-07-06 (Iteration 3): Versioning via Git Tags, Not Copied Folders

Decision: Preserve previous algorithm versions with git commits/tags
(`iteration-02` tag) and strictly backward-compatible code changes
(new `mutation=` parameter defaults to `"swap"`), rather than copying
version folders.

Context: User requires previous versions be kept for comparison.

Evidence: Default-parameter runs reproduce Iteration-2 hitting
generations bit-for-bit under the same seeds (verified on 4 spot
checks before starting Experiment C).

Expected impact: `git diff iteration-02..iteration-03` shows exactly
what changed; old outputs remain untouched in `prism-research/outputs/`
while Iteration-3 outputs live in `experiments/iteration-03/results/`.

Reversal condition: If backward compatibility ever has to break, copy
the old module into `prism-research/legacy/` first.

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
