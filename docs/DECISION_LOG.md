# PRISM Decision Log

## 2026-07-24 (Iteration 23, Experiment S): D20 Scope Note — Sensitivity Magnitude Not Guaranteed by Headroom Alone

Decision (D26): Experiment S falsified H19 (predicted random-set fitness std
>= 0.15 on the hard MATH-500 pool for a mid-band model; observed 0.078,
statistically indistinguishable from Q2's ceiling-compressed Qwen std of
0.075). The pre-registered interpretation matrix (status doc S11.6) calls
this branch a scope note on D20: order-sensitivity MAGNITUDE is not fully
explained by target-model headroom/ceiling alone -- Q2's "ceiling masking"
hypothesis is at most a partial explanation. D20 (transferable
instruction-order landscapes as the primary publication candidate) is
NOT reversed: H20 (sparse optima, 1.6%) and H23 (position-effect transfer
to hard difficulty, r=0.432) both held, and H22 (the pre-flight forecast)
was CORRECT -- the landscape is real and structured, just with lower raw
sensitivity on this specific model/pool than hypothesized. Candidate
confounds for future work: grading-filter-driven difficulty homogenization
within the hard-question pool (see Iteration 23 write-up), and
model-specific noise (Llama-3.1-8B's baseline accuracy/verbosity) diluting
measurable signal independent of true ordering effects.

Also of note (methodology, not a reversal): the first analysis pass
mis-implemented the H21 guided-race policy (ranked by true fitness instead
of the transfer-derived score -- an oracle, not the guided policy),
producing a false "H21 HOLDS (headline)" reading before any result was
published or committed. Caught before archival; the corrected run shows
guided (32.9 evals) as the best point estimate but not a decisive win over
random (43.6 evals, overlapping CIs) -- consistent with, not contradicting,
Experiment R's "modest support" finding.

## 2026-07-22 (Experiment S review): Benchmark #2 Approved by Bley

Decision (D25): Bley approved Experiment S (Benchmark #2, the MATH-500
high-resolution hard-reasoning ordering landscape) after reviewing the HTML
brief at `deliverables/experiment_s_review.html` (hypotheses H19-H23, design,
race methodology, procedure gates, publication-readiness verdict). Envelope:
a fresh, dedicated $10.00 hard cost cap (the approved worst-case), tracked in
`experiments/iteration-23-experiment-s/results/spend_guard.json`, independent
of the iteration-19 cross-family $9 cap. Prompt-optimizer baselines remain a
SEPARATE, still-unapproved item (~$5-10) -- not authorized by this decision.
Execution: pilot gate -> pre-flight (H22 forecast committed to git before the
main run) -> main landscape -> analysis, per the pre-registered procedure.

## 2026-07-14 (One-Pager): Zero-Cost Program Items Approved by Bley

Decision (D22): Bley approved the three $0 items from
`docs/NEXT_STEPS_ONE_PAGER_2026-07-14.md`: (3) the SciML pipeline-ordering
suite (Benchmark #4, extend Experiment P to 5-8 dynamical systems), (4) the
NAS-Bench search-stage confirmation (Benchmark #5, pre-registered forecasts
on high/low-structure ANASOD slices), and (6) the rho1-vs-alternatives
ablation. The paid items (Benchmark #2 Experiment S at $5-7 and the
prompt-optimizer baselines at $5-10) remain NOT approved and must not incur
spend. Execution order: ablation -> SciML suite -> NAS-Bench confirmation.

## 2026-07-11 (Review): Paper Framing Approved by Bley

Decision (D21): Bley approved decisions 1, 2, 3, and 5 of
`review/RESEARCH_DISCUSSION_BRIEF_RESPONSES_2026-07-11.md`:
(1) PRISM's identity statement — a predictive protocol for permutation
optimization (measure → forecast → select strategy → execute → verify);
the evolutionary searcher is the default executor, not the identity.
(2) The protocol-vs-searcher terminology is adopted throughout paper and
docs; theory claims (elitist absorption, aging record convergence) attach
only to the searcher, never to enumeration studies.
(3) Prompt-optimizer baselines (OPRO/APE, DSPy-MIPROv2, GEPA, GREATER;
PromptBridge for the transfer claim) are a REQUIRED condition of the LLM
paper (~$5-10), including the complementarity experiment (freeze an
optimizer's output, permute its module order).
(5) The rho1-vs-alternatives mini-ablation (free, CPU) is approved.

Still open: review decision 4 (long-term-vision framing option 1 vs 2)
and 6 (SLM candidate pool — resolved by D16 pilots).

## 2026-07-08 (Iteration 18): Primary Candidate Is Transferable Instruction Ordering

Decision (D20): the primary publication-oriented research candidate is now
"transferable instruction-order landscapes," supported by the LLM ordering
landscape, D14 pre-flight diagnostics, Iteration 16 cross-size transfer, and
Iteration 18 transfer-guided evaluation. The transformer-replacement,
KV-cache, activation-routing, feature-visualization, and continual-learning
framings are deferred because current literature is crowded and local evidence
is weak. Evidence: Iteration 18 literature refresh and Experiment R.

Reversal condition: cross-model/SLM transfer fails decisively in Iteration 17
or a higher-resolution harder LLM benchmark shows no budgeted advantage over
random after confidence intervals.

## 2026-07-08 (Iteration 16): FDC Borderline Band

Decision (D19): FDC in (+0.05, +0.3) is a borderline band handled like
the near-zero regime (random sampling as method of record); the hard
"do not use evolutionary search" call is reserved for strongly positive
FDC (the measured 100%-stable deceptive call was at +0.78). Evidence:
Experiment P (FDC +0.109; random 40/40 vs PRISM 38/40 — near-zero
behavior, not deception).

## 2026-07-08 (Iteration 14): Headline Claims Require >=40-Seed CIs

Decision (D18): any result promoted to abstract/headline status must be
backed by >=40 seeds with confidence intervals (or exact enumeration);
15-seed readings are exploratory. Evidence: the It-9 "3x faster"
claim reversed at 40 seeds. Reversal condition: none — methodology
standard.

Last updated: 2026-07-08 (Iteration 18)

## 2026-07-08 (Iteration 12): Encoding-Matched Surrogates Join the Guideline

Decision (D17): when the D14 pre-flight indicates precedence structure
(argmax rho1 = insert), the precedence-pair surrogate is the method of
record — Experiment N shows it dominating all population methods (4x
matched-operator elitist on the single-optimum kendall n=7; random 0/15
there). D15 otherwise unchanged; the elitist+restart hybrid or aging is
the default when no pre-flight is run.

Reversal condition: a calibrated acquisition function or a different
encoding that dominates it on the same protocol.

## 2026-07-08 (Iteration 11): Fitness Resolution Before Search Budget

Decision (D16): for API-priced ordering applications, the variance gate
and pre-flight sample must also establish that the fitness statistic can
DISCRIMINATE (optimum ties not dense at the chosen resolution) before
any search budget is spent. Evidence: Experiment M — 20-question
granularity made perfect orderings dense; all methods saturated at 1.0,
exactly as the sampled pre-flight forecast.

## 2026-07-07 (Iteration 10): Replacement Policy Joins the Pre-Flight Guideline

Decision (D15): the D14 pre-flight now also selects the replacement
policy. FDC materially negative → elitist PRISM (matched operator or
portfolio): fastest, keeps the Theorem-2.2 guarantee. FDC ≈ 0 →
random sampling or aging-PRISM (statistically equivalent there; aging
gives anytime population behavior). Aging evolution is the safe
default when the pre-flight is skipped, because it never underperforms
random — unlike elitist PRISM, which can (Experiment I).

Evidence: Experiment L, 40-seed verification on parity n=7 — aging
78% hit rate vs elitist 48% vs random 75%; elitist fastest on
structured XOR n=6 (18.5 vs 28.7 mean evals).

Trade-off recorded: aging sacrifices strict elitism, so almost-sure
absorption no longer holds as stated (best-ever record retains the
optimum, but the population can lose it).

Reversal condition: a hybrid (elitist + stagnation-triggered aging
restarts) that dominates both — natural Iteration-11 candidate.

## 2026-07-07 (Iteration 8): The Locality Pre-Flight Is Mandatory

Decision (D14): every new PRISM application begins with the locality
diagnostic — sample a few hundred evaluations, compute rho1 per
operator and FDC. Matched operator = argmax rho1 (excluding scramble,
whose rho1 is inflated by identity moves). Proceed with evolutionary
search only if FDC is materially negative; near-zero FDC → report
random sampling as the method of record; positive FDC → do not use
PRISM.

Evidence: Experiment J — the diagnostic reproduces the operator-
matching result 3/3 and all 8 observed search outcomes from pre-search
statistics alone.

Expected impact: replaces expensive trial-and-error search experiments
with a ~cheap measurement; the paper's methodological centerpiece
alongside ground-truth benchmarking.

Reversal condition: an application where the diagnostic's prediction
materially misleads (would itself be a publishable finding).

## 2026-07-07 (Iteration 7): Scale-Aware Hyperparameters + Mandatory Random Baseline

Decision (D12): pop 20 / p_m 0.05 are n≤6 settings. For n≥7 use
pop ≥ 40 and p_m ≥ 0.5 (15/15 exact hits at n=7 vs 4/15 with defaults).
Every search-quality claim must include a random-without-replacement
baseline under the distinct-evaluation metric.

Evidence: Experiment I sensitivity sweep (free, against the cached
5040-permutation landscape).

Reversal condition: a principled adaptive schedule (e.g., p_m scaled to
maintain expected novel-offspring rate) that dominates fixed settings.

## 2026-07-07 (Iteration 7): Locality Before Attribution

Decision (D13): before attributing any application win to PRISM
(starting with the LLM reasoning-chain experiment), measure landscape
locality (fitness correlation of move-adjacent orderings) and compare
to the random baseline. Rationale: Experiment I showed PRISM ≈ random
on a weak-locality neural landscape while beating random by orders of
magnitude on structured synthetic landscapes — the advantage is a
landscape property, and claims must be conditioned on it.

Reversal condition: none; this is a methodology standard.

## 2026-07-07 (Iteration 6): Runtime Secrets from Google Cloud Secret Manager

Decision: API keys (OpenAI TTS, etc.) are fetched at run time via
`gcloud secrets versions access latest --secret=<NAME>` and never
written to the repository, environment files, or logs.

Context: Audio-lesson generation needed the OpenAI API key; the EVE app
already manages keys in Google Cloud Secret Manager.

Evidence: `scripts/generate_audio_lessons.py` retrieves the key inside
the process; nothing key-shaped appears in any committed artifact.

Reversal condition: none anticipated.

## 2026-07-07 (Iteration 6): Notion Tracker Is the Progress View, Repo Is Truth

Decision: The "PRISM Research Tracker" database (on the Comprehensive
Documentation Notion page) is the living progress dashboard — its
formula `Progress` property is the single progress metric, with board /
table / timeline / chart views. The git repository remains the source
of truth for research content; Notion summarizes, never originates.

Context: User requested an up-to-date Notion documentation page and a
formula-driven project tracker with multiple views.

Evidence: Tracker created 2026-07-07 with 21 workstreams spanning
iterations 02-06 and next priorities.

Reversal condition: if Notion and repo state diverge, repo wins and the
tracker is corrected.

## 2026-07-06 (Iteration 5): v4 Is the Canonical Toy Benchmark Design

Decision: The v4 benchmark design — five permuted residual bottleneck
blocks, weight init seeded from the permutation, fitness = mean of k=3
trials — replaces the v2 neural toy benchmarks for all forward work;
v2 results remain in the record for historical comparison only.

Context: R10 documented that v2 fitness was stochastic and used only 3
of 5 permutation positions; the Iteration-3 depth-based redesign (v3)
was falsified.

Evidence: Experiment G — determinism verified by repeat evaluation; all
orderings trainable (no chance-collapse); landscape std 0.098-0.120;
exact enumeration gives ground-truth optima and honest hit rates
(XOR-v4 100%, Parity-v4 40% at 60 generations — headroom to
discriminate search variants).

Expected impact: publication-grade toy results; template for scaling
beyond n=5 (regret vs best-known when enumeration is infeasible).

Reversal condition: none anticipated; extend rather than revert.

## 2026-07-06 (Iteration 4): Uniform Operator Portfolio as Recommended Default

Decision: When the landscape type of an ordering problem is unknown,
PRISM should run with `mutation="portfolio"` (uniform random operator
per mutation event). A fixed matched operator remains best when the
landscape type is known. `mutation="adaptive"` is relegated to
landscape diagnosis (its final weight vector identifies the landscape
type) rather than production search.

Context: Iteration 3 showed mismatched fixed operators hard-fail on
plateau-rich landscapes; requiring users to type their landscape a
priori is error-prone.

Evidence: Experiment F — portfolio solves all three typed landscapes to
n=16 with zero censoring at 1.1-4.1x matched-operator generations;
adaptive learns the correct operator (3/3) but does not consistently
beat uniform and costs one extra evaluation per mutation event.

Expected impact: removes the highest-severity configuration risk (R12)
at a bounded constant-factor cost; strengthens the paper's method
section.

Reversal condition: a credit-assignment scheme that consistently beats
the uniform portfolio (e.g., UCB or windowed rewards) in a future
iteration.

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
