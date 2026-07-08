"""Iteration 14: upgrade the compendium HTML to companion v2.

Auditable record of every change: docs/ICML_READINESS_AUDIT.md sec. 4.
1. Corrected claims (LLM search parity at 40 seeds; CI-backed numbers).
2. Ledger rows for iterations 11-14; refreshed roadmap; counters.
3. Three new sections: protocol decision tree (4b), generation
   walkthrough (2.2), benchmark Q&A matrix (5b) — content injected by
   companion_v2.js appended before </body>.
Idempotent via COMPANION-V2 marker.
"""

import io
import sys

P = "deliverables/PRISM_Research_Compendium.html"
s = io.open(P, encoding="utf-8").read()
if "COMPANION-V2" in s:
    sys.exit("already patched")


def sub(old, new):
    global s
    assert old in s, "NOT FOUND: " + old[:70]
    s = s.replace(old, new)


sub("Nine algorithm versions, twelve experiments, two falsified",
    "Twelve algorithm versions, fourteen experiments, two falsified")
sub('<div class="key"><div class="v" data-count="9">0</div><div class="k">algorithm versions, each a git tag, each bit-for-bit reproducible</div></div>',
    '<div class="key"><div class="v" data-count="12">0</div><div class="k">algorithm versions, each a git tag, each bit-for-bit reproducible</div></div>')
sub("experiments (A–L), incl. 2 falsifications",
    "experiments (A–N), incl. 2 falsifications")
sub("RESEARCH COMPENDIUM · v1.0 · JULY 2026",
    "RESEARCH COMPENDIUM · v2.0 · JULY 2026 <!--COMPANION-V2-->")
sub("tags iteration-02 … iteration-10",
    "tags iteration-02 … iteration-14")

# --- corrected LLM claim in Figure 9 caption ---
sub("""FDC = −0.346 → search beats random. Both held: PRISM found an exact
optimum in mean 6 distinct evaluations vs random's 18, 15/15
seeds.</figcaption></figure>""",
    """FDC = −0.346 → searchable structure. At 40 seeds all methods find an
exact optimum comparably fast (PRISM 9.9 [7,13] distinct evaluations vs
random 10.8 [8,14] — an earlier 15-seed “3× faster” reading did not
survive the larger seed count and is corrected here). The payload is the
90-point ordering effect and the validated forecasts, not search
superiority on a friendly landscape.</figcaption></figure>""")

sub('note:"PRISM: 6 evals · random: 18"',
    'note:"all methods ≈10 evals (40-seed CIs overlap)"')

# --- Figure 10 caption: CI-backed aging + Experiment N ---
sub("""predicts for FDC ≈ 0. On structured landscapes elitist PRISM stays
fastest (18.5 vs 28.7 evals, XOR n=6). A BANANAS-style positional
surrogate wins only where its encoding matches the landscape (the LLM
chain). Result: a guideline, not a silver bullet — and aging is the safe
default when the pre-flight is skipped.</figcaption></figure>""",
    """predicts for FDC ≈ 0 (40-seed Wilson CIs: aging [0.62,0.88] vs elitist
[0.33,0.63]; random [0.60,0.86] overlaps aging — robustness recovered,
superiority not claimed). The stronger Experiment-N result: a
<b>precedence-encoded surrogate</b> reaches kendall n=7’s single
optimum-in-5040 in 14.8 evaluations [14,15] vs elitist 54.2 [50,59] —
non-overlapping CIs — while random finds it 2/40 times. Encoding must
match the landscape, exactly parallel to operator matching. Aging remains
the safe default when the pre-flight is skipped.</figcaption></figure>""")

# --- ledger rows ---
anchor = '<tr><td>Aging / surrogate improve robustness (literature)</td><td>10</td><td class="part">Aging: 48→78% (= random); guideline D15</td></tr>'
sub(anchor, anchor + """
<tr><td>Harder LLM instance (n=8, 40,320 orderings) discriminates</td><td>11</td><td class="part">Ordering effect grows (0.10→1.00); sampled pre-flight correctly forecast saturation (D16)</td></tr>
<tr><td>H17 · hybrid dominates both regimes / H18 · precedence surrogate</td><td>12</td><td class="ok">H17 partial (never worst); H18 confirmed — 14.8 vs 54.2 evals, CIs disjoint (D17)</td></tr>
<tr><td>Headline claims survive 40-seed CIs + pre-flight error bounds</td><td>14</td><td class="part">Kendall/aging/falsifications hold; LLM “3× faster” corrected to parity</td></tr>""")

# --- roadmap card refresh ---
old3 = '<span class="tag">ITERATION 11 · LEAD</span><div class="t">Harder LLM instance</div>'
assert old3 in s
start = s.index(old3)
card_end = s.index("</div></div>", start) + len("</div></div>")
s = (s[:start]
     + '<span class="tag">DONE · IT-11–14</span><div class="t">Harder LLM · surrogates · submission draft · statistics pass</div>'
       '<div class="d">n=8 instance run ($5.56, sampled pre-flight validated at scale); precedence surrogate shipped (D17); '
       'paper in submission form with Appendix A + 40-seed CIs; ICML-readiness audit on record.</div></div>'
     + s[card_end:])

