from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IMAGE_DIR = ROOT / "assets" / "images" / "openverse"
CREDITS_FILE = IMAGE_DIR / "image_credits.json"
OPENVERSE_API = "https://api.openverse.engineering/v1/images/"

QUERIES = [
    "ancient chinese architecture",
    "chinese garden",
    "chinese temple",
    "chinese lantern",
    "hanfu",
    "forbidden city",
    "traditional chinese courtyard",
]


def request_bytes(url: str) -> tuple[bytes, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 audiobook-video-prep/0.1",
            "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        content_type = response.headers.get("Content-Type", "")
        return response.read(), content_type


def request_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 audiobook-video-prep/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def safe_name(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value[:60] or "image"


def search(query: str, page_size: int = 8) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "q": query,
            "license_type": "commercial,modification",
            "page_size": page_size,
        }
    )
    payload = request_json(f"{OPENVERSE_API}?{params}")
    return payload.get("results", [])


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    credits = []
    seen_ids = set()

    for query in QUERIES:
        print(f"search: {query}")
        for result in search(query):
            if result.get("id") in seen_ids:
                continue
            seen_ids.add(result.get("id"))

            title = result.get("title") or query
            image_url = result.get("url") or result.get("thumbnail")
            if not image_url:
                continue

            filename = f"{len(credits) + 1:03d}_{safe_name(title)}.jpg"
            path = IMAGE_DIR / filename

            try:
                data, content_type = request_bytes(image_url)
                if "image" not in content_type.lower() and not data.startswith((b"\xff\xd8", b"\x89PNG", b"RIFF")):
                    raise ValueError(f"not an image: {content_type}")
                path.write_bytes(data)
            except Exception as error:
                print(f"skip: {title} ({error})")
                continue

            credits.append(
                {
                    "file": path.relative_to(ROOT).as_posix(),
                    "title": title,
                    "creator": result.get("creator"),
                    "source": result.get("foreign_landing_url"),
                    "license": result.get("license"),
                    "license_version": result.get("license_version"),
                    "license_url": result.get("license_url"),
                    "provider": result.get("provider"),
                    "query": query,
                }
            )
            print(f"saved: {filename}")
            time.sleep(0.25)

            if len(credits) >= 30:
                break
        if len(credits) >= 30:
            break

    CREDITS_FILE.write_text(json.dumps(credits, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"downloaded: {len(credits)}")
    print(f"credits: {CREDITS_FILE}")


if __name__ == "__main__":
    main()

