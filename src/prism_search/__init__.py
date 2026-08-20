"""PRISM: diagnostics and search for permutation-valued decisions."""

from .core import PRISM
from .diagnostics import fitness_distance_correlation, preflight
from .distances import cayley_distance, kendall_tau_distance, ulam_distance
from .results import PreflightResult, PrismResult

__all__ = [
    "PRISM",
    "PreflightResult",
    "PrismResult",
    "cayley_distance",
    "fitness_distance_correlation",
    "kendall_tau_distance",
    "preflight",
    "ulam_distance",
]

__version__ = "0.1.0"
