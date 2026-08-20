"""Permutation mutation operators used by PRISM."""

from __future__ import annotations

from collections.abc import Callable, MutableSequence, Sequence
from typing import TypeAlias

from numpy.random import Generator

Permutation: TypeAlias = Sequence[int]
MutablePermutation: TypeAlias = MutableSequence[int]
MutationOperator: TypeAlias = Callable[[MutablePermutation, Generator], None]


def _require_mutable_permutation(permutation: MutablePermutation) -> None:
    if len(permutation) < 2:
        raise ValueError("A mutation requires a permutation with at least two elements")
    if len(set(permutation)) != len(permutation):
        raise ValueError("Permutation elements must be unique")


def swap(permutation: MutablePermutation, rng: Generator) -> None:
    """Swap two positions in place."""

    _require_mutable_permutation(permutation)
    i, j = rng.choice(len(permutation), 2, replace=False)
    permutation[int(i)], permutation[int(j)] = permutation[int(j)], permutation[int(i)]


def insert(permutation: MutablePermutation, rng: Generator) -> None:
    """Remove one element and insert it at a different position in place."""

    _require_mutable_permutation(permutation)
    i, j = (int(value) for value in rng.choice(len(permutation), 2, replace=False))
    element = permutation.pop(i)
    permutation.insert(j, element)


def inversion(permutation: MutablePermutation, rng: Generator) -> None:
    """Reverse one contiguous segment in place."""

    _require_mutable_permutation(permutation)
    i, j = sorted(int(value) for value in rng.choice(len(permutation), 2, replace=False))
    permutation[i : j + 1] = permutation[i : j + 1][::-1]


def scramble(permutation: MutablePermutation, rng: Generator) -> None:
    """Randomly shuffle one contiguous segment in place."""

    _require_mutable_permutation(permutation)
    i, j = sorted(int(value) for value in rng.choice(len(permutation), 2, replace=False))
    segment = list(permutation[i : j + 1])
    rng.shuffle(segment)
    permutation[i : j + 1] = segment


MUTATION_OPERATORS: dict[str, MutationOperator] = {
    "swap": swap,
    "insert": insert,
    "inversion": inversion,
    "scramble": scramble,
}
