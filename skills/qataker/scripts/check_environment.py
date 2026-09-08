#!/usr/bin/env python3
"""Check imports and sibling scripts without installing or downloading models."""

import importlib
import json
import shutil
import sys
from pathlib import Path


def check():
    root = Path(__file__).resolve().parents[1]
    required = {}
    for name in ("pymupdf", "pymupdf4llm", "trafilatura", "yt_dlp", "whisper", "tree_sitter_language_pack"):
        try:
            importlib.import_module(name)
            required[name] = {"ok": True}
        except Exception as exc:
            required[name] = {"ok": False, "error": str(exc)}
    for name in ("ffmpeg", "ffprobe"):
        required[name] = {"ok": shutil.which(name) is not None, "path": shutil.which(name)}
    for name in ("extract_pdf.py", "extract_transcript.py"):
        path = root.parent / "notetaker" / "scripts" / name
        required[f"notetaker/{name}"] = {"ok": path.is_file(), "path": str(path)}
    ready = all(item["ok"] for item in required.values())
    print(json.dumps({"python": sys.executable, "base_ready": ready, "required": required,
                      "note": "Imports only; OCR engines, grammar assets, Whisper weights and extraction are checked separately."},
                     ensure_ascii=False, indent=2))
    return 0 if ready else 1


if __name__ == "__main__":
    raise SystemExit(check())
