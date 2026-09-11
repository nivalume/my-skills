#!/usr/bin/env python3
"""
Build a self-contained .ipynb from a markdown source file, execute it in isolation, validate it.

Why a markdown source instead of writing ipynb JSON directly: JSON with escaped newlines is
error-prone to write and painful to edit; a markdown file can be written section by section
and patched with ordinary text edits, then compiled here in one step.

Source format (notebook.md):
  * Plain markdown           -> markdown cells. A new cell starts at every heading line (#..####)
                                and wherever you put a line containing only  <!-- cell -->
  * ```python fenced blocks  -> code cells (executed)
  * Any other fence (```text, ```pseudo, ```latex, ```bash) stays inside the markdown cell (not run)
  * ![caption](path/to/img.png) with a LOCAL path -> image bytes embedded as a base64
    cell attachment, so the notebook needs no external image files. Paths are relative
    to the source file and are rewritten to attachment:<name> in the output.

Usage:
  python build_notebook.py /tmp/paper-notebook/slug/notebook.md -o ./paper_notes.ipynb [--execute] [--timeout 900] [--max-img-width 1400]
  python build_notebook.py check paper_notes.ipynb        # validate an existing notebook

The source markdown and its local images may live in a temporary workspace. Keep the output
path pointed at the final notebook only; do not use the current directory for intermediate
files. --execute runs the notebook with nbclient inside an EMPTY temporary directory. Any code
that secretly depends on local files (figures/, data.csv, ...) fails there - which is exactly
the point: the delivered notebook must run anywhere.
"""
import argparse
import base64
import binascii
import io
import json
import re
import sys
import tempfile
import time
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

