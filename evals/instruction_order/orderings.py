"""Ordering sets that define the conditions of the benchmark.

Three designs, in increasing order of cost:

``random``
    Independent uniform orderings. Cheap, unbiased, and what the published
    random-set statistics in arXiv:2608.08344 were computed on.
``diverse``
    A greedy maximin design under a PRISM operator-aligned distance, so a small
    budget still covers the space rather than clustering. Use when you can
    afford few orderings and want the range statistic to mean something.
``exhaustive``
    Every permutation. Only defensible at n=6 (720 orderings); refuses above
    that rather than quietly costing a fortune.

The distances come from `prism_search`, which is what makes the geometry here
match the geometry the diagnostics in the paper were computed under - Cayley
for arbitrary swaps, Ulam for insert/precedence moves, Kendall for pair order.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from itertools import permutations
from typing import Literal

import numpy as np

from prism_search import cayley_distance, kendall_tau_distance, ulam_distance

Ordering = tuple[int, ...]
Design = Literal["random", "diverse", "exhaustive"]

#: Operator name -> the distance that is aligned to it. Mirrors the alignment
#: rule in the PRISM paper; using a mismatched pair is the documented way to
#: get a meaningless fitness-distance correlation.
DISTANCES: dict[str, Callable[[Sequence[int], Sequence[int]], int]] = {
    "swap": cayley_distance,
    "insert": ulam_distance,
    "precedence": kendall_tau_distance,
}

#: Above this, `exhaustive` is refused. 7! = 5,040 orderings x 32 questions is
#: already 161k model calls, which is not something to trigger by accident.
MAX_EXHAUSTIVE_N = 6


def exhaustive(n: int) -> list[Ordering]:
    """Every permutation of ``range(n)``, in lexicographic order."""
    if n > MAX_EXHAUSTIVE_N:
        raise ValueError(
            f"exhaustive enumeration refused for n={n}: {math.factorial(n):,} orderings. "
            f"Use design='random' or 'diverse' above n={MAX_EXHAUSTIVE_N}."
        )
    return [tuple(p) for p in permutations(range(n))]


def random_orderings(n: int, count: int, seed: int) -> list[Ordering]:
    """`count` distinct uniform orderings, seeded and reproducible."""
    _check_count(n, count)
    rng = np.random.default_rng(seed)
    seen: dict[Ordering, None] = {}
    # Distinct-by-construction: duplicates would silently reduce the number of
    # conditions and inflate the apparent agreement between them.
    while len(seen) < count:
        seen[tuple(int(x) for x in rng.permutation(n))] = None
    return list(seen)


def diverse_orderings(
    n: int, count: int, seed: int, operator: str = "swap", pool_factor: int = 40
) -> list[Ordering]:
    """Greedy maximin subset under the operator-aligned PRISM distance.

    Draws a candidate pool, seeds it with one ordering, then repeatedly adds
    whichever candidate is furthest from everything chosen so far.
    """
    _check_count(n, count)
    if operator not in DISTANCES:
        raise ValueError(f"unknown operator {operator!r}; expected one of {sorted(DISTANCES)}")
    distance = DISTANCES[operator]

    pool_size = min(math.factorial(n), max(count * pool_factor, count))
    pool = random_orderings(n, pool_size, seed)
    chosen = [pool[0]]
    remaining = pool[1:]
    while len(chosen) < count and remaining:
        best_index, best_score = 0, -1
        for index, candidate in enumerate(remaining):
            score = min(distance(candidate, picked) for picked in chosen)
            if score > best_score:
                best_index, best_score = index, score
        chosen.append(remaining.pop(best_index))
    return chosen


def build_orderings(
    n: int,
    *,
    design: Design = "random",
    count: int = 50,
    seed: int = 7,
    operator: str = "swap",
) -> list[Ordering]:
    """Dispatch to the requested design."""
    if design == "exhaustive":
        return exhaustive(n)
    if design == "random":
        return random_orderings(n, count, seed)
    if design == "diverse":
        return diverse_orderings(n, count, seed, operator)
    raise ValueError(f"unknown design {design!r}; expected random, diverse or exhaustive")


def _check_count(n: int, count: int) -> None:
    if count < 2:
        raise ValueError(f"count must be at least 2 to measure a spread, got {count}")
    total = math.factorial(n)
    if count > total:
        raise ValueError(f"asked for {count} distinct orderings but only {total} exist for n={n}")
