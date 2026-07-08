"""Build current PRISM paper PDF and PPTX deliverables.

This script avoids a LaTeX dependency so it works on the current Windows
machine. It uses reportlab for the paper PDF and python-pptx for the deck.
The Markdown sources remain the editable canonical drafts.
"""

from pathlib import Path
import re

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Inches, Pt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DELIVERABLES = ROOT / "deliverables"
PAPER_MD = DELIVERABLES / "PRISM_Framework_Research_Paper.md"
PAPER_PDF = DELIVERABLES / "PRISM_Framework_Research_Paper.pdf"
PPTX = DELIVERABLES / "PRISM_Framework_Presentation.pptx"
RL_GAPS = ROOT / "prism-research" / "outputs" / "rl_ordering_gaps.png"

TOL_BLUE = RGBColor(0x44, 0x77, 0xAA)
TOL_RED = RGBColor(0xEE, 0x66, 0x77)
TOL_GREEN = RGBColor(0x22, 0x88, 0x33)
TOL_YELLOW = RGBColor(0xCC, 0xBB, 0x44)
TOL_PURPLE = RGBColor(0xAA, 0x33, 0x77)
TOL_GREY = RGBColor(0xBB, 0xBB, 0xBB)


def clean_inline(text):
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    return text


def parse_table(lines, start):
    table_lines = []
    i = start
    while i < len(lines) and lines[i].strip().startswith("|"):
        table_lines.append(lines[i].strip())
        i += 1
    rows = []
    for idx, line in enumerate(table_lines):
        cells = [c.strip() for c in line.strip("|").split("|")]
        if idx == 1 and all(set(c) <= {"-", ":"} for c in cells):
            continue
        rows.append(cells)
    return rows, i


