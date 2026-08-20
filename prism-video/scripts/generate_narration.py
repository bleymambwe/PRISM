"""Generate deterministic 24 kHz Kokoro narration, manifests, and captions."""

from __future__ import annotations

import argparse
import json
import math
import re
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
FILM_PATH = ROOT / "src" / "data" / "film.json"
AUDIO_DIR = ROOT / "public" / "audio"
CAPTION_DIR = ROOT / "public" / "captions"
DATA_DIR = ROOT / "public" / "data"
MANIFEST_PATH = ROOT / "src" / "data" / "audioManifest.json"
SAMPLE_RATE = 24_000
FPS = 30
LEAD_FRAMES = 12
TAIL_FRAMES = 18

PRONUNCIATIONS = {
    "PRISM": "prism",
    "FDC": "F D C",
    "SINDy": "sin-dee",
    "GSM8K": "G S M eight K",
    "MATH-500": "Math five hundred",
    "NAS-Bench-201": "NAS Bench two oh one",
    "rho_1": "rho one",
    "ρ₁": "rho one",
    "ρ(Q)": "the spectral radius of Q",
    "p_m": "p sub m",
    "S_n": "the symmetric group S n",
    "n!": "n factorial",
}

AUDITIONS = {
    "prose": (
        "Prism studies systems whose components are fixed but whose order changes the outcome. "
        "The first task is not to launch an optimizer. It is to measure whether ordering creates meaningful variance, "
        "whether the evaluator has enough resolution, and whether nearby permutations contain useful information. "
        "Only then should the method choose enumeration, random sampling, a surrogate, transfer guidance, or evolutionary search."
    ),
    "equations": (
        "The state is the entire population. As the number of generations grows, the probability that the population contains an optimal ordering approaches one. "
        "The expected absorption time is described by the fundamental matrix of the transient states. "
        "This is an eventual guarantee under stated assumptions, not a promise that a real search will finish quickly."
    ),
    "acronyms": (
        "Prism estimates rho one and F D C before search. The language-model study uses G S M eight K. "
        "The scientific pipeline uses sin-dee. The later reasoning study uses Math five hundred, and the architecture study uses NAS Bench two oh one. "
        "Population size is called mu, while p sub m is the mutation probability."
    ),
}


def normalize_pronunciation(text: str) -> str:
    for written, spoken in PRONUNCIATIONS.items():
        text = text.replace(written, spoken)
    return text