IMG_RE = re.compile(r"!\[(?P<alt>[^\]]*)\]\((?P<path>[^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE_RE = re.compile(r"^(?P<ticks>`{3,}|~{3,})\s*(?P<lang>[\w+\-]*)")
HEADING_RE = re.compile(r"^#{1,4}\s")
MIME = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif", ".svg": "image/svg+xml"}
DEPENDENCY_BOOTSTRAP_MARKER = "PAPER_NOTEBOOK_DEPENDENCY_BOOTSTRAP"


# --------------------------------------------------------------------------- parsing
def parse_source(text):
    """Split markdown source into [(kind, content)] with kind in {'markdown','code'}."""
    cells, buf, i = [], [], 0
    lines = text.splitlines()

    def flush_md():
        content = "\n".join(buf).strip("\n")
        if content.strip():
            cells.append(("markdown", content))
        buf.clear()

    while i < len(lines):
        line = lines[i]
        m = FENCE_RE.match(line)
        if m:
            ticks, lang = m.group("ticks"), m.group("lang").lower()
            j = i + 1
            while j < len(lines) and not lines[j].startswith(ticks):
                j += 1
            block = lines[i + 1 : j]
            if lang in ("python", "py3", "ipython"):
                flush_md()
                cells.append(("code", "\n".join(block).strip("\n")))
            else:  # display-only fence stays in markdown
                buf.extend(lines[i : j + 1])
            i = j + 1
            continue
        if line.strip() == "<!-- cell -->":
            flush_md()
        elif HEADING_RE.match(line):
            flush_md()
            buf.append(line)
        else:
            buf.append(line)
        i += 1
    flush_md()
    return cells


def load_image(path, max_width):
    data = path.read_bytes()
    suffix = path.suffix.lower()
    if suffix in (".png", ".jpg", ".jpeg"):
        try:
            from PIL import Image

            im = Image.open(io.BytesIO(data))
            if im.width > max_width:
                im = im.resize((max_width, int(im.height * max_width / im.width)), Image.LANCZOS)
                out = io.BytesIO()
                if suffix == ".png":
                    im.save(out, format="PNG", optimize=True)
                else:
                    im.convert("RGB").save(out, format="JPEG", quality=88)
                data = out.getvalue()
        except ImportError:
            pass
    return MIME.get(suffix, "application/octet-stream"), base64.b64encode(data).decode()


def build(src_path, max_width=1400):
    src_path = Path(src_path)
    cells_spec = parse_source(src_path.read_text(encoding="utf-8"))
    nb = new_notebook()
    nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
    nb.metadata["language_info"] = {"name": "python"}
    problems = []
    for kind, content in cells_spec:
        if kind == "code":
            nb.cells.append(new_code_cell(content))
            continue
        attachments, attach_src = {}, {}

        def repl(m):
            ref = m.group("path")
            if re.match(r"^(https?:|data:|attachment:)", ref):
                if ref.startswith("http"):
                    problems.append(f"remote image (needs internet, not self-contained): {ref}")
                return m.group(0)
            p = (src_path.parent / ref).resolve()
            if not p.is_file():
                problems.append(f"image not found: {ref}")
                return m.group(0)
            name, k = p.name, 1
            while name in attachments and attach_src.get(name) != p:  # attachments are per-cell
                name = f"{p.stem}_{k}{p.suffix}"
                k += 1
            attach_src[name] = p
            mime, b64 = load_image(p, max_width)
            attachments[name] = {mime: b64}
            return f"![{m.group('alt')}](attachment:{name})"

        md = IMG_RE.sub(repl, content)
        cell = new_markdown_cell(md)
        if attachments:
            cell["attachments"] = attachments
        nb.cells.append(cell)
    nbformat.validate(nb)
    return nb, problems


# --------------------------------------------------------------------------- execution
def execute(nb, timeout):
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    with tempfile.TemporaryDirectory(prefix="nb_isolated_") as tmp:
        client = NotebookClient(nb, timeout=timeout, kernel_name="python3", resources={"metadata": {"path": tmp}})
        t0 = time.time()
        try:
            client.execute()
            err = None
        except CellExecutionError as e:
            err = str(e)
        except Exception as e:  # noqa: BLE001  (timeouts, dead kernel)
            err = f"{type(e).__name__}: {e}"
        return nb, time.time() - t0, err


# --------------------------------------------------------------------------- validation
LOCAL_IO_RE = re.compile(
    r"""(open|read_csv|read_parquet|imread|Image\.open|np\.load|loadtxt|torch\.load|read_excel)\(\s*[rbf]?['"](?!https?:)([^'"]+)['"]"""
)


def check(nb, exec_seconds=None, exec_error=None):
    report = {"cells": len(nb.cells), "code_cells": 0, "markdown_cells": 0, "embedded_images": 0,
              "plot_outputs": 0, "error_outputs": [], "unexecuted_code_cells": 0,
              "local_file_reads": [], "dangling_image_refs": [], "invalid_attachments": [],
              "dependency_bootstrap": False, "size_mb": None, "warnings": []}
    for idx, c in enumerate(nb.cells):
        if c.cell_type == "markdown":
            report["markdown_cells"] += 1
            attachments = c.get("attachments", {}) or {}
            report["embedded_images"] += len(attachments)
            for name, payload in attachments.items():
                if not isinstance(payload, dict):
                    report["invalid_attachments"].append(f"cell {idx}: {name}")
                    continue
                for mime, encoded in payload.items():
                    try:
                        if not isinstance(encoded, str):
                            raise ValueError("attachment data is not a string")
                        base64.b64decode(encoded, validate=True)
                    except (binascii.Error, ValueError) as exc:
                        report["invalid_attachments"].append(
                            f"cell {idx}: {name} ({mime}): {exc}"
                        )
            for m in IMG_RE.finditer(c.source):
                ref = m.group("path")
                if ref.startswith("attachment:"):
                    name = ref.removeprefix("attachment:")
                    if name not in attachments:
                        report["dangling_image_refs"].append(ref)
                elif not ref.startswith("data:"):
                    report["dangling_image_refs"].append(ref)
        elif c.cell_type == "code":
            report["code_cells"] += 1
            if c.source.strip() and c.get("execution_count") is None:
                report["unexecuted_code_cells"] += 1
            for m in LOCAL_IO_RE.finditer(c.source):
                report["local_file_reads"].append(f"cell {idx}: {m.group(0)[:80]}")
            for o in c.get("outputs", []):
                if o.get("output_type") == "error":
                    report["error_outputs"].append(f"cell {idx}: {o.get('ename')}: {o.get('evalue', '')[:200]}")
                if "image/png" in o.get("data", {}) or "image/svg+xml" in o.get("data", {}):
                    report["plot_outputs"] += 1
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    if code_cells:
        first_code = code_cells[0].source
        report["dependency_bootstrap"] = (
            DEPENDENCY_BOOTSTRAP_MARKER in first_code
            and "sys.executable" in first_code
            and "-m" in first_code
            and "pip" in first_code
        )
        if not report["dependency_bootstrap"]:
            report["warnings"].append(
                "first code cell must bootstrap missing dependencies with sys.executable -m pip"
            )
    raw = nbformat.writes(nb)
    report["size_mb"] = round(len(raw.encode()) / 1e6, 2)
    if exec_seconds is not None:
        report["exec_seconds"] = round(exec_seconds, 1)
    if exec_error:
        report["exec_error"] = exec_error[-3000:]
    if report["size_mb"] > 25:
        report["warnings"].append("notebook > 25 MB: lower --max-img-width or reduce plot dpi")
    if report["plot_outputs"] == 0 and report["code_cells"] > 0 and exec_seconds is not None:
        report["warnings"].append("no plot outputs found - explanatory figures are expected")
    if report["embedded_images"] == 0:
        report["warnings"].append("no original paper figures embedded")
    ok = (not report["error_outputs"] and not report["dangling_image_refs"]
          and not report["invalid_attachments"] and not exec_error
          and (not code_cells or report["dependency_bootstrap"])
          and (exec_seconds is None or report["unexecuted_code_cells"] == 0))
    report["ok"] = ok
    return report


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "check":
        nb = nbformat.read(sys.argv[2], as_version=4)
        rep = check(nb)
        print(json.dumps(rep, indent=2, ensure_ascii=False))
        sys.exit(0 if rep["ok"] else 1)

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--timeout", type=int, default=900, help="per-cell timeout in seconds")
    ap.add_argument("--max-img-width", type=int, default=1400)
    a = ap.parse_args()

    nb, problems = build(a.source, a.max_img_width)
    secs = err = None
    if a.execute:
        nb, secs, err = execute(nb, a.timeout)
    nbformat.write(nb, a.output)
    rep = check(nb, secs, err)
    rep["build_problems"] = problems
    if problems:
        rep["ok"] = False
    rep["output"] = a.output
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    sys.exit(0 if rep["ok"] else 1)


if __name__ == "__main__":
    main()