def build_paper_pdf():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="PaperTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#4477AA"),
        spaceAfter=16,
    ))
    styles.add(ParagraphStyle(
        name="PaperH1",
        parent=styles["Heading1"],
        fontSize=14,
        leading=17,
        textColor=colors.HexColor("#4477AA"),
        spaceBefore=12,
        spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="PaperH2",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#228833"),
        spaceBefore=10,
        spaceAfter=6,
    ))
    body = ParagraphStyle(
        name="PaperBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        spaceAfter=6,
    )
    code = ParagraphStyle(
        name="PaperCode",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8.2,
        leading=10,
        backColor=colors.HexColor("#F5F8FA"),
        borderColor=colors.HexColor("#BBBBBB"),
        borderWidth=0.25,
        borderPadding=5,
        spaceAfter=8,
    )

    # Figures injected after matching headings (generated from the
    # committed experiment CSVs by scripts/build_book_figures.py)
    figdir = DELIVERABLES / "book_figures"
    cap_style = ParagraphStyle(name="FigCap", parent=body, fontSize=8,
                               leading=10.5,
                               textColor=colors.HexColor("#666460"),
                               spaceBefore=2, spaceAfter=10)
    FIGURE_MAP = {
        "1. Introduction": [
            ("fig_concept.png", "Figure 1: the same fixed components in "
             "two orders — ordering alone separates success from "
             "failure on the benchmarks of Section 5.", 6.2)],
        "4. Algorithm": [
            ("fig_loop.png", "Figure 2: one PRISM generation.", 6.2),
            ("fig_moves.png", "Figure 3: the four mutation operators; "
             "each induces a different neighborhood over orderings.",
             6.2)],
        "5. Theoretical Framing": [
            ("fig_markov.png", "Figure 4: transient states drain into "
             "the absorbing set; elitism seals it.", 6.0)],
        "6.2 Synthetic runtime scaling": [
            ("fig_scaling.png", "Figure 5: measured hitting times vs "
             "the n³ log n shape (Iteration 2).", 4.6)],
        "6.3 Operator-landscape matching (requirement, not preference)": [
            ("fig_operators.png", "Figure 6: matched operators (bold) "
             "vs mismatch climbing into the censoring cap.", 6.4)],
        "6.4 The operator portfolio": [
            ("fig_portfolio.png", "Figure 7: matched vs portfolio at "
             "n=16; dashed line = mismatched-operator failure.", 5.2),
            ("fig_adaptive.png", "Figure 8: adaptive mode's learned "
             "weights identify the matched operator 3/3.", 6.0)],
        "6.5 Ground truth by construction": [
            ("fig_landscapes.png", "Figure 9: three exactly enumerated "
             "landscapes; dashed line = global optimum.", 6.4),
            ("fig_trajectories.png", "Figure 10: convergence "
             "trajectories — plateaus, jumps, elitism-enforced "
             "monotonicity.", 5.4)],
        "6.6 The honest boundary and the pre-flight diagnostic": [
            ("fig_n7_honest.png", "Figure 11: n=7 — tuning fixes "
             "exploration (left) but random matches PRISM's quality "
             "anyway (right).", 6.2),
            ("fig_locality.png", "Figure 12: ρ1 per operator and "
             "FDC reproduce all observed outcomes pre-search.", 6.4)],
        "6.7 Application: LLM reasoning-chain ordering": [
            ("fig_llm.png", "Figure 13: position effects and the full "
             "enumerated LLM landscape (6.3%–96.9% by order "
             "alone).", 6.4),
            ("fig_llm_search.png", "Figure 14: distinct evaluations to "
             "the first exact optimum.", 4.2)],
        "6.8 Method selection beyond operators: replacement and surrogates": [
            ("fig_surrogate.png", "Figure 15: the precedence surrogate "
             "reaches kendall's single optimum 4x faster than elitist "
             "search (left) and is tied-best for robustness on parity "
             "(right).", 6.2)],
        "11. Conclusion": [
            ("fig_arc.png", "Figure 16: the research arc — including "
             "the falsifications.", 6.4)],
    }

    def inject_figures(heading):
        for fname, cap, w in FIGURE_MAP.get(heading, []):
            fp = figdir / fname
            if not fp.exists():
                continue
            img = Image(str(fp))
            ratio = img.imageHeight / img.imageWidth
            img.drawWidth = w * inch
            img.drawHeight = w * ratio * inch
            story.append(Spacer(1, 4))
            story.append(img)
            story.append(Paragraph(cap, cap_style))

    lines = PAPER_MD.read_text(encoding="utf-8").splitlines()
    story = []
    current_section = [""]
    i = 0
    in_code = False
    code_lines = []

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if stripped.startswith("```"):
            if in_code:
                story.append(Preformatted("\n".join(code_lines), code))
                code_lines = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        if in_code:
            code_lines.append(line)
            i += 1
            continue
        if not stripped:
            story.append(Spacer(1, 4))
            i += 1
            continue
        if stripped.startswith("|"):
            rows, i = parse_table(lines, i)
            table = Table(rows, repeatRows=1)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DDE8F2")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#222222")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#BBBBBB")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(table)
            story.append(Spacer(1, 8))
            continue
        if stripped.startswith("# "):
            story.append(Paragraph(clean_inline(stripped[2:]), styles["PaperTitle"]))
        elif stripped.startswith("## "):
            inject_figures(current_section[0])
            current_section[0] = stripped[3:].strip()
            story.append(Paragraph(clean_inline(stripped[3:]), styles["PaperH1"]))
        elif stripped.startswith("### "):
            inject_figures(current_section[0])
            current_section[0] = stripped[4:].strip()
            story.append(Paragraph(clean_inline(stripped[4:]), styles["PaperH2"]))
        elif stripped.startswith("- "):
            items = []
            while i < len(lines) and lines[i].strip().startswith("- "):
                item_text = clean_inline(lines[i].strip()[2:])
                items.append(ListItem(Paragraph(item_text, body), leftIndent=12))
                i += 1
            story.append(ListFlowable(items, bulletType="bullet", leftIndent=18))
            continue
        else:
            story.append(Paragraph(clean_inline(stripped), body))
        i += 1

    inject_figures(current_section[0])
    if RL_GAPS.exists():
        story.append(PageBreak())
        story.append(Paragraph("Appendix Figure: PRISM-RL Gaps", styles["PaperH1"]))
        story.append(Image(str(RL_GAPS), width=6.0 * inch, height=3.2 * inch))

    doc = SimpleDocTemplate(
        str(PAPER_PDF),
        pagesize=A4,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title="PRISM Framework Research Paper",
        author="Blessings Mambwe",
    )
    doc.build(story)


def set_run_font(run, size=18, color=RGBColor(0x22, 0x22, 0x22), bold=False):
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.name = "Aptos"


def add_title(slide, title, subtitle=None):
    box = slide.shapes.add_textbox(Inches(0.55), Inches(0.35), Inches(12.2), Inches(0.7))
    p = box.text_frame.paragraphs[0]
    p.text = title
    p.alignment = PP_ALIGN.LEFT
    p.runs[0].font.size = Pt(28)
    p.runs[0].font.bold = True
    p.runs[0].font.color.rgb = TOL_BLUE
    if subtitle:
        sub = slide.shapes.add_textbox(Inches(0.58), Inches(1.02), Inches(11.8), Inches(0.35))
        sp = sub.text_frame.paragraphs[0]
        sp.text = subtitle
        sp.runs[0].font.size = Pt(12)
        sp.runs[0].font.color.rgb = RGBColor(0x55, 0x55, 0x55)


def add_bullets(slide, bullets, x=0.75, y=1.45, w=6.0, h=4.5, size=18):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.clear()
    for idx, bullet in enumerate(bullets):
        p = tf.paragraphs[0] if idx == 0 else tf.add_paragraph()
        p.text = bullet
        p.level = 0
        p.space_after = Pt(7)
        p.runs[0].font.size = Pt(size)
        p.runs[0].font.color.rgb = RGBColor(0x22, 0x22, 0x22)


