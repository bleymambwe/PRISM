"""Order SAE features for a sequential ablation sweep, scored via PRISM.

The ordering question: in which order should a small set of SAE features be
ablated so that the cumulative drop in a model's next-token logit for a fixed
prompt is largest? This is a demonstration of the callback boundary in
``prism_search.integrations.saelens``. It is NOT a completed SAELens study.

Modes
-----
``--mode synthetic`` (default when SAELens is missing)
    A deterministic order-dependent toy evaluator; needs only NumPy.
``--mode saelens``
    Loads gpt2-small and a public layer-8 residual SAE through ``sae_lens``
    (``pip install sae-lens transformer-lens``; downloads weights on first run).

Usage:  python examples/saelens_feature_ordering.py --mode synthetic
"""

from __future__ import annotations

import argparse
import random
import time

import numpy as np

from prism_search import PRISM
from prism_search.integrations.saelens import make_sae_fitness, preflight_sae


def synthetic_evaluator(n: int, seed: int = 0):
    """Order-dependent score: pairwise interaction matrix plus position weights."""
    rng = np.random.default_rng(seed)
    interact = rng.normal(size=(n, n))
    weights = np.linspace(1.0, 0.2, n)

    def evaluate(order: tuple[int, ...]) -> float:
        return float(sum(weights[pos] * interact[order[pos - 1] if pos else feat, feat]
                         for pos, feat in enumerate(order)))

    return evaluate


def saelens_evaluator(n: int, prompt: str, release: str, sae_id: str):
    """Cumulative-ablation effect on the final-token top logit, order-dependent
    because each step re-encodes the residual after earlier ablations."""
    import torch
    from sae_lens import SAE
    from transformer_lens import HookedTransformer

    model = HookedTransformer.from_pretrained("gpt2-small", device="cpu")
    sae = SAE.from_pretrained(release=release, sae_id=sae_id, device="cpu")
    hook = sae.cfg.metadata.hook_name if hasattr(sae.cfg, "metadata") else sae.cfg.hook_name
    tokens = model.to_tokens(prompt)

    with torch.no_grad():
        base_logits, cache = model.run_with_cache(tokens, names_filter=hook)
        acts = sae.encode(cache[hook])[0, -1]
        top_feats = torch.topk(acts, n).indices.tolist()
        target = int(base_logits[0, -1].argmax())
        base = float(base_logits[0, -1, target])

    def evaluate(order: tuple[int, ...]) -> float:
        feats = [top_feats[i] for i in order]
        state = {"removed": []}

        def patch(resid, hook):  # noqa: ARG001
            x = resid.clone()
            for f in feats:
                latent = sae.encode(x)[0, -1]
                x[0, -1] -= latent[f] * sae.W_dec[f]
            return x

        with torch.no_grad():
            logits = model.run_with_hooks(tokens, fwd_hooks=[(hook, patch)])
        return base - float(logits[0, -1, target])  # larger drop = higher fitness

    return evaluate


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["synthetic", "saelens"], default="synthetic")
    p.add_argument("--n", type=int, default=6, help="features to order")
    p.add_argument("--budget", type=int, default=60, help="distinct evaluations")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--max-seconds", type=float, default=200.0)
    p.add_argument("--prompt", default="The Eiffel Tower is located in the city of")
    p.add_argument("--release", default="gpt2-small-res-jb")
    p.add_argument("--sae-id", default="blocks.8.hook_resid_pre")
    args = p.parse_args()

    if args.mode == "saelens":
        try:
            evaluator = saelens_evaluator(args.n, args.prompt, args.release, args.sae_id)
        except ImportError as exc:
            raise SystemExit(f"SAELens mode needs sae-lens + transformer-lens: {exc}")
    else:
        evaluator = synthetic_evaluator(args.n, args.seed)

    start = time.monotonic()
    report = preflight_sae(args.n, evaluator, pair_samples=10, landscape_samples=20,
                           seed=args.seed)
    print("preflight:", report)

    fitness = make_sae_fitness(evaluator, args.n)
    pop = max(4, min(10, args.budget // 4))
    result = PRISM(args.n, fitness, pop_size=pop, seed=args.seed).search(args.budget)
    print("PRISM best:", result.best_perm, result.best_fitness)

    rng = random.Random(args.seed)
    rand_best = max(fitness(tuple(rng.sample(range(args.n), args.n)))
                    for _ in range(args.budget))
    print("random-order best at equal budget:", rand_best)
    elapsed = time.monotonic() - start
    note = "  WARNING: over --max-seconds; lower --budget/--n" if elapsed > args.max_seconds else ""
    print(f"elapsed {elapsed:.1f}s (limit {args.max_seconds}s){note}")


if __name__ == "__main__":
    main()
