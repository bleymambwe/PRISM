"""Evolutionary executors for permutation-valued optimization."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from math import factorial, isfinite

import numpy as np

from .operators import MUTATION_OPERATORS
from .results import PrismResult

FitnessFunction = Callable[[Sequence[int]], float]
PORTFOLIO_MODES = ("portfolio", "adaptive")


class PRISM:
    """Evolutionary search over permutations of ``range(n)``.

    Parameters are validated at construction.  ``search`` is the recommended
    executor because it enforces a distinct-evaluation budget.  ``evolve``
    preserves the generation-based interface used by the original experiments.
    """

    def __init__(
        self,
        n: int,
        fitness_fn: FitnessFunction,
        pop_size: int = 20,
        p_m: float = 0.05,
        k: int = 3,
        elitism: int = 1,
        seed: int | None = None,
        mutation: str = "swap",
    ) -> None:
        if n < 2:
            raise ValueError("n must be at least 2")
        if pop_size < 2:
            raise ValueError("pop_size must be at least 2")
        if not 0.0 <= p_m <= 1.0:
            raise ValueError("p_m must be between 0 and 1")
        if not 1 <= k <= pop_size:
            raise ValueError("k must be between 1 and pop_size")
        if not 0 <= elitism < pop_size:
            raise ValueError("elitism must be between 0 and pop_size - 1")
        valid_modes = set(MUTATION_OPERATORS) | set(PORTFOLIO_MODES)
        if mutation not in valid_modes:
            raise ValueError(
                f"Unknown mutation mode {mutation!r}; choose from {', '.join(sorted(valid_modes))}"
            )
        if pop_size > factorial(n):
            raise ValueError("pop_size cannot exceed the number of distinct permutations")

        self.n = n
        self.fitness_fn = fitness_fn
        self.pop_size = pop_size
        self.p_m = p_m
        self.k = k
        self.elitism = elitism
        self.mutation_mode = mutation
        self.rng = np.random.default_rng(seed)
        self._operator_names = list(MUTATION_OPERATORS)
        self._operator_weights = np.full(
            len(self._operator_names), 1.0 / len(self._operator_names)
        )
        self.population = self._initial_population()

    def _initial_population(self) -> list[list[int]]:
        population: list[list[int]] = []
        seen: set[tuple[int, ...]] = set()
        while len(population) < self.pop_size:
            candidate = tuple(int(value) for value in self.rng.permutation(self.n))
            if candidate not in seen:
                seen.add(candidate)
                population.append(list(candidate))
        return population

    def _evaluate(self, permutation: Sequence[int]) -> float:
        value = float(self.fitness_fn(permutation))
        if not isfinite(value):
            raise ValueError(f"fitness_fn returned a non-finite value for {permutation}")
        return value

    def _mutate(self, child: list[int]) -> int | None:
        if self.mutation_mode in MUTATION_OPERATORS:
            MUTATION_OPERATORS[self.mutation_mode](child, self.rng)
            return None
        operator_index = int(self.rng.choice(len(self._operator_names), p=self._operator_weights))
        MUTATION_OPERATORS[self._operator_names[operator_index]](child, self.rng)
        return operator_index

    def _reward_operator(self, operator_index: int, reward: float) -> None:
        gamma = 0.1
        weight_floor = 0.10
        weights = self._operator_weights.copy()
        weights[operator_index] = (1.0 - gamma) * weights[operator_index] + gamma * reward
        weights = np.maximum(weights / weights.sum(), weight_floor)
        self._operator_weights = weights / weights.sum()

    def _weights_result(self) -> dict[str, float] | None:
        if self.mutation_mode not in PORTFOLIO_MODES:
            return None
        return dict(zip(self._operator_names, self._operator_weights.round(6), strict=True))

    def evolve(
        self,
        generations: int = 150,
        target_fitness: float | None = None,
        verbose: bool = False,
    ) -> PrismResult:
        """Run the legacy generation-based executor.

        This method reevaluates each population every generation to reproduce
        the original PRISM experiments.  Prefer :meth:`search` when evaluation
        budgets represent expensive or distinct candidates.
        """

        if generations < 1:
            raise ValueError("generations must be at least 1")
        best_fitness = -float("inf")
        best_perm: list[int] = []
        history: list[float] = []
        hit_generation: int | None = None
        evaluations = 0

        for generation in range(generations):
            fitnesses = [self._evaluate(permutation) for permutation in self.population]
            evaluations += len(self.population)
            best_index = int(np.argmax(fitnesses))
            if fitnesses[best_index] > best_fitness:
                best_fitness = fitnesses[best_index]
                best_perm = self.population[best_index].copy()
            history.append(fitnesses[best_index])
            if verbose and generation % 50 == 0:
                print(f"Generation {generation}: best={fitnesses[best_index]:.6g}")
            if target_fitness is not None and best_fitness >= target_fitness:
                hit_generation = generation
                break

            order = np.argsort(fitnesses)[::-1]
            new_population = [
                self.population[int(index)].copy() for index in order[: self.elitism]
            ]
            while len(new_population) < self.pop_size:
                tournament = self.rng.choice(self.pop_size, self.k, replace=False)
                parent_index = int(
                    tournament[int(np.argmax([fitnesses[int(index)] for index in tournament]))]
                )
                child = self.population[parent_index].copy()
                if self.rng.random() < self.p_m:
                    operator_index = self._mutate(child)
                    if operator_index is not None and self.mutation_mode == "adaptive":
                        child_fitness = self._evaluate(child)
                        evaluations += 1
                        self._reward_operator(
                            operator_index,
                            float(child_fitness > fitnesses[parent_index]),
                        )
                new_population.append(child)
            self.population = new_population

        return PrismResult(
            best_perm=best_perm,
            best_fitness=best_fitness,
            history=history,
            hit_generation=hit_generation,
            generations_run=len(history),
            evaluations=evaluations,
            operator_weights=self._weights_result(),
            termination_reason="target_reached" if hit_generation is not None else "generations",
        )

    def search(
        self,
        max_evaluations: int,
        *,
        target_fitness: float | None = None,
        max_proposal_attempts: int = 1_000,
    ) -> PrismResult:
        """Run a steady-state executor with a distinct-evaluation budget."""

        if max_evaluations < self.pop_size:
            raise ValueError("max_evaluations must be at least pop_size")
        if max_proposal_attempts < 1:
            raise ValueError("max_proposal_attempts must be at least 1")
        budget = min(max_evaluations, factorial(self.n))
        cache: dict[tuple[int, ...], float] = {}
        cache_hits = 0
        for candidate in self.population:
            key = tuple(candidate)
            cache[key] = self._evaluate(candidate)

        best_key = max(cache, key=cache.__getitem__)
        history = [cache[best_key]]
        termination_reason = "budget_exhausted"
        while len(cache) < budget:
            if target_fitness is not None and cache[best_key] >= target_fitness:
                termination_reason = "target_reached"
                break
            population_fitness = [cache[tuple(candidate)] for candidate in self.population]
            tournament = self.rng.choice(self.pop_size, self.k, replace=False)
            parent_index = int(
                tournament[
                    int(np.argmax([population_fitness[int(index)] for index in tournament]))
                ]
            )
            parent = self.population[parent_index]
            child: list[int] | None = None
            operator_index: int | None = None
            for _ in range(max_proposal_attempts):
                proposal = parent.copy()
                operator_index = self._mutate(proposal)
                if tuple(proposal) not in cache:
                    child = proposal
                    break
                cache_hits += 1
            if child is None:
                termination_reason = "proposal_space_saturated"
                break

            child_fitness = self._evaluate(child)
            cache[tuple(child)] = child_fitness
            if operator_index is not None and self.mutation_mode == "adaptive":
                self._reward_operator(
                    operator_index,
                    float(child_fitness > population_fitness[parent_index]),
                )

            elite_indices = {
                int(index) for index in np.argsort(population_fitness)[::-1][: self.elitism]
            }
            replaceable = [index for index in range(self.pop_size) if index not in elite_indices]
            worst_index = min(replaceable, key=population_fitness.__getitem__)
            self.population[worst_index] = child
            if child_fitness > cache[best_key]:
                best_key = tuple(child)
            history.append(cache[best_key])

        return PrismResult(
            best_perm=list(best_key),
            best_fitness=cache[best_key],
            history=history,
            evaluations=len(cache),
            operator_weights=self._weights_result(),
            cache_hits=cache_hits,
            termination_reason=termination_reason,
        )
