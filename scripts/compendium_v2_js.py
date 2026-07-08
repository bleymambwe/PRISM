"""Iteration 14: inject companion-v2 JS (tree, walkthrough, QA) before
the closing </script> of the compendium. Idempotent via marker."""

import io
import sys

P = "deliverables/PRISM_Research_Compendium.html"
s = io.open(P, encoding="utf-8").read()
if "companionV2js" in s:
    sys.exit("js already injected")

JS = r"""
/* ================= companion v2: decision tree ================= */
(()=>{ // companionV2js
const TREE={
 start:{q:"Step 1 — the gate. You evaluated ~30 random orderings. Does fitness vary materially (std above your measurement resolution)?",
  opts:[["Yes — orderings differ","pf"],["No — flat fitness","stopFlat"]]},
 stopFlat:{v:"Ordering does not matter for this system. Stop — you just saved the whole search budget. (Precedent: AND truth-table, Iteration 2: zero order-variance.)",bad:true},
 pf:{q:"Step 2 — pre-flight (~a few hundred evaluations). What does FDC look like? (Regime call reliability at 200 sample points: 0.78–1.00 across our landscapes.)",
  opts:[["Materially negative (≤ −0.15)","neg"],["Near zero","zero"],["Positive (> +0.05)","pos"]]},
 pos:{v:"Deceptive landscape — fitness is smooth but points AWAY from optima. Do not use evolutionary search at all. (This call was 100% stable in resampling; precedent: deceptive_n7, +0.78.)",bad:true},
 zero:{v:"Needle-in-a-haystack: no method beats uniform random sampling here. Report random-without-replacement as the method of record; aging-PRISM is equivalent if you want anytime population behavior. (Precedent: parity n=7 — every 40-seed hit-rate CI overlaps random's [0.60,0.86].)"},
 neg:{q:"Step 3 — structure exists; search will pay. Does ρ1 show a clear operator signal, and is the max the insert operator (precedence structure)?",
  opts:[["Yes — insert dominates ρ1","surr"],["Another operator dominates","match"],["ρ1 all ≈ 0 (no signal)","port"]]},
 surr:{v:"Use the precedence-pair surrogate (binary i-before-j features + ridge, evaluate-top-predicted). It dominated every population method on pure precedence: 14.8 evals [14,15] to a 1-in-5040 optimum vs elitist 54.2 [50,59]; random 2/40. (Experiment N, D17. Operator-pick reliability at 100 pairs: 0.94 on kendall.)"},
 match:{v:"Use elitist PRISM with the matched operator (argmax ρ1, excluding scramble): fastest, and keeps the convergence guarantee. (Pick reliability at 100 pairs: 0.96–0.99 on typed landscapes. Precedent: Experiment C — mismatch is a 100% failure, not a slowdown.)"},
 port:{v:"No operator signal usually accompanies weak locality — double-check FDC. If genuinely negative but ρ1-flat, run the uniform portfolio (zero failures everywhere, ≤4.1× matched cost) or the elitist+restart hybrid (never worst on any landscape tested)."}
};
const el2=document.getElementById("tree");
if(el2){
 let path=[];
 function render(){
  el2.innerHTML="";
  let node="start";
  const frag=document.createDocumentFragment();
  for(const choice of path.concat([null])){
   const nd=TREE[node];
   const d=document.createElement("div");
   if(nd.v!==undefined){
    d.className="tnode tverdict"+(nd.bad?" bad":"");
    d.innerHTML="<span class='q'>Recommendation.</span> "+nd.v;
    frag.appendChild(d);break;
   }
   d.className="tnode";
   d.innerHTML="<span class='q'>"+nd.q+"</span>";
   if(choice===null){
    nd.opts.forEach(([label,next])=>{
     const b=document.createElement("button");
     b.className="tbtn";b.textContent=label;
     b.onclick=()=>{path.push(next===undefined?label:next);render();};
     b.dataset.next=next;
     b.onclick=()=>{path.push(next);render();};
     d.appendChild(b);});
    frag.appendChild(d);break;
   } else {
    const chosen=nd.opts.find(o=>o[1]===choice);
    const sp=document.createElement("span");
    sp.className="trel";sp.textContent="→ "+chosen[0];
    d.appendChild(sp);frag.appendChild(d);node=choice;
   }
  }
  const r=document.createElement("button");
  r.className="treset";r.textContent="start over";
  r.onclick=()=>{path=[];render();};
  el2.appendChild(frag);el2.appendChild(r);
 }
 render();
}
/* ================= companion v2: walkthrough ================= */
const W=document.getElementById("walk");
if(W){
 const pop=[
  {p:"[2,0,1,4,3]",f:.667},{p:"[1,2,0,3,4]",f:.917},
  {p:"[0,3,2,1,4]",f:.75},{p:"[4,1,3,0,2]",f:.583},
  {p:"[3,4,0,2,1]",f:.833},{p:"[0,1,2,3,4]",f:.667}];
 const msg=document.getElementById("wmsg");
 const steps=[
  {m:"Generation start: six of the twenty orderings, each with its deterministic XOR-v4 fitness (from the enumerated landscape).",
   f:()=>{}},
  {m:"Evaluate + elitism: the best ordering — [1,2,0,3,4] at 0.917 — is copied to the next generation unchanged. It can never be lost (green).",
   f:els=>els[1].classList.add("elite")},
  {m:"Tournament: three slots are drawn at random — here slots 1, 4 and 6 (blue). The best of the three ([3,4,0,2,1], 0.833) becomes the parent.",
   f:els=>{els[0].classList.add("win");els[3].classList.add("win");els[4].classList.add("win");}},
  {m:"Mutation: with probability p_m the child is perturbed — the portfolio draws one operator at random; an insert move turns [3,4,0,2,1] into [3,0,2,4,1] (red). Most children copy through unchanged.",
   f:els=>{els[4].classList.add("mut");els[4].querySelector(".pp").textContent="[3,0,2,4,1]";els[4].querySelector(".f").textContent="f = ?";}},
  {m:"Repeat until the new population is full, evaluate, and loop. Elitism makes best-fitness monotone; mutation keeps every ordering reachable — the two halves of the convergence theorem.",
   f:()=>{}}];
 let step=0, els=[];
 function reset(){
  W.innerHTML="";els=[];step=0;
  const row=document.createElement("div");row.className="wrow";
  pop.forEach(o=>{const d=document.createElement("div");
   d.className="wslot";
   d.innerHTML="<div class='pp'>"+o.p+"</div><div class='f'>f = "+o.f+"</div>";
   row.appendChild(d);els.push(d);});
  W.appendChild(row);msg.textContent=steps[0].m;steps[0].f(els);step=1;
 }
 document.getElementById("wnext").onclick=()=>{
  if(step>=steps.length){reset();return;}
  msg.textContent=steps[step].m;steps[step].f(els);step++;
  if(step>=steps.length)document.getElementById("wnext").textContent="restart ▸";
  else document.getElementById("wnext").textContent="Next step ▸";};
 document.getElementById("wreset").onclick=()=>{document.getElementById("wnext").textContent="Next step ▸";reset();};
 reset();
}
/* ================= companion v2: benchmark QA ================= */
const QA=document.getElementById("qa");
if(QA){
 const items=[
  ["Synthetic typed landscapes","Experiments C, D, F · iterations 3–4",[
   ["What is it?","Closed-form permutation objectives: hamming (absolute position), kendall (precedence), adjacency (routing), deceptive (adversarial). Deterministic, exact optima known."],
   ["Why selected?","Each isolates one structure class from the permutation-EA literature — the cleanest way to test operator-neighborhood theory."],
   ["What does it measure?","Generations to reach the optimum; censoring rate at a 10,000-generation cap."],
   ["Baselines & comparability?","Full factorial: 4 operators × 3 types × 6 sizes, identical loop/seeds/cap; portfolio and adaptive added in Experiment F; random added at n=7 (2/40 hits on kendall)."],
   ["Where does PRISM win / lose?","Matched operator wins every type (swap 405 gens at n=16 on hamming). Mismatch on plateau-rich types = 100% failure. Deceptive defeats everything."],
   ["Why?","Operators define the neighborhood graph; plateaus are uncrossable under the wrong moves; deception points the gradient away from optima."],
   ["Statistically meaningful?","Effect sizes are censoring-vs-hundreds-of-generations; 15 seeds/cell suffice for the binary claim; n=7 comparisons re-run at 40 seeds with CIs (It-14)."],
   ["What would strengthen it?","Mixed-type landscapes — the open frontier."]]],
  ["Ground-truth neural benchmarks (v4)","Experiments G, H, I · iterations 5–7",[
   ["What is it?","Networks of n permuted residual blocks; weight init seeded from the permutation → deterministic fitness; entire landscapes enumerated (120 / 720 / 5,040 orderings)."],
   ["Why selected?","Determinism + enumerability = an exact answer key; eliminates best-observed noise bias that inflated the original results."],
   ["What does it measure?","Exact hit rate, regret, and evaluations-to-first-optimum against known optima."],
   ["Baselines & comparability?","Six methods × 40 seeds × Wilson CIs (It-14), all against the same cached landscape — perfectly comparable."],
   ["Where does PRISM win / lose?","Wins at n=5–6 (hit rates 0.90–1.00). LOSES at n=7 parity: elitist 19/40 [0.33,0.63] is significantly worse than random 30/40 [0.60,0.86]; no method separates from random there."],
   ["Why?","Locality: ρ1 ≈ 0.02 and FDC ≈ −0.06 at n=7 — the top of the landscape is locally random, so local search has nothing to climb."],
   ["Conclusions?","Evolutionary search pays exactly when pre-search locality statistics say it will — the falsification became the diagnostic."],
   ["What would strengthen it?","n≥8 via sampled statistics; alternative seeding conventions to test landscape-family sensitivity."]]],
  ["LLM instruction ordering (GSM8K)","Experiments K, M · iterations 9, 11",[
   ["What is it?","6 (then 8) fixed reasoning instructions permuted as numbered prompt steps; fitness = Gemini 2.5 Flash-Lite accuracy (temp 0) on fixed GSM8K subsets; all 720 n=6 orderings enumerated (~$3–5)."],
   ["Why selected?","A real, API-priced ordering surface where ground truth is still enumerable — and prompt-order sensitivity was folklore without a map."],
   ["What does it measure?","Accuracy per ordering; per-module position effects; search efficiency vs random at equal distinct-evaluation budgets."],
   ["Comparable conditions?","Identical prompts modulo step order; same model snapshot, decoding, questions, extraction; shared answer cache."],
   ["Key result?","Ordering swings accuracy 6.3% → 96.9%. ANSWER-first = 0.435 vs ANSWER-last = 0.870; COMPUTE-first = 0.908."],
   ["Was search superior?","No — corrected at 40 seeds: PRISM 9.9 [7,13] evals vs random 10.8 [8,14] (optima dense at 60/720). The pre-flight predicted the operator (insert) and the searchability correctly; that, plus the effect map, is the contribution."],
   ["Limitations?","One model, one task family; extraction regex; contamination affects absolute accuracy but not ordering comparisons; n=8 fitness resolution too coarse to discriminate (D16)."],
   ["What would strengthen it?","Second model; harder questions (MATH); finer-grained fitness; cross-model transfer of position effects."]]],
  ["Method improvements","Experiments L, N · iterations 10, 12",[
   ["What is it?","Aging evolution (Real et al.), elitist+restart hybrid, and BANANAS-style surrogates with positional vs precedence encodings, benchmarked on four cached landscapes."],
   ["Why selected?","Each targets a measured weakness: premature convergence (aging/hybrid) and the random-parity result (surrogates)."],
   ["Statistically meaningful?","40 seeds + CIs everywhere (It-14). Aging > elitist on parity (CIs barely overlap); surr-prec > elitist on kendall (disjoint CIs); on parity NO method separates from random."],
   ["Where do they lose?","Aging is slower on structured landscapes; hybrid wastes restarts where patience suffices; positional surrogate inert off its structure class."],
   ["Conclusions?","Method selection is landscape diagnosis: operator, replacement policy, and encoding all follow from the same pre-flight (D15, D17)."],
   ["What would strengthen it?","Uncertainty-aware acquisition; more encodings (adjacency); stagnation-threshold sweep for the hybrid."]]]
 ];
 items.forEach(([title,tag,rows])=>{
  const d=document.createElement("details");d.className="qx";
  d.innerHTML="<summary>"+title+"<span class='tag2'>"+tag+"</span></summary>";
  const body=document.createElement("dl");body.className="qbody";
  rows.forEach(([q,a])=>{body.innerHTML+="<dt>"+q+"</dt><dd>"+a+"</dd>";});
  d.appendChild(body);QA.appendChild(d);
 });
}
})();
"""

s = s.replace("</script>\n</body>", JS + "\n</script>\n</body>")
io.open(P, "w", encoding="utf-8").write(s)
print("companion v2 JS injected; length", len(s))
