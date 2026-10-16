"""Make iteration-26's ``from benchmarks.synthetic import OBJECTIVES`` resolve.

``prism-research/benchmarks/*.py`` (git-ignored) no longer exists on disk; only
bytecode remains.  The anonymous artifact ships the same objectives as source.
Equality with the old bytecode was checked on every permutation at n=5,6,7
(0 mismatches), so this shim is behaviour-preserving.
"""

import importlib.util
import os
import sys
import types

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC = os.path.join(
    _HERE, "..", "..", "publication", "tmlr-submission", "anonymous-artifact", "loaders", "synthetic.py"
)
if "benchmarks.synthetic" not in sys.modules:
    spec = importlib.util.spec_from_file_location("benchmarks.synthetic", _SRC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    package = types.ModuleType("benchmarks")
    package.__path__ = []
    package.synthetic = module
    sys.modules["benchmarks"] = package
    sys.modules["benchmarks.synthetic"] = module
