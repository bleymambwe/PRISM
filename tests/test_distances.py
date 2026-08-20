import pytest

from prism_search import cayley_distance, kendall_tau_distance, ulam_distance


@pytest.mark.parametrize(
    ("distance", "expected"),
    [
        (cayley_distance, 0),
        (kendall_tau_distance, 0),
        (ulam_distance, 0),
    ],
)
def test_identity_distance_is_zero(distance, expected):
    assert distance([0, 1, 2, 3], [0, 1, 2, 3]) == expected


def test_distances_match_their_move_geometries():
    identity = [0, 1, 2, 3]
    assert cayley_distance(identity, [1, 0, 2, 3]) == 1
    assert kendall_tau_distance(identity, [3, 2, 1, 0]) == 6
    assert ulam_distance(identity, [1, 2, 3, 0]) == 1


@pytest.mark.parametrize("distance", [cayley_distance, kendall_tau_distance, ulam_distance])
def test_distances_are_symmetric(distance):
    left = [2, 0, 3, 1]
    right = [0, 1, 2, 3]
    assert distance(left, right) == distance(right, left)


@pytest.mark.parametrize("distance", [cayley_distance, kendall_tau_distance, ulam_distance])
def test_distances_reject_nonmatching_permutations(distance):
    with pytest.raises(ValueError, match="same unique elements"):
        distance([0, 1, 1], [0, 1, 2])
