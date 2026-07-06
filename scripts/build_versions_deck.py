"""Build deliverables/PRISM_Versions_Deck.pptx — one deck walking the
algorithm/research versions (git tags iteration-02 .. iteration-05, with
the Iteration-6 outlook), one chapter per version: what changed, key
results, honest failures. Reuses the visual helpers of
build_research_paper_and_ppt.py (Iteration 6 artifact).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_research_paper_and_ppt import (  # noqa: E402
    Presentation, Inches, Pt, RGBColor, PP_ALIGN,
    TOL_BLUE, TOL_GREEN, TOL_YELLOW, TOL_PURPLE, TOL_RED, TOL_GREY,
    add_title, add_bullets, add_footer, add_bar, DELIVERABLES,
)

OUT = DELIVERABLES / "PRISM_Versions_Deck.pptx"

VERSIONS = [
    ("iteration-02", "Rebuild and Reproduce", TOL_BLUE, [
        "Situation: handover described a codebase that did not exist on disk",
        "Rebuilt from the surviving notebook: seeded, deterministic, documented",
        "All 5 headline benchmark results reproduced (XOR/OR/AND/parity 100%, poly MSE 0.0070)",
        "First multi-size test of the O(n^3 log n) theorem: exponents 2.9-3.1 (n >= 6)",
        "Corrections logged: order matters 4/5, noisy best-ever fitness, positions 3-4 unused",
    ]),
    ("iteration-03", "Operator-Landscape Matching", TOL_GREEN, [
        "Added insert / inversion / scramble mutations (swap default, bit-for-bit compatible)",
        "Added adjacency (R-type) and deceptive synthetic landscapes",
        "H1 CONFIRMED 3/3: literature-matched operator best on every landscape type",
        "Mismatch on plateau-rich landscapes = 100% censoring by n=12-16 (hard failure)",
        "Deceptive landscape defeats all operators: polynomial time is landscape-conditional",
        "Honest failure: depth-based benchmark redesign (v3) falsified - all orderings untrainable",
    ]),
    ("iteration-04", "The Operator Portfolio", TOL_PURPLE, [
        "mutation='portfolio': uniform random operator per mutation event",
        "Solves every landscape, every size, zero censoring, zero configuration",
        "Overhead vs matched operator only 1.1-4.1x (vs unbounded failure if you guess wrong)",
        "mutation='adaptive': learns weights; identifies the matched operator 3/3",
        "But adaptive does not consistently beat uniform - relegated to landscape diagnosis",
        "Decision D8: portfolio is the recommended default for unknown landscapes",
    ]),
    ("iteration-05", "Ground Truth and the Story So Far", TOL_YELLOW, [
        "Benchmark v4: residual blocks + permutation-seeded init (deterministic, all positions used)",
        "All 120 orderings enumerated: XOR optimum 8/120, parity optimum 2/120",
        "PRISM hit rate: XOR 100%, parity 40% (mean regret 0.033) - exact statistics",
        "Paper updated through Iteration 5; animated HTML research log shipped",
        "Decision D9: v4 is the canonical toy benchmark; risk R10 closed",
    ]),
    ("iteration-06", "Outlook", TOL_RED, [
        "Scale v4 beyond n=5: enumeration at n=6, regret-vs-baseline at n=7",
        "Versions deck + multi-level audio lessons + Notion tracker (this iteration)",
        "Then: LLM reasoning-chain ordering, portfolio on deceptive landscapes",
        "Publication target: operator story + scaling + ground-truth benchmarks",
    ]),
]


def build():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]
    idx = 1

    # Title slide
    slide = prs.slides.add_slide(blank)
    add_title(slide, "PRISM: The Versions",
              "One chapter per algorithm/research version - git tags iteration-02 .. iteration-05")
    add_bullets(slide, [
        "Each version is a git tag; default parameters reproduce the previous version bit-for-bit",
        "Compare any two: git diff iteration-02..iteration-05",
        "Full lab logs in iterations/, living handover in docs/HANDOVER.md",
    ], y=1.7, w=11.7)
    bar = slide.shapes.add_shape(1, Inches(0.58), Inches(6.35), Inches(12.1), Inches(0.18))
    bar.fill.solid(); bar.fill.fore_color.rgb = TOL_BLUE; bar.line.color.rgb = TOL_BLUE
    add_footer(slide, idx); idx += 1

    # Timeline slide
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Version Timeline", "2026-07-05 .. 2026-07-06")
    labels = [v[0].replace("iteration-", "it-") + "\n" + v[1] for v in VERSIONS]
    for i, (tag, name, color, _) in enumerate(VERSIONS):
        x = 0.7 + i * 2.5
        shp = slide.shapes.add_shape(1, Inches(x), Inches(3.2), Inches(2.1), Inches(1.1))
        shp.fill.solid(); shp.fill.fore_color.rgb = color
        shp.line.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        tf = shp.text_frame; tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tag
        p.alignment = PP_ALIGN.CENTER
        p.runs[0].font.size = Pt(13); p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        p2 = tf.add_paragraph(); p2.text = name
        p2.alignment = PP_ALIGN.CENTER
        p2.runs[0].font.size = Pt(10)
        p2.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    add_footer(slide, idx); idx += 1

    # One chapter slide per version
    for tag, name, color, bullets in VERSIONS:
        slide = prs.slides.add_slide(blank)
        add_title(slide, f"{tag} - {name}")
        add_bullets(slide, bullets, w=11.7, size=16)
        stripe = slide.shapes.add_shape(1, Inches(0.0), Inches(0.0), Inches(0.18), Inches(7.5))
        stripe.fill.solid(); stripe.fill.fore_color.rgb = color; stripe.line.color.rgb = color
        add_footer(slide, idx); idx += 1

    # Numbers slide: hitting time at n=16 (log-ish comparison via bars)
    slide = prs.slides.add_slide(blank)
    add_title(slide, "One Number Per Version",
              "mean generations to optimum at n=16 (lower is better; 10000 = censored cap)")
    add_bullets(slide, [
        "Fixed matched operator (it-03): hamming 405, kendall 396, adjacency 1199",
        "Any mismatched fixed operator: 10000 (100% of runs censored)",
        "Portfolio (it-04): 1140 / 501 / 1915 - never fails, never configured",
        "v4 ground truth (it-05): search quality measured exactly (hit rate, regret)",
    ], w=11.7)
    add_bar(slide, "match", 405, 10000, 4.2, TOL_GREEN)
    add_bar(slide, "portf", 1140, 10000, 4.75, TOL_PURPLE)
    add_bar(slide, "wrong", 10000, 10000, 5.3, TOL_RED)
    add_footer(slide, idx); idx += 1

    # Hypothesis ledger
    slide = prs.slides.add_slide(blank)
    add_title(slide, "Hypothesis Ledger", "every hypothesis, including the falsified ones")
    add_bullets(slide, [
        "Reproduction (it-02): CONFIRMED with 3 corrections",
        "H1 operator matching (it-03): CONFIRMED 3/3",
        "H2 deceptive breaks polynomial time (it-03): CONFIRMED",
        "H3 deeper networks use all positions (it-03): FALSIFIED - all orderings untrainable",
        "H4 portfolio succeeds everywhere <= 4x (it-04): CONFIRMED",
        "H5 adaptive beats uniform (it-04): learning yes, speedup no",
        "H6-H8 v4 trainable / deterministic / order-sensitive (it-05): CONFIRMED",
    ], w=11.7, size=16)
    add_footer(slide, idx); idx += 1

    prs.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
