"""Restart Kokoro after native CPU exits until every scene WAV is complete."""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILM = ROOT / "src" / "data" / "film.json"
AUDIO = ROOT / "public" / "audio"
LOG = ROOT / "public" / "data" / "narration-generation.log"


def scene_ids() -> list[str]:
    data = json.loads(FILM.read_text(encoding="utf-8"))
    return [scene["id"] for scene in data["scenes"]]


def completed(ids: list[str]) -> set[str]:
    return {ident for ident in ids if (AUDIO / f"{ident}.wav").exists()}


def main() -> None:
    ids = scene_ids()
    LOG.parent.mkdir(parents=True, exist_ok=True)
    attempts = 0
    previous = -1
    while len(completed(ids)) < len(ids):
        done = len(completed(ids))
        print(f"Kokoro resume pass {attempts + 1}: {done}/{len(ids)} scene WAVs present", flush=True)
        with LOG.open("a", encoding="utf-8") as log:
            log.write(f"\nresume pass {attempts + 1}: {done}/{len(ids)}\n")
            result = subprocess.run(
                [sys.executable, "-u", "scripts/generate_narration.py"],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                check=False,
            )
            log.write(f"exit={result.returncode}\n")
        now = len(completed(ids))
        print(f"Pass ended with code {result.returncode}; progress {now}/{len(ids)}", flush=True)
        if now <= done and now == previous:
            raise RuntimeError(f"Two consecutive passes made no progress. Inspect {LOG}")
        previous = now
        attempts += 1
        time.sleep(2)
    print("All scene WAVs are complete. Running one final manifest/master pass.", flush=True)
    subprocess.run([sys.executable, "-u", "scripts/generate_narration.py"], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
