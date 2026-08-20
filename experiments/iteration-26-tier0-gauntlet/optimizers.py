"""Optimizer suite replayed against enumerated landscapes (Tier 0, E0.1).

Every method is charged by *distinct evaluated permutations*.  Repeats are
served from the oracle's cache and cost nothing, which is the accounting
convention used throughout the PRISM study.  Uniform sampling without
replacement is the reference method and receives exactly the same budget.

``prism_protocol`` is the honest end-to-end entry: it spends part of its budget
on the pre-flight probe, is charged for it, and only then runs whichever
executor the protocol selected.  Comparing that against uniform sampling at
equal *total* budget is the comparison a sceptical reviewer actually wants.

Progress guarantee
------------------
Because revisits are free, a method that converges onto an already-exhausted
neighbourhood can propose forever without ever spending budget.  Every
stochastic method therefore tracks consecutive non-charging proposals and
restarts from a fresh permutation once it stalls -- which is what a competent
implementation does anyway, and keeps the comparison fair rather than letting
a method hang.  ``Oracle`` also raises ``Stalled`` as a hard safety net.
"""

from __future__ import annotations

import itertools
import sys
from collections.abc import Callable, Sequence

import numpy as np

sys.path.insert(0, "src")

from prism_search.diagnostics import preflight  # noqa: E402
from prism_search.operators import MUTATION_OPERATORS  # noqa: E402


class BudgetExhausted(Exception):
    """Raised when a method asks for one distinct evaluation too many."""


class Stalled(BudgetExhausted):
    """Raised when a method stops proposing anything new (safety net)."""


class Oracle:
    """Charges distinct evaluations against a fixed budget.

    Records the best-so-far curve and the distinct-evaluation index at which a
    true global optimum was first evaluated.  Because the landscapes are fully
    enumerated, ``hit`` is exact rather than a best-observed proxy.
    """

    def __init__(
        self,
        table: dict[tuple[int, ...], float],
        optima: frozenset,
        budget: int,
        stall_limit: int = 20000,
    ):
        self.table = table
        self.optima = optima
        self.budget = budget
        self.stall_limit = stall_limit
        self.seen: set[tuple[int, ...]] = set()
        self.curve: list[float] = []
        self.hit: int | None = None
        self.best: float = -np.inf
        self.repeats = 0
        self._since_progress = 0

    @property
    def count(self) -> int:
        return len(self.seen)

    def is_new(self, perm: Sequence[int]) -> bool:
        return tuple(int(x) for x in perm) not in self.seen

    def __call__(self, perm: Sequence[int]) -> float:
        key = tuple(int(x) for x in perm)
        value = self.table[key]
        if key in self.seen:
            self.repeats += 1
            self._since_progress += 1
            if self._since_progress > self.stall_limit:
                raise Stalled
            return value
        if self.count >= self.budget:
            raise BudgetExhausted
        self._since_progress = 0
        self.seen.add(key)
        if value > self.best:
            self.best = value
        if self.hit is None and key in self.optima:
            self.hit = self.count
        self.curve.append(self.best)
        return value

    def done(self) -> bool:
        return self.count >= self.budget

    def best_at(self, budget: int) -> float:
        if not self.curve:
            return float("nan")
        return self.curve[min(budget, len(self.curve)) - 1]


Method = Callable[[Oracle, int, np.random.Generator], None]

_OPERATOR_NAMES = ("swap", "insert", "inversion")
_STALL_RESTART = 60


def _random_perm(n: int, rng: np.random.Generator) -> list[int]:
    return [int(x) for x in rng.permutation(n)]


def _fresh_random(oracle: Oracle, n: int, rng: np.random.Generator, attempts: int = 400) -> list[int]:
    """Sample an unevaluated permutation, or give up if the space is saturated."""

    for _ in range(attempts):
        candidate = _random_perm(n, rng)
        if oracle.is_new(candidate):
            return candidate
    raise Stalled


# --------------------------------------------------------------------------
# reference
# --------------------------------------------------------------------------


