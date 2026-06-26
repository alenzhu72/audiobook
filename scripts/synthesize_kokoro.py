from __future__ import annotations

import argparse
import importlib.metadata
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEGMENTS_FILE = ROOT / "data" / "segments" / "segments.jsonl"
AUDIO_DIR = ROOT / "assets" / "audio" / "kokoro"
SAMPLE_RATE = 24_000
MIN_KOKORO_VERSION = (0, 9, 4)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate audiobook wav files with Kokoro.")
    parser.add_argument("--chapter", type=int, help="Only synthesize one chapter.")
    parser.add_argument("--limit", type=int, help="Only synthesize the first N matching segments.")
    parser.add_argument("--voice", default="zf_xiaobei", help="Kokoro voice name or local voice tensor.")
    parser.add_argument("--lang", default="z", help="Kokoro language code. Use z for Mandarin Chinese.")
    parser.add_argument("--speed", type=float, default=0.95)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_segments() -> list[dict]:
    return [
        json.loads(line)
        for line in SEGMENTS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def save_segments(segments: list[dict]) -> None:
    with SEGMENTS_FILE.open("w", encoding="utf-8") as out:
        for segment in segments:
            out.write(json.dumps(segment, ensure_ascii=False) + "\n")


def selected_segments(segments: list[dict], chapter: int | None, limit: int | None) -> list[dict]:
    selected = [
        segment
        for segment in segments
        if chapter is None or segment["chapter_index"] == chapter
    ]
    return selected[:limit] if limit else selected


def version_tuple(value: str) -> tuple[int, ...]:
    parts = []
    for item in value.split("."):
        digits = "".join(ch for ch in item if ch.isdigit())
        if not digits:
            break
        parts.append(int(digits))
    return tuple(parts)


def main() -> None:
    if sys.version_info >= (3, 13):
        raise SystemExit(
            "Kokoro does not support Python 3.13+ yet. "
            "Create a Python 3.12 environment first, then run this script with "
            ".\\.venv-kokoro\\Scripts\\python.exe"
        )

    args = parse_args()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    try:
        import numpy as np
        import soundfile as sf
        from kokoro import KPipeline
    except ImportError as error:
        raise SystemExit(
            "Missing Kokoro dependencies. Run: pip install -r requirements-kokoro.txt"
        ) from error

    kokoro_version = importlib.metadata.version("kokoro")
    if version_tuple(kokoro_version) < MIN_KOKORO_VERSION:
        raise SystemExit(
            f"Kokoro {kokoro_version} is too old for Mandarin Chinese. "
            "Run: .\\.venv-kokoro\\Scripts\\python.exe -m pip install --upgrade -r .\\requirements-kokoro.txt"
        )

    segments = load_segments()
    targets = selected_segments(segments, args.chapter, args.limit)
    pipeline = KPipeline(lang_code=args.lang)

    for index, segment in enumerate(targets, start=1):
        audio_path = AUDIO_DIR / f"{segment['id']}.wav"
        relative_audio_path = audio_path.relative_to(ROOT).as_posix()
        if audio_path.exists() and not args.overwrite:
            segment["audio_path"] = relative_audio_path
            continue

        parts = []
        for _, _, audio in pipeline(
            segment["text"],
            voice=args.voice,
            speed=args.speed,
            split_pattern=r"\n+",
        ):
            parts.append(audio)

        if not parts:
            print(f"skipped empty audio: {segment['id']}")
            continue

        merged = np.concatenate(parts)
        duration = round(len(merged) / SAMPLE_RATE, 3)
        if len(segment["text"]) > 20 and duration < 2:
            raise SystemExit(
                f"Generated audio is suspiciously short for {segment['id']} ({duration}s). "
                "This usually means an old Kokoro/Misaki install. Upgrade with: "
                ".\\.venv-kokoro\\Scripts\\python.exe -m pip install --upgrade -r .\\requirements-kokoro.txt"
            )
        sf.write(audio_path, merged, SAMPLE_RATE)
        segment["audio_path"] = relative_audio_path
        segment["duration_sec"] = duration
        print(f"{index}/{len(targets)} {segment['id']} {segment['duration_sec']}s")

    save_segments(segments)


if __name__ == "__main__":
    main()
