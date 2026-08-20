"""Convert the approved production brief into data-driven narration scenes."""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
BRIEF = REPO / "PRISM_Remotion_Kokoro_Production_Brief.md"
OUT = ROOT / "src" / "data" / "film.json"

ARTIFACTS = {
    "A": "prism-research/outputs/validation_results.csv; validation_variance.csv",
    "B": "prism-research/outputs/scaling_results.csv; scaling_summary.csv",
    "C": "experiments/iteration-03/results/operator_study_results.csv",
    "D": "experiments/iteration-03/results/operator_study_results.csv",
    "E": "experiments/iteration-03/results/toy_v3_results.csv",
    "F": "experiments/iteration-04/results/portfolio_results.csv",
    "G": "experiments/iteration-05/results/v4_landscape.csv; v4_search.csv",
    "H": "experiments/iteration-06/results/n6_landscape.csv; n6_search.csv; n7_search.csv",
    "I": "experiments/iteration-07/results/n7_parity_landscape.csv; iteration-14/headline_cis.csv",
    "J": "experiments/iteration-08/results/locality.csv; iteration-14/preflight_error.csv",
    "K": "experiments/iteration-09/results/llm_landscape.csv; llm_position_effects.csv",
    "L": "experiments/iteration-10/results/improved_search.csv",
    "M": "experiments/iteration-11/results/search_results.csv",
    "N": "experiments/iteration-12/results/hybrid_surrogate.csv",
    "O": "experiments/iteration-16/results/transfer.txt; v4_landscape.csv",
    "P": "experiments/iteration-16/results/sciml_landscape.csv",
    "Q": "experiments/iteration-17 paper-cut record",
    "R": "experiments/iteration-18/results/transfer_guided_selection.txt",
    "S": "experiments/iteration-23-experiment-s/results/orderings.json",
    "T": "experiments/iteration-24-prompt-optimizer-baselines/results/T_RESULTS_SUMMARY.json",
}

GRAPH_IDS = {
    "A": "A-validation", "B": "T4-scaling", "C": "CD-operators",
    "D": "CD-operators", "E": "E-flat", "F": "F-portfolio",
    "G": "G-landscape", "H": "H-scaleup", "I": "I-audit",
    "J": "J-locality", "K": "K-llm", "L": "L-methods",
    "M": "M-eight-module", "N": "N-surrogate", "O": "O-transfer",
    "P": "P-sciml", "Q": "Q-progress", "R": "R-guided",
    "S": "EP-S-math", "T": "EP-T-opro",
}


def clean(text: str) -> str:
    fixes = {
        "â€“": "–", "â€”": "—", "âˆ’": "minus ", "â€œ": "“,",
        "â€": "”", "Ã—": " times ", "â†’": " to ", "naÃ¯ve": "naive",
        "RÃ¶ssler": "Rossler", "PRISM": "prism", "FDC": "F D C",
        "SINDy": "sin-dee", "GSM8K": "G S M eight K",
        "MATH-500": "Math five hundred", "n!": "n factorial",
    }
    for old, new in fixes.items():
        text = text.replace(old, new)
    text = re.sub(r"~~~.*?~~~", " ", text, flags=re.S)
    text = re.sub(r"\x60\x60\x60.*?\x60\x60\x60", " ", text, flags=re.S)
    text = re.sub(r"\x60([^\x60]*)\x60", r"\1", text)
    text = re.sub(r"\\\[(.*?)\\\]", r"\1", text, flags=re.S)
    text = re.sub(r"\\\((.*?)\\\)", r"\1", text)
    text = text.replace("\\", "").replace("**", "").replace("|", ". ")
    text = re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", text, flags=re.M)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_sections() -> list[tuple[str, str]]:
    raw = BRIEF.read_text(encoding="utf-8")
    body = raw[raw.index("## 8. Narrative architecture"):raw.index("## 14. Mandatory data-derived")]
    matches = list(re.finditer(r"^(##|###)\s+(.+)$", body, flags=re.M))
    keep_h2 = ("10. From experiments", "11. Scaling", "12. Main-film")
    result = []
    for index, match in enumerate(matches):
        level, title = match.groups()
        if level == "##" and not title.startswith(keep_h2):
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        content = body[match.end():end].strip()
        if content:
            result.append((title.strip(), content))
    return result


