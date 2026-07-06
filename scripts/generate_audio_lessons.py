"""Generate the PRISM educational audio lessons via OpenAI TTS.

Pattern adopted from the EVE app's tts_service.py (OpenAITTSService):
- POST https://api.openai.com/v1/audio/speech, model tts-1, mp3 output
- scripts longer than 4096 chars are split on sentence boundaries and
  the MP3 parts concatenated, so the whole lesson is voiced
Differences from EVE: output goes to local files (no Firebase upload),
and the API key is fetched at runtime from Google Cloud Secret Manager
(gcloud secrets versions access latest --secret=OPENAI_API_KEY) so it
never lives in the repo.

Resumable: lessons whose MP3 already exists are skipped; rerun after
any failure. (Iteration 6 artifact.)

Usage: python scripts/generate_audio_lessons.py
"""

import re
import subprocess
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).parent.parent
SCRIPTS_DIR = ROOT / "deliverables" / "audio" / "scripts"
OUT_DIR = ROOT / "deliverables" / "audio"
TTS_URL = "https://api.openai.com/v1/audio/speech"
MODEL = "tts-1"
CHUNK_LIMIT = 4096

# voice per lesson: nova (default, matches EVE) for the teaching levels,
# onyx for the research deep-dive and paper narration
VOICES = {
    "lesson-1-simple": "nova",
    "lesson-2-student": "nova",
    "lesson-3-practitioner": "nova",
    "lesson-4-research": "onyx",
    "lesson-5-critics": "nova",
    "lesson-6-paper": "onyx",
}


def get_api_key():
    r = subprocess.run(
        ["gcloud", "secrets", "versions", "access", "latest",
         "--secret=OPENAI_API_KEY"],
        capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        sys.exit(f"gcloud secret access failed: {r.stderr[:300]}")
    return r.stdout.strip()


def split_text(text, limit):
    """Sentence-boundary chunking, ported from EVE tts_service.py."""
    text = (text or "").strip()
    if len(text) <= limit:
        return [text] if text else []
    pieces = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""
    for piece in pieces:
        if not piece:
            continue
        if len(piece) > limit:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(piece), limit):
                seg = piece[i:i + limit]
                if len(seg) == limit:
                    chunks.append(seg)
                else:
                    current = seg
            continue
        candidate = piece if not current else f"{current} {piece}"
        if len(candidate) <= limit:
            current = candidate
        else:
            chunks.append(current)
            current = piece
    if current:
        chunks.append(current)
    return chunks


def synthesize(api_key, text, voice):
    for attempt in range(3):
        try:
            resp = requests.post(
                TTS_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                json={"model": MODEL, "input": text, "voice": voice,
                      "response_format": "mp3"},
                timeout=120)
            if resp.status_code == 200:
                return resp.content
            print(f"  TTS error {resp.status_code}: {resp.text[:200]}")
            if resp.status_code in (429, 500, 502, 503):
                time.sleep(2 ** attempt)
                continue
            return None
        except requests.RequestException as e:
            print(f"  attempt {attempt + 1} failed: {e}")
            time.sleep(2 ** attempt)
    return None


def main():
    api_key = get_api_key()
    print("API key retrieved from Secret Manager.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for script_path in sorted(SCRIPTS_DIR.glob("lesson-*.txt")):
        name = script_path.stem
        out = OUT_DIR / f"{name}.mp3"
        if out.exists() and out.stat().st_size > 0:
            print(f"{name}: already generated, skipping")
            continue
        text = script_path.read_text(encoding="utf-8")
        voice = VOICES.get(name, "nova")
        chunks = split_text(text, CHUNK_LIMIT)
        print(f"{name}: {len(text)} chars, {len(chunks)} chunk(s), "
              f"voice={voice}")
        parts = []
        ok = True
        for i, chunk in enumerate(chunks):
            audio = synthesize(api_key, chunk, voice)
            if audio is None:
                print(f"{name}: FAILED on chunk {i + 1}/{len(chunks)}")
                ok = False
                break
            parts.append(audio)
        if ok:
            out.write_bytes(b"".join(parts))
            print(f"{name}: wrote {out.stat().st_size} bytes")

    print("DONE")


if __name__ == "__main__":
    main()
