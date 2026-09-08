#!/usr/bin/env python3
"""Export reviewed Markdown Q&A JSON to the user's fixed Anki note type. Stdlib only."""

import argparse
import csv
import html
import io
import json
from pathlib import Path

NOTE_TYPE = "KaTeX and Markdown Basic (Color)"
HEADERS = ("#separator:Comma\n#html:true\n"
           f"#notetype:{NOTE_TYPE}\n#columns:Front,Back,Tags\n#tags column:3\n")


def render_csv(cards):
    if not isinstance(cards, list) or not cards:
        raise ValueError("Expected a non-empty JSON array of cards")
    stream = io.StringIO(newline="")
    stream.write(HEADERS)
    writer = csv.writer(stream, quoting=csv.QUOTE_ALL, lineterminator="\n")
    seen = set()
    for index, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            raise ValueError(f"Card {index}: expected an object")
        for field in ("front", "back", "source"):
            value = card.get(field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Card {index}: {field} must be non-empty text")
            if any(ord(char) < 32 and char not in "\n\r\t" for char in value):
                raise ValueError(f"Card {index}: {field} contains control characters")
        front = card["front"].strip()
        key = " ".join(front.split())
        if key in seen:
            raise ValueError(f"Card {index}: duplicate front")
        seen.add(key)
        tags = card.get("tags", [])
        if not isinstance(tags, list) or any(
            not isinstance(tag, str) or not tag or any(char.isspace() or ord(char) < 32 for char in tag)
            for tag in tags
        ):
            raise ValueError(f"Card {index}: tags must be a list of non-empty, whitespace-free strings")
        back = card["back"].strip() + "\n\n---\n来源：" + card["source"].strip()
        # The template reads innerHTML. Escape source HTML once at this boundary.
        writer.writerow([html.escape(front, quote=False), html.escape(back, quote=False), " ".join(tags)])
    return stream.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        cards = json.loads(args.input.read_text(encoding="utf-8"))
        content = render_csv(cards)  # Validate the whole batch before opening the destination.
        with args.output.open("x", encoding="utf-8", newline="") as stream:
            stream.write(content)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"error: {exc}\n")
    print(f"Exported {len(cards)} cards to {args.output}")


if __name__ == "__main__":
    main()
