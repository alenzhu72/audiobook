from __future__ import annotations

import html
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / "data" / "sources" / "ctext_yuguihong.json"
RAW_DIR = ROOT / "data" / "raw"
TEXT_DIR = ROOT / "data" / "text"
SEGMENT_DIR = ROOT / "data" / "segments"
MANIFEST_FILE = ROOT / "data" / "manifest.json"
SEGMENTS_FILE = SEGMENT_DIR / "segments.jsonl"

TEXT_CELL_RE = re.compile(
    r'<tr class="result"[^>]*>.*?<td class="ctext"[^>]*>.*?</td><td class="ctext">(.*?)</td></tr>',
    re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
SENTENCE_RE = re.compile(r"([^。！？!?]+[。！？!?]?)")


def clean_html_text(value: str) -> str:
    value = TAG_RE.sub("", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", "", value)
    return value.strip()


def extract_paragraphs(raw_html: str) -> list[str]:
    paragraphs = []
    for match in TEXT_CELL_RE.finditer(raw_html):
        text = clean_html_text(match.group(1))
        if text:
            paragraphs.append(text)
    return paragraphs


def split_for_tts(paragraph: str, max_chars: int = 80) -> list[str]:
    sentences = [m.group(1).strip() for m in SENTENCE_RE.finditer(paragraph) if m.group(1).strip()]
    if not sentences:
        return [paragraph]

    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not current:
            current = sentence
        elif len(current) + len(sentence) <= max_chars:
            current += sentence
        else:
            chunks.append(current)
            current = sentence

        while len(current) > max_chars:
            chunks.append(current[:max_chars])
            current = current[max_chars:]

    if current:
        chunks.append(current)
    return chunks


def main() -> None:
    source = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    SEGMENT_DIR.mkdir(parents=True, exist_ok=True)

    manifest = {
        "book_title": source["book_title"],
        "source": source["source"],
        "source_url": source["source_url"],
        "chapters": [],
    }

    segment_count = 0
    with SEGMENTS_FILE.open("w", encoding="utf-8") as segment_out:
        for chapter in source["chapters"]:
            raw_file = RAW_DIR / f"chapter_{chapter['index']:02d}_{chapter['id']}.html"
            raw_html = raw_file.read_text(encoding="utf-8")
            paragraphs = extract_paragraphs(raw_html)

            text_file = TEXT_DIR / f"chapter_{chapter['index']:02d}.txt"
            text_file.write_text(
                chapter["title"] + "\n\n" + "\n\n".join(paragraphs) + "\n",
                encoding="utf-8",
            )

            chapter_segments = 0
            for paragraph_index, paragraph in enumerate(paragraphs, start=1):
                for chunk_index, text in enumerate(split_for_tts(paragraph), start=1):
                    chapter_segments += 1
                    segment_count += 1
                    record = {
                        "id": f"ch{chapter['index']:02d}_{chapter_segments:04d}",
                        "chapter_index": chapter["index"],
                        "chapter_title": chapter["title"],
                        "paragraph_index": paragraph_index,
                        "chunk_index": chunk_index,
                        "speaker": "narrator",
                        "text": text,
                        "image_prompt": "",
                        "audio_path": "",
                        "duration_sec": None,
                    }
                    segment_out.write(json.dumps(record, ensure_ascii=False) + "\n")

            manifest["chapters"].append(
                {
                    "index": chapter["index"],
                    "id": chapter["id"],
                    "title": chapter["title"],
                    "paragraph_count": len(paragraphs),
                    "segment_count": chapter_segments,
                    "text_file": str(text_file.relative_to(ROOT)),
                    "source_url": f"https://ctext.org/wiki.pl?if=gb&chapter={chapter['id']}&remap=gb",
                }
            )

    manifest["segment_count"] = segment_count
    MANIFEST_FILE.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"chapters: {len(manifest['chapters'])}")
    print(f"segments: {segment_count}")
    print(f"manifest: {MANIFEST_FILE}")


if __name__ == "__main__":
    main()

