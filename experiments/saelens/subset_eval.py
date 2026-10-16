"""Stage 1 (resumable): loss of GPT-2 small with every subset of K SAE features ablated.

Frozen setup
  model   : gpt2 (HF transformers), CPU, float32
  SAE     : jbloom/GPT2-Small-SAEs-Reformatted, blocks.8.hook_resid_pre (24576 features),
            loaded directly from its safetensors file (same weights and encode/decode as
            sae_lens: relu((x - b_dec) @ W_enc + b_enc)); no sae_lens install required.
  data    : first N_SEQ x SEQ_LEN tokens of the wikitext-2-raw-v1 test split (fixed)
  space   : K=10 candidate features = top-K by mean activation x decoder norm on a disjoint
            selection slice (train split). Fixed once, saved to results/features.json.
  ablation: x <- x - sum_{i in S} a_i(x) * W_dec[i]  (zero-ablate feature i, keep SAE error)

Why subsets: a permutation's prefix sets are all that matter, so the 2^K subset losses
determine every permutation's fitness. Stage 2 then searches on a lookup table.

Usage (foreground chunks, kill-safe, resumes):  python subset_eval.py 240
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import torch

HERE = Path(__file__).parent
RES = HERE / "results"
K, N_SEQ, SEQ_LEN, LAYER = 10, 16, 64, 8
REPO, SAE_DIR = "jbloom/GPT2-Small-SAEs-Reformatted", f"blocks.{LAYER}.hook_resid_pre"
torch.set_num_threads(4)


def load_sae():
    from huggingface_hub import hf_hub_download
    from safetensors.torch import load_file

    w = load_file(hf_hub_download(REPO, f"{SAE_DIR}/sae_weights.safetensors"))
    return {k: v.float() for k, v in w.items()}  # W_enc, W_dec, b_enc, b_dec


def tokens(split: str):
    from datasets import load_dataset
    from transformers import AutoTokenizer

    text = "\n\n".join(load_dataset("wikitext", "wikitext-2-raw-v1", split=split)["text"])[:200_000]
    ids = AutoTokenizer.from_pretrained("gpt2")(text)["input_ids"][: N_SEQ * SEQ_LEN]
    return torch.tensor(ids).view(N_SEQ, SEQ_LEN)


def main(budget_s: float) -> None:
    from transformers import AutoModelForCausalLM

    t0 = time.time()
    RES.mkdir(exist_ok=True)
    out = RES / "subset_losses.csv"
    model = AutoModelForCausalLM.from_pretrained("gpt2").eval()
    sae = load_sae()
    W_enc, W_dec, b_enc, b_dec = sae["W_enc"], sae["W_dec"], sae["b_enc"], sae["b_dec"]

    def acts_of(x):
        return torch.relu((x - b_dec) @ W_enc + b_enc)

    captured: dict = {}
    state: dict = {"feats": None}

    def hook(_m, args):
        x = args[0]
        if state["feats"] is None:
            captured["x"] = x.detach()
            return None
        idx = state["feats"]
        return (x - acts_of(x)[..., idx] @ W_dec[idx],) + args[1:]

    model.transformer.h[LAYER].register_forward_pre_hook(hook)

    def lm_loss(ids):
        with torch.no_grad():
            return model(ids, labels=ids).loss.item()

    feats_path = RES / "features.json"
    if not feats_path.exists():
        lm_loss(tokens("train"))
        a = acts_of(captured["x"]).reshape(-1, W_enc.shape[1])
        feats = (a.mean(0) * W_dec.norm(dim=1)).topk(K).indices.tolist()
        feats_path.write_text(json.dumps({"layer": LAYER, "sae": f"{REPO}/{SAE_DIR}", "features": feats}))
    feats = json.loads(feats_path.read_text())["features"]

    ids = tokens("test")
    done: dict[int, float] = {}
    if out.exists():
        with out.open() as f:
            done = {int(r["mask"]): float(r["loss"]) for r in csv.DictReader(f)}
    new = not out.exists()
    with out.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["mask", "loss"])
        for mask in range(2**K):
            if mask in done:
                continue
            if time.time() - t0 > budget_s:
                print(f"BUDGET HIT: {len(done)}/{2**K} subsets done; rerun to resume")
                return
            state["feats"] = [feats[i] for i in range(K) if mask >> i & 1] or None
            loss = lm_loss(ids)
            w.writerow([mask, repr(loss)])
            f.flush()
            done[mask] = loss
    print(f"STAGE 1 COMPLETE: {len(done)} subsets")


if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else 240)