# --- new sections ---
tree_html = """
<!-- ============ 4b PROTOCOL TREE ============ -->
<section id="s4b" class="rv" data-toc="4b|The protocol — try it">
<h2><span class="num">4b</span>The PRISM Protocol as a decision tree — click through it</h2>
<p class="dim">The program’s practical output. Each branch shows the measured
reliability of that call from the Iteration-14 error study (200 resampled
pre-flights at realistic sample sizes: 100 move-pairs per operator, 200
FDC points). Click an answer to walk a case.</p>
<div id="tree" style="background:var(--surface);border:1px solid var(--border);padding:18px;max-width:52rem"></div>
</section>
"""
sub("<!-- ============ 5 LEDGER ============ -->",
    tree_html + "\n<!-- ============ 5 LEDGER ============ -->")

walk_html = """
<h3><span class="num">2.2</span>One generation, step by step</h3>
<p>Six of the twenty population slots, with real fitness values from the
enumerated XOR-v4 landscape. Step through the loop:</p>
<figure><div><button class="tbtn" id="wnext">Next step ▸</button>
<button class="treset" id="wreset">restart</button></div>
<div id="walk"></div><div class="wmsg" id="wmsg"></div>
<figcaption><b>Figure 2b</b> — Interactive walkthrough of one PRISM
generation. Elitism copies the best unchanged; each remaining slot is
filled by a tournament of three and, occasionally, a mutation.</figcaption></figure>
"""
sub("</section>\n\n<!-- ============ 3 THEORY ============ -->",
    walk_html + "</section>\n\n<!-- ============ 3 THEORY ============ -->")

qa_html = """
<!-- ============ 5b BENCHMARK QA ============ -->
<section id="s5b" class="rv" data-toc="5b|Benchmark Q&amp;A">
<h2><span class="num">5b</span>Every benchmark, interrogated</h2>
<p class="dim">The questions a reviewer asks — what is it, why chosen, what it
measures, baselines, comparability, where PRISM wins and loses, why, and
what would strengthen it — answered per experiment family. Click to expand.</p>
<div id="qa"></div>
</section>
"""
sub("<!-- ============ 6 COST ============ -->",
    qa_html + "\n<!-- ============ 6 COST ============ -->")

# --- CSS ---
css_add = """
/* ---------- decision tree / walkthrough / QA (companion v2) ---------- */
.tnode{margin:10px 0;padding:12px 16px;border-left:3px solid var(--accent);background:var(--def)}
.tnode .q{font-weight:bold}
.tbtn{display:inline-block;margin:8px 10px 2px 0;padding:6px 14px;border:1px solid var(--accent);
  color:var(--accent);background:none;cursor:pointer;font:inherit;font-size:.85rem}
.tbtn:hover{background:var(--accent);color:#fff}
.tverdict{border-left-color:var(--good);background:var(--thm)}
.tverdict.bad{border-left-color:var(--bad);background:var(--neg)}
.treset{font-size:.75rem;color:var(--muted);cursor:pointer;border:none;background:none;
  text-decoration:underline;font-family:inherit;padding:0;margin-top:10px}
.trel{font-family:ui-monospace,monospace;font-size:.7rem;color:var(--muted);display:block;margin-top:4px}
.wrow{display:flex;gap:8px;align-items:stretch;flex-wrap:wrap;margin:8px 0}
.wslot{width:108px;padding:6px;border:1px solid var(--border);background:var(--page);
  font-family:ui-monospace,monospace;font-size:.68rem;text-align:center;transition:all .4s}
.wslot .f{color:var(--muted)}
.wslot.elite{border-color:var(--good);box-shadow:0 0 0 1px var(--good)}
.wslot.win{border-color:var(--accent);box-shadow:0 0 0 1px var(--accent)}
.wslot.mut{border-color:var(--adaptive);box-shadow:0 0 0 1px var(--adaptive)}
.wmsg{font-family:Helvetica,Arial,sans-serif;font-size:.85rem;color:var(--ink2);min-height:2.6em;margin-top:8px}
details.qx{border:1px solid var(--border);background:var(--surface);margin:8px 0;max-width:52rem}
details.qx summary{padding:10px 14px;cursor:pointer;font-weight:bold;font-size:.95rem}
details.qx summary .tag2{font-family:ui-monospace,monospace;font-size:.65rem;color:var(--muted);margin-left:8px}
details.qx .qbody{padding:0 16px 12px;font-family:Helvetica,Arial,sans-serif;font-size:.8rem;color:var(--ink2)}
details.qx .qbody dt{font-weight:600;color:var(--ink);margin-top:8px}
details.qx .qbody dd{margin:2px 0 0 0}
"""
sub("@media (prefers-reduced-motion: reduce){",
    css_add + "@media (prefers-reduced-motion: reduce){")

io.open(P, "w", encoding="utf-8").write(s)
print("companion v2 structure applied; length", len(s))
