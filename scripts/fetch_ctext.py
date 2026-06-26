from __future__ import annotations

import json
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILE = ROOT / "data" / "sources" / "ctext_yuguihong.json"
RAW_DIR = ROOT / "data" / "raw"
BASE_URL = "https://ctext.org/wiki.pl?if=gb&chapter={chapter_id}&remap=gb"
TOC_URL = "https://ctext.org/wiki.pl?if=gb&res=163914&remap=gb"


def fetch(url: str) -> str:
    curl = shutil.which("curl.exe") or shutil.which("curl")
    if curl:
        result = subprocess.run(
            [curl, "-L", "--silent", "--show-error", url],
            check=True,
            capture_output=True,
        )
        return result.stdout.decode("utf-8")

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 audiobook-prep/0.1 (+local personal project)"
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8")


def save_if_missing(path: Path, url: str) -> None:
    if path.exists() and path.stat().st_size > 0:
        print(f"cached: {path}")
        return
    print(f"fetching: {url}")
    path.write_text(fetch(url), encoding="utf-8")
    time.sleep(1.2)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    source = json.loads(SOURCE_FILE.read_text(encoding="utf-8"))

    save_if_missing(RAW_DIR / "toc.html", TOC_URL)
    for chapter in source["chapters"]:
        filename = f"chapter_{chapter['index']:02d}_{chapter['id']}.html"
        save_if_missing(RAW_DIR / filename, BASE_URL.format(chapter_id=chapter["id"]))


if __name__ == "__main__":
    main()