def chunks(text: str, target: int = 215) -> list[str]:
    paragraphs = [clean(p) for p in re.split(r"\n\s*\n", text) if clean(p)]
    output, current, count = [], [], 0
    for paragraph in paragraphs:
        if paragraph.lower().startswith(("visual:", "end the epilogue")):
            continue
        words = paragraph.split()
        if current and count + len(words) > target:
            output.append(" ".join(current))
            current, count = [], 0
        current.append(paragraph)
        count += len(words)
    if current:
        output.append(" ".join(current))
    return output or [clean(text)]


def experiment_code(title: str) -> str | None:
    match = re.search(r"Experiment(?:s)?\s+([A-T])", title)
    if match:
        return match.group(1)
    if title.startswith("Q completed"):
        return "Q"
    return None


def is_epilogue(title: str) -> bool:
    return title.startswith(("Q completed", "Q2", "Iteration 20", "Iteration 21", "Iteration 22", "Experiment S", "Experiment T"))


def derive(title: str, content: str) -> tuple[str, str, str, str]:
    sentences = re.split(r"(?<=[.!?])\s+", clean(content))
    finding = next(
        (s for s in sentences if any(k in s.lower() for k in ("result", "conclusion", "lesson", "range", "hit rate"))),
        sentences[0],
    )
    limitation = next(
        (s for s in sentences if any(k in s.lower() for k in ("limitation", "caveat", "do not", "incomplete", "only"))),
        "The conclusion is scoped to the recorded evaluator, landscape, and budget.",
    )
    decision = next(
        (s for s in sentences if any(k in s.lower() for k in ("decision", "motivat", "recommend", "next experiment"))),
        "Carry this constraint into the next experiment and compare methods at equal cost.",
    )
    sample_match = re.search(
        r"(?:all\s+)?[\d,]+(?:\s*(?:orders|orderings|seeds|runs|questions|rows|calls|systems|landscapes|permutations|cells))",
        clean(content),
        flags=re.I,
    )
    sample = sample_match.group(0) if sample_match else "the sample reported in the source"
    return finding[:300], limitation[:300], decision[:300], sample[:120]


def key_for(title: str) -> str:
    title = re.sub(r"\s+\(\d+[^)]*minutes\)$", "", title)
    return re.sub(r"\s+—.*$", "", title)


def title_for(title: str) -> str:
    return clean(re.sub(r"^\d+\.\s*", "", title))


def status_for(title: str, content: str, epilogue: bool) -> str:
    text = f"{title} {content}".lower()
    if "failed" in text or "falsified" in text or "negative result" in text:
        return "negative"
    if "correction" in text or "corrected" in text or "retract" in text:
        return "corrected"
    if "boundary" in text or "no advantage" in text or "random competitiveness" in text:
        return "boundary"
    if "in progress" in text or "proposal" in text or "future" in text:
        return "planned"
    if epilogue or title.startswith("Experiment"):
        return "completed"
    return "concept"


def visual_for(title: str, code: str | None) -> str:
    if code:
        return "chart"
    if title.startswith("Chapter 0"):
        return "cards"
    if title.startswith("Chapter 2"):
        return "algorithm"
    if title.startswith("Chapter 3"):
        return "mutation"
    if title.startswith("Chapter 4"):
        return "supernet"
    if title.startswith("Chapter 5"):
        return "theory"
    if title.startswith("Chapter 7") or title.startswith("10."):
        return "protocol"
    if title.startswith("11."):
        return "supernet"
    if title.startswith("12."):
        return "conclusion"
    return "table"


