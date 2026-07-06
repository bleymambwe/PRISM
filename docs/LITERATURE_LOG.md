# PRISM Literature and Source Review Log

Last updated: 2026-07-05

This file records literature, references, and source documents that have been
reviewed or cited by project materials. Entries should distinguish direct paper
review from inherited notes or secondary summaries.

## Inherited Source Notes

### NEAT, Innovation Numbers, and Speciation

Source: `other.md`

Status: Inherited analysis, not independently revalidated during the 2026-07-05
continuity setup.

Key finding recorded in existing notes: Innovation numbers are mentioned in the
GNGN material but are not fully specified. Branch IDs may act as implicit
branch-level innovation numbers, but within-branch gene innovation tracking and
NEAT-style crossover remain underspecified.

Research impact: This is a major design issue if PRISM/GNGN is extended from
fixed branch permutation search toward topology evolution.

Follow-up:

- Verify the source papers and exact NEAT compatibility-distance formulation.
- Decide whether innovation tracking belongs in the next PRISM algorithm
  version or only in a GNGN/topology-evolution extension.
- Formalize the relationship between permutation-level distance and
  topology-level distance.

### Presentation and Visualization Guidance

Source: `presentation.md`

Status: Inherited presentation guide.

Key content: Beamer/LaTeX setup, color palette, math presentation guidance,
TikZ/network diagrams, and slide structure for a GNGN/NEAT audience.

Research impact: Useful for dissemination, but not itself evidence for
algorithmic correctness.

## Future Literature Entry Format

Use this structure for each paper or source:

- Citation:
- Link or local path:
- Reviewed by:
- Date reviewed:
- Research question:
- Key claims:
- Methods relevant to PRISM:
- Evidence quality:
- Limitations:
- How it changes project direction:
