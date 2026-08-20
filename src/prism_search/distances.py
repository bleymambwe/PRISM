"""Distances for permutations represented as sequences of unique integers."""

from __future__ import annotations

from collections.abc import Callable, Sequence

Distance = Callable[[Sequence[int], Sequence[int]], int]


def _relative_positions(left: Sequence[int], right: Sequence[int]) -> list[int]:
    if len(left) != len(right) or set(left) != set(right) or len(set(left)) != len(left):
        raise ValueError("Inputs must be permutations of the same unique elements")
    right_positions = {value: index for index, value in enumerate(right)}
    return [right_positions[value] for value in left]


def cayley_distance(left: Sequence[int], right: Sequence[int]) -> int:
    """Minimum number of arbitrary swaps needed to transform one ordering."""

    mapping = _relative_positions(left, right)
    visited = [False] * len(mapping)
    cycles = 0
    for start in range(len(mapping)):
        if visited[start]:
            continue
        cycles += 1
        cursor = start
        while not visited[cursor]:
            visited[cursor] = True
            cursor = mapping[cursor]
    return len(mapping) - cycles


def kendall_tau_distance(left: Sequence[int], right: Sequence[int]) -> int:
    """Number of discordant pairs between two orderings."""

    positions = _relative_positions(left, right)
    return sum(
        positions[i] > positions[j]
        for i in range(len(positions))
        for j in range(i + 1, len(positions))
    )


def ulam_distance(left: Sequence[int], right: Sequence[int]) -> int:
    """Minimum insert moves, equal to n minus the longest common subsequence."""

    positions = _relative_positions(left, right)
    tails: list[int] = []
    for value in positions:
        low, high = 0, len(tails)
        while low < high:
            middle = (low + high) // 2
            if tails[middle] < value:
                low = middle + 1
            else:
                high = middle
        if low == len(tails):
            tails.append(value)
        else:
            tails[low] = value
    return len(positions) - len(tails)


DISTANCES: dict[str, Distance] = {
    "cayley": cayley_distance,
    "kendall": kendall_tau_distance,
    "ulam": ulam_distance,
}

OPERATOR_DISTANCE = {
    "swap": "cayley",
    "insert": "ulam",
    "inversion": "kendall",
    "scramble": "cayley",
}
