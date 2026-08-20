import numpy as np
import pytest

from prism_search.operators import MUTATION_OPERATORS


@pytest.mark.parametrize("name", MUTATION_OPERATORS)
def test_mutations_preserve_permutation(name):
    permutation = list(range(8))
    MUTATION_OPERATORS[name](permutation, np.random.default_rng(7))
    assert sorted(permutation) == list(range(8))


@pytest.mark.parametrize("name", MUTATION_OPERATORS)
def test_mutations_reject_singleton(name):
    with pytest.raises(ValueError, match="at least two"):
        MUTATION_OPERATORS[name]([0], np.random.default_rng(7))


def test_mutations_reject_duplicate_elements():
    with pytest.raises(ValueError, match="unique"):
        MUTATION_OPERATORS["swap"]([0, 0], np.random.default_rng(7))