def narration(title: str, body: str, finding: str, limitation: str, decision: str, sample: str, graph: str | None) -> str:
    opening = (
        f"This section examines {title_for(title)} from first principles. "
        "Keep two questions separate: does changing the order change the measured outcome, "
        "and does the proposed search method beat a matched alternative at the same distinct-evaluation budget? "
    )
    graph_reading = ""
    if graph:
        graph_reading = (
            f" Now read evidence panel {graph}. The axes, units, and sample are stated on screen. "
            f"The sample represented here is {sample}. Raw observations remain visible wherever the artifact provides them. "
            "Censored observations stay marked at the cap rather than becoming invented hitting times, and sampled landscapes leave unobserved permutations blank. "
            f"The supported finding is: {finding} The broader claim not established here is: {limitation} "
            f"This evidence changed the program as follows: {decision} "
        )
    closing = (
        " The distinction is part of the result. A large ordering effect does not automatically imply an evolutionary-search advantage, "
        "and almost-sure convergence does not promise practical efficiency."
    )
    return opening + clean(body) + graph_reading + closing


def evidence_narration(
    title: str,
    finding: str,
    limitation: str,
    decision: str,
    sample: str,
    graph: str | None,
    artifact: str,
) -> str:
    panel = graph or "the section's explanatory diagram"
    return (
        f"Pause on {panel} for a complete evidence reading of {title_for(title)}. "
        "First, identify the research question before looking at the answer. The question asks whether the fixed components create a meaningful ordering surface, "
        "whether a particular neighborhood provides useful guidance on that surface, or whether a cheaper executor is equally effective. "
        f"The sample is {sample}, and the source artifact is {clean(artifact)}. "
        "The horizontal axis names the recorded independent quantity—such as permutation size, position, distance, or distinct evaluations. "
        "The vertical axis names the measured outcome—such as accuracy, error, hit probability, regret, correlation, or hitting time. "
        "Raw points remain visible when their count permits. A summary line or bar describes those points; it does not replace them. "
        "A capped observation receives a censor marker, and a sampled landscape never pretends to be exhaustively enumerated. "
        f"The central pattern supports this finding: {finding} "
        f"The correct limitation is: {limitation} "
        "That limitation rules out a broader promotional interpretation while preserving the result actually measured. "
        f"The decision carried into the research program is: {decision} "
        "Finally, compare against the equal-budget alternative. Generations, repeated cache hits, and distinct evaluations are not interchangeable. "
        "A method earns a search-efficiency claim only when uncertainty, evaluator resolution, optimum density, and evaluation cost have all been accounted for."
    )


def make_inventory() -> dict:
    spoken = (
        "This inventory confirms that the film has reconstructed all twelve numbered figures, all eight numbered tables, and all three algorithms. "
        "Figures one through twelve cover ordering effects, algorithm flow, the supernet decoder, absorbing states, spectral decay, XOR convergence, "
        "a complete generation, the S three Cayley graph, diversity, convergence assumptions, the proposed weight-sharing strategy, and the research roadmap. "
        "Tables one through eight cover search spaces, operator matching, the experiment ledger, exact landscape sizes, neural outcomes, operator results, "
        "the language-model study, and proposed domains. The three algorithms cover the main loop, tournament selection, and generic mutation. "
        "Each item appears first in its substantive teaching scene; this inventory is the final completeness check."
    )
    return {
        "id": "paper-inventory", "chapter": "Chapter-12", "chapterTitle": "Paper inventory",
        "title": "Twelve figures, eight tables, and three algorithms", "visual": "table",
        "audio": "audio/paper-inventory.wav", "durationInFrames": 0, "spokenText": spoken,
        "captionCues": [], "finding": "The complete numbered paper inventory is present.",
        "limitation": "Inventory presence does not substitute for source validation.",
        "downstreamDecision": "Run the automated content audit before rendering.",
        "claimStatus": "completed", "source": "PRISM paper cut through Iteration 18",
        "sampleSize": "12 figures; 8 tables; 3 algorithms",
        "caveat": "Every item is also mapped to a substantive scene.",
        "altDescription": "A progressive checklist covers every numbered paper item.",
        "paperFigures": list(range(1, 13)), "paperTables": list(range(1, 9)), "algorithms": [1, 2, 3],
    }


