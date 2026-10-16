# SAELens ablation-order experiment

Question: does PRISM's permutation search beat random, Nevergrad and a greedy sort at
choosing the ORDER in which SAE features are ablated in frozen GPT-2 small?

The objective depends only on prefix sets, so stage 1 evaluates all 2^10 feature subsets once
(resumable, CPU); stage 2 searches on the lookup table and compares to the exact DP optimum.

    python experiments/saelens/subset_eval.py 240   # repeat until it prints STAGE 1 COMPLETE
    python experiments/saelens/search_orders.py

Caveat: if feature effects are near-additive, the greedy sort is near-optimal and the landscape
is trivial; report that baseline honestly. Not evidence of a completed SAELens study until
stage 1 has run in full and the results are reviewed.
