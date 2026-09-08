#!/usr/bin/env python3
"""Run with python3 scripts/test_export_anki.py; no third-party dependencies."""

import csv
import html
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from export_anki import HEADERS, render_csv


def main():
    card = {"front": '条件 x < 3 且 y > 2 时，"A,B" 怎么变化？',
            "back": '先判断。\n\n```python\nx = "A,B"\nprint(x)  # \\$literal\n```\n\n$y = x^2$\n\n<script>alert(1)</script> & text',
            "source": '[材料](https://example.org/a?x=1&y=2) §2，p. 3',
            "tags": ["算法::边界", "source::demo"]}
    encoded = render_csv([card])
    rows = list(csv.reader(io.StringIO(encoded[len(HEADERS):], newline="")))
    assert len(rows) == 1 and len(rows[0]) == 3
    assert html.unescape(rows[0][0]) == card["front"]
    assert html.unescape(rows[0][1]) == card["back"] + "\n\n---\n来源：" + card["source"]
    assert "<script>" not in rows[0][1]
    assert rows[0][2] == "算法::边界 source::demo"
    for invalid in ([], {}, [None], [{**card, "back": " "}], [{**card, "source": ""}],
                    [card, {**card, "front": "  " + card["front"]}],
                    [{**card, "tags": "tag"}], [{**card, "tags": ["two words"]}],
                    [{**card, "front": "bad\x00text"}]):
        try:
            render_csv(invalid)
        except ValueError:
            pass
        else:
            raise AssertionError(f"Accepted invalid input: {invalid!r}")
    with tempfile.TemporaryDirectory() as temp:
        source, target = Path(temp) / "cards.json", Path(temp) / "cards.csv"
        source.write_text(json.dumps([card], ensure_ascii=False), encoding="utf-8")
        command = [sys.executable, str(Path(__file__).with_name("export_anki.py")), str(source), str(target)]
        subprocess.run(command, check=True, capture_output=True)
        assert target.read_text(encoding="utf-8") == encoded
        assert subprocess.run(command, capture_output=True).returncode != 0
        assert target.read_text(encoding="utf-8") == encoded  # Existing output is never overwritten.
    print("CSV round-trip, validation, CLI and overwrite checks passed")


if __name__ == "__main__":
    main()
