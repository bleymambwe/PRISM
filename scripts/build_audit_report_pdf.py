"""Render docs/EXPERIMENTS_AUDIT_REPORT_2026-07-12.md to PDF via reportlab.

Same no-LaTeX approach as build_research_paper_and_ppt.py (this machine has
no TeX). Generic subset of Markdown: #/##/### headings, bullet lists, pipe
tables, fenced code blocks, bold / inline code, horizontal rules.

Usage: python scripts/build_audit_report_pdf.py
"""

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    ListFlowable, ListItem, Paragraph, Preformatted, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs" / "EXPERIMENTS_AUDIT_REPORT_2026-07-12.md"
OUT = ROOT / "docs" / "EXPERIMENTS_AUDIT_REPORT_2026-07-12.pdf"

BLUE = colors.HexColor("#2a5da8")
GREEN = colors.HexColor("#1e7a3a")


def inline(text):
    text = (text.replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;"))
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    text = re.sub(r"`([^`]+)`",
                  r"<font name='Courier' size='8'>\1</font>", text)
    return text


def build():
    styles = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=styles["Title"], fontSize=17,
                           leading=21, textColor=BLUE, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading1"], fontSize=13,
                        leading=16, textColor=BLUE, spaceBefore=12,
                        spaceAfter=5)
    h3 = ParagraphStyle("H3", parent=styles["Heading2"], fontSize=11,
                        leading=14, textColor=GREEN, spaceBefore=9,
                        spaceAfter=4)
    body = ParagraphStyle("B", parent=styles["BodyText"], fontSize=9,
                          leading=12.5, spaceAfter=4)
    cell = ParagraphStyle("C", parent=body, fontSize=7.5, leading=9.5,
                          spaceAfter=0)
    code = ParagraphStyle("P", parent=styles["Code"], fontSize=7.5,
                          leading=9.5, leftIndent=10, spaceAfter=6)

    lines = SRC.read_text(encoding="utf-8").splitlines()
    story = []
    i = 0
    bullets = []

    def flush_bullets():
        nonlocal bullets
        if bullets:
            story.append(ListFlowable(
                [ListItem(Paragraph(inline(b), body), leftIndent=14)
                 for b in bullets],
                bulletType="bullet", start="circle", leftIndent=10))
            story.append(Spacer(1, 4))
            bullets = []

    while i < len(lines):
        ln = lines[i]
        s = ln.strip()
        if s.startswith("```"):
            flush_bullets()
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            story.append(Preformatted("\n".join(block), code))
            i += 1
            continue
        if s.startswith("|"):
            flush_bullets()
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in
                         lines[i].strip().strip("|").split("|")]
                if not all(set(c) <= {"-", ":", " "} for c in cells):
                    rows.append([Paragraph(inline(c), cell) for c in cells])
                i += 1
            if rows:
                ncols = len(rows[0])
                width = (A4[0] - 90) / max(ncols, 1)
                t = Table(rows, colWidths=[width] * ncols, repeatRows=1)
                t.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0),
                     colors.HexColor("#e8eef8")),
                    ("GRID", (0, 0), (-1, -1), 0.4,
                     colors.HexColor("#b9c4d6")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 2),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                ]))
                story.append(t)
                story.append(Spacer(1, 6))
            continue
        if s.startswith("# ") and not story:
            story.append(Paragraph(inline(s[2:]), title))
        elif s.startswith("### "):
            flush_bullets()
            story.append(Paragraph(inline(s[4:]), h3))
        elif s.startswith("## "):
            flush_bullets()
            story.append(Paragraph(inline(s[3:]), h2))
        elif s.startswith("# "):
            flush_bullets()
            story.append(Paragraph(inline(s[2:]), h2))
        elif s in ("---", "***"):
            flush_bullets()
            story.append(Spacer(1, 6))
        elif s.startswith(("- ", "* ")):
            bullets.append(s[2:])
        elif re.match(r"^\d+\.\s", s):
            bullets.append(re.sub(r"^\d+\.\s", "", s))
        elif s.startswith("> "):
            flush_bullets()
            story.append(Paragraph(inline(s[2:]), body))
        elif s:
            # continuation of a bullet? markdown soft-wraps use 2-space indent
            if bullets and ln.startswith("  "):
                bullets[-1] += " " + s
            else:
                flush_bullets()
                story.append(Paragraph(inline(s), body))
        else:
            flush_bullets()
        i += 1
    flush_bullets()

    doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=45,
                            rightMargin=45, topMargin=48, bottomMargin=48,
                            title="PRISM Experiments Audit Report")
    doc.build(story)
    print(f"wrote {OUT} ({OUT.stat().st_size:,} bytes)")


if __name__ == "__main__":
    build()