def add_footer(slide, index):
    box = slide.shapes.add_textbox(Inches(11.7), Inches(7.05), Inches(1.0), Inches(0.25))
    p = box.text_frame.paragraphs[0]
    p.text = str(index)
    p.alignment = PP_ALIGN.RIGHT
    p.runs[0].font.size = Pt(9)
    p.runs[0].font.color.rgb = TOL_GREY


def add_bar(slide, label, value, max_value, y, color):
    x0 = Inches(7.1)
    wmax = Inches(4.8)
    h = Inches(0.28)
    slide.shapes.add_textbox(Inches(6.2), Inches(y), Inches(0.8), h).text = label
    bg = slide.shapes.add_shape(1, x0, Inches(y), wmax, h)
    bg.fill.solid()
    bg.fill.fore_color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
    bg.line.color.rgb = RGBColor(0xEE, 0xEE, 0xEE)
    fg = slide.shapes.add_shape(1, x0, Inches(y), int(wmax * value / max_value), h)
    fg.fill.solid()
    fg.fill.fore_color.rgb = color
    fg.line.color.rgb = color
    val = slide.shapes.add_textbox(Inches(12.0), Inches(y - 0.03), Inches(0.7), Inches(0.3))
    p = val.text_frame.paragraphs[0]
    p.text = f"{value:g}"
    p.runs[0].font.size = Pt(10)


