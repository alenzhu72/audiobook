from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEGMENTS_FILE = ROOT / "data" / "segments" / "segments.jsonl"
SRT_DIR = ROOT / "data" / "subtitles"


def format_time(seconds: float) -> str:
    millis = round(seconds * 1000)
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def main() -> None:
    SRT_DIR.mkdir(parents=True, exist_ok=True)
    current_chapter = None
    index = 1
    cursor = 0.0
    lines: list[str] = []

    for raw in SEGMENTS_FILE.read_text(encoding="utf-8").splitlines():
        segment = json.loads(raw)
        chapter = segment["chapter_index"]
        if current_chapter is None:
            current_chapter = chapter
        if chapter != current_chapter:
            write_srt(current_chapter, lines)
            current_chapter = chapter
            index = 1
            cursor = 0.0
            lines = []

        duration = segment["duration_sec"] or max(2.5, len(segment["text"]) / 4.5)
        start = cursor
        end = cursor + duration
        lines.extend(
            [
                str(index),
                f"{format_time(start)} --> {format_time(end)}",
                segment["text"],
                "",
            ]
        )
        index += 1
        cursor = end

    if current_chapter is not None:
        write_srt(current_chapter, lines)


def write_srt(chapter: int, lines: list[str]) -> None:
    path = SRT_DIR / f"chapter_{chapter:02d}.srt"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote: {path}")


if __name__ == "__main__":
    main()

