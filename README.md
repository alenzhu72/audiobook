# Yuguihong Audiobook Project

This project turns the CText edition of `玉闺红全传` into structured audiobook/video production inputs.

Current scope:

- Fetch and cache the 10 chapter pages from CText.
- Extract clean chapter text.
- Split the text into narration segments for TTS, subtitles, and image prompts.
- Keep source metadata so outputs can be traced back to the original edition.

Recommended local path for your GTX 1060 6GB:

1. Use this project to prepare text and segment data.
2. Use Kokoro or GPT-SoVITS for TTS.
3. Use existing images or Stable Diffusion 1.5 for visuals.
4. Use FFmpeg for final audiobook/video assembly.

## Quick Start

```powershell
python .\scripts\fetch_ctext.py
python .\scripts\prepare_text.py
python .\scripts\make_srt.py
```

Generated working files:

- `data/raw/`: cached HTML pages from CText
- `data/text/`: clean chapter text
- `data/segments/segments.jsonl`: one TTS/video unit per line
- `data/manifest.json`: book/chapter metadata

## Kokoro TTS Draft

Kokoro currently does not support Python 3.13+.

This project uses `kokoro>=0.9.4` because older Kokoro versions can produce broken Mandarin output.

If your default `python --version` is 3.13 or 3.14, create a separate Kokoro environment first:

```powershell
powershell.exe -ExecutionPolicy Bypass -File .\scripts\setup_kokoro_env.ps1
```

This script creates `.venv-kokoro` with a compatible Python version and installs the TTS dependencies.

If `pip install` says `Requires-Python <3.13` or `No matching distribution found`, you are still using the wrong Python. Run:

```powershell
.\.venv-kokoro\Scripts\python.exe --version
.\.venv-kokoro\Scripts\python.exe -m pip install -r .\requirements-kokoro.txt
```

The version should be Python 3.10, 3.11, or 3.12.

If you previously installed `kokoro==0.7.16`, upgrade it and regenerate the old test files:

```powershell
.\.venv-kokoro\Scripts\python.exe -m pip install --upgrade -r .\requirements-kokoro.txt
.\.venv-kokoro\Scripts\python.exe .\scripts\synthesize_kokoro.py --chapter 1 --limit 6 --overwrite
```

Manual install, only if your current Python is 3.10-3.12:

```powershell
pip install -r .\requirements-kokoro.txt
```

On Windows, Kokoro's Chinese pipeline also needs `espeak-ng` installed. The upstream Kokoro README has Windows notes for that dependency.

Generate a small audio test for chapter 1:

```powershell
.\.venv-kokoro\Scripts\python.exe .\scripts\synthesize_kokoro.py --chapter 1 --limit 5
```

Generate all segments for one chapter:

```powershell
.\.venv-kokoro\Scripts\python.exe .\scripts\synthesize_kokoro.py --chapter 1
```

The script writes `.wav` files to `assets/audio/kokoro/` and updates matching records in `data/segments/segments.jsonl` with `audio_path` and `duration_sec`.

## Source

Primary source page:

https://ctext.org/wiki.pl?if=gb&res=163914&remap=gb

Please respect CText's notice against large-scale automated downloading. This project only fetches the 10 listed chapter pages plus the table of contents and caches them locally.