def build_pptx():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    slides = [
        ("PRISM", "Permutation-Based Reasoning and Intelligence Search",
         ["A framework for optimizing the order of fixed components",
          "Core loop: ordering, tournament selection, mutation, elitism",
          "Current evidence: neural toys, synthetic scaling, PRISM-RL proof of concept"]),
        ("When Order Matters", None,
         ["Neural modules can be fixed while their execution order is unknown",
          "Curricula and options in RL are naturally order-sensitive",
          "Compiler passes, reasoning chains, and tool pipelines share this structure"]),
        ("Core Idea", None,
         ["Represent each candidate as a permutation pi in S_n",
          "Evaluate the ordered system with a task-specific fitness function",
          "Search the finite space using evolutionary pressure"]),
        ("PRISM Algorithm Loop", None,
         ["Initialize a population of random permutations",
          "Evaluate all candidates",
          "Preserve elite candidates",
          "Tournament-select parents and mutate children",
          "Return the best ordering observed"]),
        ("Theoretical Lens", None,
         ["Finite Markov chain over populations of permutations",
          "With nonzero mutation, optima remain reachable",
          "With elitism, populations containing an optimum are absorbing",
          "Project theory records O(n^3 log n) expected runtime under assumptions"]),
        ("Evidence Map", None,
         ["Neural toy validation: headline results reproduce (Iteration 2)",
          "Synthetic scaling: consistent with n^3 log n to n = 16 (Iterations 2-3)",
          "Operator study COMPLETE: matching confirmed 3/3 landscapes (Iteration 3)",
          "Operator portfolio automates the choice at <= 4.1x cost (Iteration 4)",
          "Benchmark v4: exact enumerated ground truth, honest hit rates (Iteration 5)",
          "PRISM-RL: options and curricula can be optimized as permutations"]),
        ("Toy Neural Validation", None,
         ["XOR, OR, AND, and 3-bit parity reach 1.0000 best fitness",
          "Polynomial regression reproduces near reference MSE",
          "Important correction: original toys use only part of the permutation"]),
        ("Synthetic Runtime Scaling", None,
         ["Hamming exponent: 3.73 over all tested n; 3.14 excluding n <= 5",
          "Kendall exponent: 3.68 over all tested n; 2.89 excluding n <= 5",
          "E[T] / (n^3 log n) remains in a narrow empirical band"]),
        ("Operator-Landscape Matching (Confirmed 3/3)", None,
         ["Swap wins absolute-position: 405 gens at n=16; all others 100% censored",
          "Insert wins precedence: 396 at n=16; smooth landscape forgives mismatch",
          "Inversion wins adjacency: 1199 at n=16; all others 100% censored",
          "Mismatch on plateau-rich landscapes is hard failure, not slowdown",
          "Deceptive landscape defeats every operator: runtime bound is conditional"]),
        ("Operator Portfolio (Iteration 4)", None,
         ["Uniform random operator per mutation event - zero configuration",
          "Solves every landscape at every size, zero censoring, n <= 16",
          "Overhead vs matched operator: 1.1x to 4.1x (vs unbounded failure)",
          "Adaptive weights identify the matched operator 3/3 - landscape diagnosis",
          "Recommendation: matched operator if type known, else portfolio"]),
        ("Benchmark v4: Exact Ground Truth (Iteration 5)", None,
         ["Five permuted residual bottleneck blocks - every position functional",
          "Weight init seeded from the permutation: deterministic fitness",
          "All 120 orderings enumerated: XOR optimum 8/120, parity 2/120",
          "PRISM hit rate: XOR 100%, parity 40% with mean regret 0.033",
          "Search quality is now an exact statistic, not best-observed noise"]),
        ("PRISM-RL Framing", None,
         ["PRISM is not a low-level RL control algorithm",
          "It is a meta-level optimizer for finite RL orderings",
          "Examples: option order, curriculum order, subgoal order, module order"]),
        ("PRISM-RL Results", None,
         ["Option route grid: inversion improves mean gap from 5.50 to 1.75",
          "Chain curriculum: insert reaches exact optimum in 100% of runs",
          "Random search remains strong on small 6! curriculum space"]),
        ("What Customization Means", None,
         ["Fitness wrapper: converts an RL rollout or training run into F(pi)",
          "Mutation choice: optional domain-aligned search operator",
          "Noise handling: future stochastic RL needs repeated rollouts or elite reevaluation"]),
        ("Limitations", None,
         ["Polynomial time is landscape-conditional: deceptive landscapes defeat all operators",
          "v4 benchmarks fix noise and unused positions, but remain small (n = 5)",
          "Synthetic landscapes are idealized single-type instances",
          "PRISM-RL benchmarks are feasibility tests, not competitive RL claims",
          "Operator classification cited from secondary synthesis - primary sources pending"]),
        ("Next Experiments", None,
         ["Scale benchmark v4 beyond n = 5 (regret vs best-known)",
          "Apply PRISM to LLM reasoning-chain ordering (precedence-type)",
          "Portfolio on deceptive landscapes; UCB-style adaptive credit",
          "Scale PRISM-RL to stochastic gridworld option ordering"]),
        ("Takeaway", None,
         ["PRISM isolates ordering as a reusable scientific search surface",
          "The same core loop transfers across neural, synthetic, and RL settings",
          "The strongest next contribution is principled mutation selection plus noise-aware evaluation"]),
    ]

    for idx, (title, subtitle, bullets) in enumerate(slides, start=1):
        slide = prs.slides.add_slide(blank)
        add_title(slide, title, subtitle)
        add_bullets(slide, bullets, w=5.6 if title in {"PRISM-RL Results", "Synthetic Runtime Scaling"} else 11.7)
        if title == "PRISM":
            shape = slide.shapes.add_shape(1, Inches(0.58), Inches(6.35), Inches(12.1), Inches(0.18))
            shape.fill.solid()
            shape.fill.fore_color.rgb = TOL_BLUE
            shape.line.color.rgb = TOL_BLUE
        if title == "PRISM Algorithm Loop":
            stages = ["Population", "Evaluate", "Elite", "Tournament", "Mutate"]
            for sidx, stage in enumerate(stages):
                x = 0.8 + sidx * 2.45
                shp = slide.shapes.add_shape(1, Inches(x), Inches(5.4), Inches(1.8), Inches(0.55))
                shp.fill.solid()
                shp.fill.fore_color.rgb = [TOL_BLUE, TOL_GREEN, TOL_YELLOW, TOL_PURPLE, TOL_RED][sidx]
                shp.line.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                p = shp.text_frame.paragraphs[0]
                p.text = stage
                p.alignment = PP_ALIGN.CENTER
                p.runs[0].font.size = Pt(12)
                p.runs[0].font.bold = True
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        if title == "PRISM-RL Results":
            add_bar(slide, "swap", 5.50, 8.5, 1.7, TOL_RED)
            add_bar(slide, "inv.", 1.75, 8.5, 2.25, TOL_GREEN)
            add_bar(slide, "rand", 8.50, 8.5, 2.8, TOL_GREY)
            if RL_GAPS.exists():
                slide.shapes.add_picture(str(RL_GAPS), Inches(6.35), Inches(3.45), width=Inches(6.0))
        if title == "Synthetic Runtime Scaling":
            add_bar(slide, "Ham.", 3.73, 4.0, 1.75, TOL_BLUE)
            add_bar(slide, "Ken.", 3.68, 4.0, 2.3, TOL_GREEN)
            add_bar(slide, "H n>=6", 3.14, 4.0, 2.85, TOL_YELLOW)
            add_bar(slide, "K n>=6", 2.89, 4.0, 3.4, TOL_PURPLE)
        add_footer(slide, idx)

    prs.save(PPTX)


def main():
    DELIVERABLES.mkdir(exist_ok=True)
    build_paper_pdf()
    build_pptx()
    print(f"Wrote {PAPER_PDF}")
    print(f"Wrote {PPTX}")


if __name__ == "__main__":
    main()
