# Iteration 19: ANASOD--PRISM Boundary Test

## Question

Can PRISM diagnose when the ANASOD operation-distribution abstraction is
sufficient and when exact edge placement retains exploitable structure?
This is a boundary test, not an attempt to falsify ANASOD globally.

## Design

NAS-Bench-201 contains six fixed edges and five operation choices, hence
15,625 cells partitioned into 210 operation-count distributions. For every
dataset and distribution, `anasod_boundary.py` exhaustively computes the
within-distribution standard deviation/range, swap-neighborhood rho1, and
exact fitness-distance correlation (FDC) to the nearest tied optimum. It also
reports eta-squared: the fraction of total architecture-level variance
explained by distribution membership.

The Figure-1 ANASOD example (four 3x3 convolutions and two 1x1 convolutions)
contains only `6!/(4!2!) = 15` unique placements. It is reported as a case
study, but conclusions are based on all 210 distributions rather than that
small slice alone.

## Inputs and commands

Preferred compact CSV schema: `arch,cifar10-valid,cifar100,ImageNet16-120`.
At least one score column is required. Architecture strings use the canonical
NAS-Bench-201 representation.

```powershell
python experiments/iteration-19/anasod_boundary.py --csv PATH.csv
```

The reproducible compact backend used for the reported run stores the
three repeated last-epoch validation accuracies and is installed from PyPI:

```powershell
pip install simple-hpo-bench==0.2.0
python experiments/iteration-19/anasod_boundary.py --simple-hpo
```

The official archive is also supported (requires `pip install nas-bench-201`):

```powershell
python experiments/iteration-19/anasod_boundary.py --pth NAS-Bench-201-v1_1-096897.pth
```

Pipeline-only smoke test (synthetic scores; never cite as evidence):

```powershell
python experiments/iteration-19/anasod_boundary.py --make-fixture experiments/iteration-19/fixture.csv
python experiments/iteration-19/anasod_boundary.py --csv experiments/iteration-19/fixture.csv --outdir experiments/iteration-19/fixture-results
```

## Decision rule

- High eta-squared plus small slice ranges and near-zero rho/FDC supports
  ANASOD's distribution abstraction and tells PRISM not to search placement.
- Material slice ranges with positive swap locality and negative FDC identify
  distributions where placement-aware search is potentially useful.
- Mixed slices support the conditional thesis: distribution is a strong
  coarse encoding, while PRISM diagnoses exceptions.

No universal numerical threshold is fixed after seeing NB201. Effect sizes,
bootstrap uncertainty (future extension), and search-vs-random confirmation on
pre-registered high/low-structure slices should determine the final claim.

## Result and limitation

The exhaustive run is complete using `simple-hpo-bench==0.2.0`, whose compact
tables expose three repeated last-epoch validation accuracies per architecture.
Operation distribution explains 46.1%, 55.6%, and 61.2% of architecture-level
variance on CIFAR-10, CIFAR-100, and ImageNet16-120, respectively. The remaining
within-distribution fractions are 53.9%, 44.4%, and 38.8%. Thus distribution is
strongly informative but is not a sufficient statistic for these tables.

For the 4xconv3x3+2xconv1x1 case, placement ranges are 0.848, 2.530, and
4.956 accuracy points. Swap rho1 is 0.137, -0.143, and 0.223; exact FDC is
-0.412, -0.273, and -0.721. This is mixed: placement effects grow across the
harder datasets, but swap locality is weak except on ImageNet16-120. It supports
the boundary thesis, not a blanket claim that PRISM search always helps.

Raw outputs are in `results/summary.json` and `results/slice_metrics.csv`.
The backend is a compact redistribution based on NATS-Bench and reports only
last-epoch results; an official-archive replication remains desirable.
Synthetic fixture output is software validation only.