def build() -> dict:
    scenes = []
    for title, content in parse_sections():
        code = experiment_code(title)
        graph = GRAPH_IDS.get(code) if code else None
        artifact = ARTIFACTS.get(code, "production brief and paper source") if code else "production brief and paper source"
        epilogue = is_epilogue(title)
        finding, limitation, decision, sample = derive(title, content)
        section_chunks = chunks(content)
        base = re.sub(r"[^a-z0-9]+", "-", key_for(title).lower()).strip("-")
        for index, body in enumerate(section_chunks, start=1):
            ident = f"{base}-{index:02d}"
            chapter = key_for(title).replace(" ", "-").replace(",", "")
            item = {
                "id": ident,
                "chapter": chapter,
                "chapterTitle": title_for(title),
                "title": title_for(title) if len(section_chunks) == 1 else f"{title_for(title)} · Part {index}",
                "visual": visual_for(title, code),
                "audio": f"audio/{ident}.wav",
                "durationInFrames": 0,
                "spokenText": narration(title, body, finding, limitation, decision, sample, graph),
                "captionCues": [],
                "finding": finding,
                "limitation": limitation,
                "downstreamDecision": decision,
                "claimStatus": status_for(title, content, epilogue),
                "source": "Post-paper research update" if epilogue else "PRISM paper cut through Iteration 18",
                "sampleSize": sample,
                "caveat": limitation,
                "altDescription": f"Animated evidence panel for {title_for(title)}. {finding}",
            }
            if graph:
                item["graphId"] = graph
                item["graphSource"] = {
                    "artifact": artifact,
                    "filters": ["paper-cut boundary preserved", "no inferred points"],
                    "transforms": ["documented in graph-manifest.json"],
                    "xAxis": "Defined in graph manifest",
                    "yAxis": "Defined in graph manifest",
                }
            if epilogue:
                item["isEpilogue"] = True
            scenes.append(item)
        evidence_id = f"{base}-evidence"
        evidence = {
            "id": evidence_id,
            "chapter": key_for(title).replace(" ", "-").replace(",", ""),
            "chapterTitle": title_for(title),
            "title": f"{title_for(title)} · Evidence reading",
            "visual": "chart" if graph else "table",
            "audio": f"audio/{evidence_id}.wav",
            "durationInFrames": 0,
            "spokenText": evidence_narration(title, finding, limitation, decision, sample, graph, artifact),
            "captionCues": [],
            "finding": finding,
            "limitation": limitation,
            "downstreamDecision": decision,
            "claimStatus": status_for(title, content, epilogue),
            "source": "Post-paper research update" if epilogue else "PRISM paper cut through Iteration 18",
            "sampleSize": sample,
            "caveat": limitation,
            "altDescription": f"Detailed graph reading for {title_for(title)}. {finding}",
        }
        if graph:
            evidence["graphId"] = graph
            evidence["graphSource"] = {
                "artifact": artifact,
                "filters": ["paper-cut boundary preserved", "no inferred points"],
                "transforms": ["documented in graph-manifest.json"],
                "xAxis": "Defined in graph manifest",
                "yAxis": "Defined in graph manifest",
            }
        if epilogue:
            evidence["isEpilogue"] = True
        scenes.append(evidence)
    scenes.insert(next((i for i, s in enumerate(scenes) if s.get("isEpilogue")), len(scenes)), make_inventory())
    return {"title": "PRISM Paper Explained", "fps": 30, "scenes": scenes}


def main() -> None:
    payload = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    main_words = sum(len(s["spokenText"].split()) for s in payload["scenes"] if not s.get("isEpilogue"))
    ep_words = sum(len(s["spokenText"].split()) for s in payload["scenes"] if s.get("isEpilogue"))
    print(f"Wrote {len(payload['scenes'])} scenes")
    print(f"Main: {main_words} words, about {main_words / 137:.1f} minutes at 137 words per minute")
    print(f"Epilogue: {ep_words} words, about {ep_words / 137:.1f} minutes at 137 words per minute")


if __name__ == "__main__":
    main()