def uniform(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    """Uniform sampling without replacement over the enumerated support.

    This is the method of record.  Best-of-k random sampling is the same
    procedure read off this curve at budget k, so it is not a separate entry.
    """

    keys = list(oracle.table.keys())
    for index in rng.permutation(len(keys)):
        oracle(list(keys[int(index)]))


# --------------------------------------------------------------------------
# neighbourhood enumeration and local search
# --------------------------------------------------------------------------


def _neighbours(perm: list[int], operator: str) -> list[list[int]]:
    n = len(perm)
    out: list[list[int]] = []
    if operator == "swap":
        for i, j in itertools.combinations(range(n), 2):
            child = perm.copy()
            child[i], child[j] = child[j], child[i]
            out.append(child)
    elif operator == "insert":
        for i in range(n):
            for j in range(n):
                if i == j:
                    continue
                child = perm.copy()
                element = child.pop(i)
                child.insert(j, element)
                if child != perm:
                    out.append(child)
    elif operator == "inversion":
        for i, j in itertools.combinations(range(n), 2):
            child = perm.copy()
            child[i : j + 1] = child[i : j + 1][::-1]
            out.append(child)
    else:  # pragma: no cover - guarded by caller
        raise ValueError(f"unknown operator {operator!r}")
    return out


def _local_search(oracle: Oracle, n: int, rng: np.random.Generator, operator: str) -> None:
    """Multi-start best-improvement local search; restarts on a local optimum."""

    while not oracle.done():
        current = _fresh_random(oracle, n, rng)
        current_value = oracle(current)
        while True:
            best_child: list[int] | None = None
            best_value = current_value
            for child in _neighbours(current, operator):
                value = oracle(child)
                if value > best_value:
                    best_value = value
                    best_child = child
            if best_child is None:
                break  # local optimum -> restart
            current, current_value = best_child, best_value


def ls_swap(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    _local_search(oracle, n, rng, "swap")


def ls_insert(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    _local_search(oracle, n, rng, "insert")


def ls_inversion(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    _local_search(oracle, n, rng, "inversion")


def simulated_annealing(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    """Geometric-cooling SA over the insert neighbourhood, restarting on stall."""

    values = list(oracle.table.values())
    scale = float(np.std(values)) or 1.0
    current = _fresh_random(oracle, n, rng)
    current_value = oracle(current)
    temperature = scale
    floor = scale * 1e-3
    stale = 0
    while not oracle.done():
        child = current.copy()
        MUTATION_OPERATORS["insert"](child, rng)
        was_new = oracle.is_new(child)
        child_value = oracle(child)
        delta = child_value - current_value
        if delta >= 0 or rng.random() < np.exp(delta / max(temperature, 1e-12)):
            current, current_value = child, child_value
        stale = 0 if was_new else stale + 1
        if stale > _STALL_RESTART:
            current = _fresh_random(oracle, n, rng)
            current_value = oracle(current)
            temperature = scale
            stale = 0
        temperature = max(temperature * 0.995, floor)


def iterated_local_search(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    """Local search plus a double-insert kick, accepting improvements only."""

    incumbent = _fresh_random(oracle, n, rng)
    incumbent_value = oracle(incumbent)
    stale = 0
    while not oracle.done():
        current, current_value = incumbent.copy(), incumbent_value
        while True:
            best_child, best_value = None, current_value
            for child in _neighbours(current, "insert"):
                value = oracle(child)
                if value > best_value:
                    best_value, best_child = value, child
            if best_child is None:
                break
            current, current_value = best_child, best_value
        if current_value > incumbent_value:
            incumbent, incumbent_value = current, current_value
            stale = 0
        else:
            stale += 1
        if stale > 3:
            incumbent = _fresh_random(oracle, n, rng)
            incumbent_value = oracle(incumbent)
            stale = 0
            continue
        kicked = incumbent.copy()
        for _ in range(2):
            MUTATION_OPERATORS["insert"](kicked, rng)
        incumbent = kicked
        incumbent_value = oracle(incumbent)


# --------------------------------------------------------------------------
# evolutionary executors
# --------------------------------------------------------------------------


def _evolutionary(
    oracle: Oracle,
    n: int,
    rng: np.random.Generator,
    *,
    operator: str | None,
    pop_size: int = 20,
    tournament: int = 3,
    aging: bool = False,
) -> None:
    """Steady-state EA.  ``aging=True`` retires the oldest member instead of
    the worst (regularized evolution, Real et al. 2019).  A stalled population
    receives a fresh random immigrant."""

    population: list[tuple[list[int], float]] = []
    for _ in range(min(pop_size, max(2, oracle.budget // 2))):
        candidate = _fresh_random(oracle, n, rng)
        population.append((candidate, oracle(candidate)))
    stale = 0
    while not oracle.done():
        picks = rng.choice(len(population), size=min(tournament, len(population)), replace=False)
        parent = max((population[int(i)] for i in picks), key=lambda item: item[1])[0]
        child = parent.copy()
        name = operator if operator is not None else _OPERATOR_NAMES[int(rng.integers(3))]
        MUTATION_OPERATORS[name](child, rng)
        if oracle.is_new(child):
            stale = 0
        else:
            stale += 1
            if stale > _STALL_RESTART:
                child = _fresh_random(oracle, n, rng)
                stale = 0
        population.append((child, oracle(child)))
        if aging:
            population.pop(0)
        else:
            worst = min(range(len(population)), key=lambda i: population[i][1])
            population.pop(worst)


def ea_elitist(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    _evolutionary(oracle, n, rng, operator="swap", aging=False)


def ea_aging(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    _evolutionary(oracle, n, rng, operator=None, aging=True)


def ea_portfolio(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    _evolutionary(oracle, n, rng, operator=None, aging=False)


# --------------------------------------------------------------------------
# surrogate-guided search
# --------------------------------------------------------------------------


def _encode_positional(perm: Sequence[int], n: int) -> np.ndarray:
    matrix = np.zeros((n, n))
    for position, module in enumerate(perm):
        matrix[module][position] = 1.0
    return matrix.ravel()


def _encode_precedence(perm: Sequence[int], n: int) -> np.ndarray:
    position = {value: index for index, value in enumerate(perm)}
    return np.array(
        [1.0 if position[i] < position[j] else 0.0 for i in range(n) for j in range(n) if i != j]
    )


def _surrogate(
    oracle: Oracle,
    n: int,
    rng: np.random.Generator,
    encode: Callable[[Sequence[int], int], np.ndarray],
    *,
    init: int = 10,
    pool: int = 200,
) -> None:
    """Ridge surrogate over an encoding; evaluate the top-predicted candidate.

    The Gram matrix is maintained incrementally rather than rebuilt each round,
    which is an implementation detail only -- the fitted weights, and therefore
    every decision the method makes, are identical either way.
    """

    targets: list[float] = []
    evaluated: list[list[int]] = []
    dimension = len(encode(list(range(n)), n))
    gram = np.eye(dimension)
    moment = np.zeros(dimension)

    def observe(candidate: list[int], value: float) -> None:
        vector = encode(candidate, n)
        gram[:, :] = gram + np.outer(vector, vector)
        moment[:] = moment + vector * value
        targets.append(value)
        evaluated.append(candidate)

    for _ in range(min(init, max(2, oracle.budget // 2))):
        candidate = _fresh_random(oracle, n, rng)
        observe(candidate, oracle(candidate))

    while not oracle.done():
        weights = np.linalg.solve(gram, moment)
        response = np.array(targets)
        top = np.argsort(response)[::-1][:5]
        candidates: list[list[int]] = []
        for index in top:
            base = evaluated[int(index)]
            for _ in range(pool // 10):
                child = base.copy()
                MUTATION_OPERATORS[_OPERATOR_NAMES[int(rng.integers(3))]](child, rng)
                if oracle.is_new(child):
                    candidates.append(child)
        for _ in range(pool // 4):
            child = _random_perm(n, rng)
            if oracle.is_new(child):
                candidates.append(child)
        if not candidates:
            candidates = [_fresh_random(oracle, n, rng)]
        design = np.stack([encode(c, n) for c in candidates])
        choice = candidates[int(np.argmax(design @ weights))]
        observe(choice, oracle(choice))


def surrogate_positional(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    _surrogate(oracle, n, rng, _encode_positional)


def surrogate_precedence(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    _surrogate(oracle, n, rng, _encode_precedence)


def eda_precedence(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    """Estimation-of-distribution search over pairwise precedence.

    Learns P(i before j) from the better half of everything evaluated so far
    and samples new orderings by insertion under that preference.  This is the
    cheap model-based baseline for "just learn the pairwise structure".
    """

    samples: list[tuple[list[int], float]] = []
    for _ in range(min(10, max(2, oracle.budget // 2))):
        candidate = _fresh_random(oracle, n, rng)
        samples.append((candidate, oracle(candidate)))

    while not oracle.done():
        ordered = sorted(samples, key=lambda item: item[1], reverse=True)
        elite = ordered[: max(2, len(ordered) // 2)]
        counts = np.ones((n, n))
        for perm, _ in elite:
            position = {value: index for index, value in enumerate(perm)}
            for i in range(n):
                for j in range(n):
                    if i != j and position[i] < position[j]:
                        counts[i][j] += 1.0
        probability = counts / (counts + counts.T)

        candidate: list[int] = []
        for value in rng.permutation(n):
            value = int(value)
            weights = []
            for slot in range(len(candidate) + 1):
                score = 0.0
                for index, other in enumerate(candidate):
                    score += np.log(
                        probability[value][other] if index >= slot else probability[other][value]
                    )
                weights.append(score)
            shifted = np.array(weights) - max(weights)
            distribution = np.exp(shifted)
            distribution /= distribution.sum()
            candidate.insert(int(rng.choice(len(weights), p=distribution)), value)

        if not oracle.is_new(candidate):
            candidate = _fresh_random(oracle, n, rng)
        samples.append((candidate, oracle(candidate)))


# --------------------------------------------------------------------------
# the protocol, with its probe cost charged
# --------------------------------------------------------------------------

_EXECUTOR_FOR_RECOMMENDATION: dict[str, Method] = {
    "evolution": ea_portfolio,
    "uniform_sampling": uniform,
    "avoid_local_search": uniform,
    "improve_evaluator": uniform,
}


def prism_protocol(oracle: Oracle, n: int, rng: np.random.Generator) -> None:
    """Spend ~20% of the budget diagnosing, then run the selected executor.

    The probe is charged to the same oracle, so the comparison against uniform
    sampling is at equal *total* distinct-evaluation budget.  If the probe
    consumes the whole budget that is a real outcome and is recorded as such.
    """

    probe = max(4, int(0.2 * oracle.budget))
    pair_samples = max(2, probe // 8)
    landscape_samples = max(2, min(probe // 2, oracle.budget - 1))
    seed = int(rng.integers(0, 2**31 - 1))

    result = preflight(
        n=n,
        fitness_fn=oracle,
        operators=_OPERATOR_NAMES,
        pair_samples=pair_samples,
        landscape_samples=landscape_samples,
        seed=seed,
    )
    executor = _EXECUTOR_FOR_RECOMMENDATION[result.recommendation]
    if executor is ea_portfolio:
        _evolutionary(oracle, n, rng, operator=result.selected_operator, aging=False)
    else:
        executor(oracle, n, rng)


METHODS: dict[str, Method] = {
    "uniform": uniform,
    "ls_swap": ls_swap,
    "ls_insert": ls_insert,
    "ls_inversion": ls_inversion,
    "simulated_annealing": simulated_annealing,
    "iterated_local_search": iterated_local_search,
    "ea_elitist": ea_elitist,
    "ea_aging": ea_aging,
    "ea_portfolio": ea_portfolio,
    "surrogate_positional": surrogate_positional,
    "surrogate_precedence": surrogate_precedence,
    "eda_precedence": eda_precedence,
    "prism_protocol": prism_protocol,
}


def run_method(
    name: str,
    table: dict[tuple[int, ...], float],
    optima: frozenset,
    n: int,
    budget: int,
    seed: int,
) -> Oracle:
    """Run one method on one landscape at one budget; return the spent oracle."""

    oracle = Oracle(table, optima, budget)
    rng = np.random.default_rng(seed)
    try:
        METHODS[name](oracle, n, rng)
    except BudgetExhausted:
        pass
    return oracle
