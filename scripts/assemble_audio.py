from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE_ROOT = ROOT.parent
SEGMENTS_FILE = ROOT / "data" / "segments" / "segments.jsonl"
DEFAULT_OUTPUT_DIR = WORKSPACE_ROOT / "outputs" / "yuguihong-audiobook"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assemble segment wav files into chapter MP3 files.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--bitrate", default="128k")
    parser.add_argument("--full-book", action="store_true", help="Also create one full-book MP3.")
    return parser.parse_args()


def load_segments() -> list[dict]:
    return [
        json.loads(line)
        for line in SEGMENTS_FILE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_concat_list(path: Path, audio_paths: list[Path]) -> None:
    lines = []
    for audio_path in audio_paths:
        escaped = audio_path.as_posix().replace("'", "'\\''")
        lines.append(f"file '{escaped}'")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_ffmpeg(ffmpeg: str, list_file: Path, output_file: Path, bitrate: str) -> None:
    command = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_file),
        "-vn",
        "-ac",
        "1",
        "-ar",
        "24000",
        "-b:a",
        bitrate,
        str(output_file),
    ]
    subprocess.run(command, check=True)


def main() -> None:
    args = parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("FFmpeg was not found on PATH.")

    segments = load_segments()
    missing = [segment["id"] for segment in segments if not segment.get("audio_path")]
    if missing:
        raise SystemExit(f"Missing audio for {len(missing)} segments. First missing: {missing[0]}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    list_dir = args.output_dir / "_concat_lists"
    list_dir.mkdir(parents=True, exist_ok=True)

    by_chapter: dict[int, list[dict]] = defaultdict(list)
    for segment in segments:
        by_chapter[segment["chapter_index"]].append(segment)

    full_book_audio_paths: list[Path] = []
    for chapter_index in sorted(by_chapter):
        chapter_segments = by_chapter[chapter_index]
        audio_paths = [ROOT / segment["audio_path"] for segment in chapter_segments]
        full_book_audio_paths.extend(audio_paths)

        list_file = list_dir / f"chapter_{chapter_index:02d}.txt"
        output_file = args.output_dir / f"yuguihong_chapter_{chapter_index:02d}.mp3"
        write_concat_list(list_file, audio_paths)
        run_ffmpeg(ffmpeg, list_file, output_file, args.bitrate)
        chapter_seconds = sum(float(segment.get("duration_sec") or 0) for segment in chapter_segments)
        print(f"chapter {chapter_index:02d}: {output_file} ({chapter_seconds / 60:.1f} min)")

    if args.full_book:
        list_file = list_dir / "full_book.txt"
        output_file = args.output_dir / "yuguihong_full_book.mp3"
        write_concat_list(list_file, full_book_audio_paths)
        run_ffmpeg(ffmpeg, list_file, output_file, args.bitrate)
        total_seconds = sum(float(segment.get("duration_sec") or 0) for segment in segments)
        print(f"full book: {output_file} ({total_seconds / 3600:.2f} hr)")


if __name__ == "__main__":
    main()