def semantic_chunks(text: str, max_words: int = 70) -> list[str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", normalize_pronunciation(text)) if s.strip()]
    chunks: list[str] = []
    current: list[str] = []
    count = 0
    for sentence in sentences:
        words = sentence.split()
        if current and count + len(words) > max_words:
            chunks.append(" ".join(current))
            current, count = [], 0
        current.append(sentence)
        count += len(words)
    if current:
        chunks.append(" ".join(current))
    return chunks


def synthesize(pipeline, text: str, voice: str, speed: float, final_pause: float = 0.62) -> np.ndarray:
    pieces: list[np.ndarray] = []
    chunks = semantic_chunks(text)
    for index, chunk in enumerate(chunks):
        generated = pipeline(chunk, voice=voice, speed=speed, split_pattern=r"\n+")
        chunk_audio = [np.asarray(audio, dtype=np.float32).reshape(-1) for _, _, audio in generated]
        if chunk_audio:
            pieces.append(np.concatenate(chunk_audio))
        if index < len(chunks) - 1:
            pieces.append(np.zeros(int(SAMPLE_RATE * 0.34), dtype=np.float32))
    pieces.append(np.zeros(int(SAMPLE_RATE * final_pause), dtype=np.float32))
    audio = np.concatenate(pieces) if pieces else np.zeros(int(SAMPLE_RATE * final_pause), dtype=np.float32)
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 0:
        audio = audio * (10 ** (-3 / 20) / peak)
    return np.clip(audio, -1.0, 1.0)


def phrase_captions(text: str, duration_seconds: float) -> list[dict]:
    words = text.split()
    phrases: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if current and (len(candidate) > 76 or len(current) >= 10):
            phrases.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        phrases.append(" ".join(current))
    weights = [max(1, len(p.split())) for p in phrases]
    total = sum(weights) or 1
    available_ms = max(1, int((duration_seconds - 0.62) * 1000))
    captions = []
    cursor = 0
    for index, (phrase, weight) in enumerate(zip(phrases, weights)):
        end = available_ms if index == len(phrases) - 1 else cursor + round(available_ms * weight / total)
        captions.append({
            "text": "\n".join(textwrap.wrap(phrase, width=42, break_long_words=False, break_on_hyphens=False)[:2]),
            "startMs": cursor,
            "endMs": max(cursor + 1, end),
            "timestampMs": cursor,
            "confidence": None,
        })
        cursor = end
    return captions


def caption_timestamp(seconds: float, separator: str) -> str:
    millis = max(0, round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{ms:03d}"


def write_caption_exports(scenes: list[dict], manifest: dict, epilogue: bool) -> None:
    selected = [s for s in scenes if bool(s.get("isEpilogue")) == epilogue]
    srt_lines: list[str] = []
    vtt_lines = ["WEBVTT", ""]
    cue_index = 1
    cursor_seconds = 0.0
    for scene in selected:
        record = manifest["scenes"][scene["id"]]
        cursor_seconds += LEAD_FRAMES / FPS
        for cue in record["captions"]:
            start = cursor_seconds + cue["startMs"] / 1000
            end = cursor_seconds + cue["endMs"] / 1000
            srt_lines.extend([str(cue_index), f"{caption_timestamp(start, ',')} --> {caption_timestamp(end, ',')}", cue["text"], ""])
            vtt_lines.extend([f"{caption_timestamp(start, '.')} --> {caption_timestamp(end, '.')}", cue["text"], ""])
            cue_index += 1
        cursor_seconds += record["durationSeconds"] + TAIL_FRAMES / FPS
    stem = "prism-epilogue" if epilogue else "prism-paper-explained"
    (CAPTION_DIR / f"{stem}.srt").write_text("\n".join(srt_lines), encoding="utf-8")
    (CAPTION_DIR / f"{stem}.vtt").write_text("\n".join(vtt_lines), encoding="utf-8")


def write_master(scenes: list[dict], manifest: dict, epilogue: bool) -> None:
    selected = [s for s in scenes if bool(s.get("isEpilogue")) == epilogue]
    target = AUDIO_DIR / ("prism-epilogue-master.wav" if epilogue else "prism-paper-explained-master.wav")
    with sf.SoundFile(target, mode="w", samplerate=SAMPLE_RATE, channels=1, subtype="PCM_16") as output:
        for scene in selected:
            output.write(np.zeros(round(SAMPLE_RATE * LEAD_FRAMES / FPS), dtype=np.float32))
            audio, sr = sf.read(AUDIO_DIR / f"{scene['id']}.wav", dtype="float32")
            if sr != SAMPLE_RATE:
                raise ValueError(f"Unexpected sample rate {sr} in {scene['id']}")
            output.write(audio)
            output.write(np.zeros(round(SAMPLE_RATE * TAIL_FRAMES / FPS), dtype=np.float32))


def run_auditions(pipeline, voice: str, speed: float, force: bool) -> None:
    directory = AUDIO_DIR / "auditions"
    directory.mkdir(parents=True, exist_ok=True)
    for name, base in AUDITIONS.items():
        text = (base + " ") * 2
        target = directory / f"{name}-{voice}.wav"
        if target.exists() and not force:
            continue
        audio = synthesize(pipeline, text, voice, speed, final_pause=0.8)
        sf.write(target, audio, SAMPLE_RATE, subtype="PCM_16")
        print(f"audition {name}: {len(audio) / SAMPLE_RATE:.1f}s -> {target}")
    (DATA_DIR / "pronunciations.json").write_text(json.dumps(PRONUNCIATIONS, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--auditions-only", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--voice", default="af_heart")
    parser.add_argument("--speed", type=float, default=0.90)
    parser.add_argument("--scene")
    parser.add_argument("--audition")
    args = parser.parse_args()

    from kokoro import KPipeline

    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    CAPTION_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", device="cpu")
    if args.audition:
        if args.audition not in AUDITIONS:
            raise ValueError(f"Unknown audition: {args.audition}")
        directory = AUDIO_DIR / "auditions"
        directory.mkdir(parents=True, exist_ok=True)
        text = (AUDITIONS[args.audition] + " ") * 2
        target = directory / f"{args.audition}-{args.voice}.wav"
        audio = synthesize(pipeline, text, args.voice, args.speed, final_pause=0.8)
        sf.write(target, audio, SAMPLE_RATE, subtype="PCM_16")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "pronunciations.json").write_text(json.dumps(PRONUNCIATIONS, indent=2) + "\n", encoding="utf-8")
        print(f"audition {args.audition}: {len(audio) / SAMPLE_RATE:.1f}s -> {target}")
        return
    run_auditions(pipeline, args.voice, args.speed, args.force)
    if args.auditions_only:
        return

    film = json.loads(FILM_PATH.read_text(encoding="utf-8"))
    scenes = [s for s in film["scenes"] if not args.scene or s["id"] == args.scene]
    manifest = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sampleRate": SAMPLE_RATE,
        "voice": args.voice,
        "scenes": {},
    }
    if MANIFEST_PATH.exists() and not args.force:
        previous = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        manifest["scenes"].update(previous.get("scenes", {}))

    narration_export = []
    for index, scene in enumerate(scenes, start=1):
        target = AUDIO_DIR / f"{scene['id']}.wav"
        if not target.exists() or args.force:
            audio = synthesize(pipeline, scene["spokenText"], args.voice, args.speed)
            sf.write(target, audio, SAMPLE_RATE, subtype="PCM_16")
        info = sf.info(target)
        audio, _ = sf.read(target, dtype="float32")
        peak = float(np.max(np.abs(audio))) if len(audio) else 0.0
        duration = info.frames / info.samplerate
        captions = phrase_captions(scene["spokenText"], duration)
        (CAPTION_DIR / f"{scene['id']}.json").write_text(json.dumps(captions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        manifest["scenes"][scene["id"]] = {
            "durationSeconds": duration,
            "durationInFrames": math.ceil(duration * FPS) + LEAD_FRAMES + TAIL_FRAMES,
            "peakDbfs": 20 * math.log10(peak) if peak > 0 else -120,
            "captions": captions,
        }
        narration_export.append({"id": scene["id"], "title": scene["title"], "spokenText": scene["spokenText"]})
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"[{index}/{len(scenes)}] {scene['id']}: {duration:.1f}s")

    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if not args.scene:
        (DATA_DIR / "final-narration.json").write_text(json.dumps(narration_export, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown = "# PRISM Paper Explained — Final Narration\n\n" + "\n\n".join(f"## {s['title']}\n\n{s['spokenText']}" for s in scenes)
        (DATA_DIR / "final-narration.md").write_text(markdown + "\n", encoding="utf-8")
        write_caption_exports(film["scenes"], manifest, epilogue=False)
        write_caption_exports(film["scenes"], manifest, epilogue=True)
        write_master(film["scenes"], manifest, epilogue=False)
        write_master(film["scenes"], manifest, epilogue=True)
    print(f"Wrote audio manifest with {len(manifest['scenes'])} scenes")


if __name__ == "__main__":
    main()
