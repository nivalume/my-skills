#!/usr/bin/env python3
"""
Extract text + figures from an academic paper into one unified layout.

Engines, tried in this order under --engine auto:
  1. arxiv   : LaTeX source tarball (original figure files, exact captions/formulas)
  2. mineru  : MinerU CLI if installed (layout model, LaTeX formulas, HTML tables, OCR)
  3. pymupdf : always available; caption-anchored cropping that also catches vector figures

Usage:
  python extract_paper.py <pdf | arXiv id | arXiv URL | source.tar.gz> -o OUT [--engine auto|arxiv|mineru|pymupdf]
  python extract_paper.py crop   <pdf> --page N --bbox x0 y0 x1 y1 -o fig.png [--dpi 200]
  python extract_paper.py render <pdf> --pages 3,5-7 -o OUTDIR [--dpi 150]

`OUT` is an intermediate directory and should be created under a task-specific system
temporary directory, never in the user's current working directory.

Output layout (same for every engine):
  OUT/paper.pdf               the PDF (downloaded or copied)
  OUT/paper.md                full text (markdown); MinerU gives LaTeX formulas
  OUT/latex/                  arXiv source (if available); main_flat.tex = all \\input resolved
  OUT/figures/                extracted figures/tables as images
  OUT/figures.json            [{id, kind, label, number, caption, page, file, source, bbox}]
  OUT/pages/                  low-res page renders for visual checking
  OUT/extraction_report.json  engine used, scanned?, warnings
"""
import argparse
import gzip
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path

try:
    import pymupdf  # PyMuPDF >= 1.24
except ImportError:  # pragma: no cover
    try:
        import fitz as pymupdf
    except ImportError:
        sys.exit("PyMuPDF is required: pip install pymupdf")

CAPTION_RE = re.compile(
    r"^\s*(?P<kind>Figure|Fig\.?|Table|Tab\.?|Algorithm|Exhibit)\s*(?P<num>[A-Z]?\d+(?:\.\d+)?)\s*[:.|\-—–]",
    re.IGNORECASE,
)
ARXIV_RE = re.compile(r"(?:arxiv\.org/(?:abs|pdf|e-print|src)/)?(?P<id>\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)")
UA = {"User-Agent": "paper-notebook-skill/1.0 (academic study use)"}


def norm_kind(k):
    k = k.lower()
    if k.startswith("fig"):
        return "figure"
    if k.startswith("tab"):
        return "table"
    return k


# --------------------------------------------------------------------------- common helpers
def render_pages(pdf_path, out_dir, pages=None, dpi=110):
    doc = pymupdf.open(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    idxs = pages if pages else range(1, doc.page_count + 1)
    written = []
    for n in idxs:
        pix = doc[n - 1].get_pixmap(dpi=dpi)
        p = out_dir / f"page_{n:03d}.png"
        pix.save(p)
        written.append(str(p))
    return written


def crop_region(pdf_path, page_no, bbox, out_png, dpi=200):
    doc = pymupdf.open(pdf_path)
    page = doc[page_no - 1]
    rect = pymupdf.Rect(*bbox) & page.rect
    pix = page.get_pixmap(dpi=dpi, clip=rect)
    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    pix.save(out_png)
    return out_png


def is_scanned(pdf_path, sample=6):
    doc = pymupdf.open(pdf_path)
    n = min(sample, doc.page_count)
    chars = sum(len(doc[i].get_text().strip()) for i in range(n))
    return (chars / max(n, 1)) < 100


def parse_pages_arg(s):
    out = []
    for part in s.split(","):
        if "-" in part:
            a, b = part.split("-")
            out.extend(range(int(a), int(b) + 1))
        elif part.strip():
            out.append(int(part))
    return out


def contact_sheet(figures, base_dir, out_png, cols=3, cell=(440, 330)):
    """All figure crops on one image, so a single visual check covers every figure."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return None
    entries = []
    for f in figures:
        files = f.get("file")
        for fp in ([files] if isinstance(files, str) else (files or [])):
            if (Path(base_dir) / fp).is_file():
                entries.append((f.get("label") or f.get("id"), Path(base_dir) / fp))
    if not entries:
        return None
    rows = (len(entries) + cols - 1) // cols
    sheet = Image.new("RGB", (cell[0] * cols, cell[1] * rows), "#dddddd")
    for i, (label, fp) in enumerate(entries):
        im = Image.open(fp).convert("RGB")
        im.thumbnail((cell[0] - 20, cell[1] - 35))
        c = Image.new("RGB", cell, "white")
        c.paste(im, (10, 25))
        ImageDraw.Draw(c).text((10, 6), f"{label}  [{fp.name}]", fill="red")
        sheet.paste(c, ((i % cols) * cell[0], (i // cols) * cell[1]))
    sheet.save(out_png)
    return str(out_png)


# --------------------------------------------------------------------------- engine: pymupdf
def pymupdf_text(pdf_path):
    try:
        import pymupdf4llm  # optional, better markdown structure

        return pymupdf4llm.to_markdown(str(pdf_path), write_images=False, show_progress=False)
    except Exception:
        doc = pymupdf.open(pdf_path)
        parts = []
        for i, page in enumerate(doc, 1):
            parts.append(f"\n\n<!-- page {i} -->\n\n")
            parts.append(page.get_text("text"))
        return "".join(parts)


def _union(rects):
    r = pymupdf.Rect(rects[0])
    for x in rects[1:]:
        r |= x
    return r


def _block_text(b):
    return " ".join(s["text"] for l in b.get("lines", []) for s in l.get("spans", [])).strip()


def _column_edges(blocks, tol=3):
    """x-positions that several long paragraphs share = text column boundaries."""
    xs0, xs1 = [], []
    for b in blocks:
        if len(b.get("lines", [])) >= 3 and len(_block_text(b)) > 200 and not CAPTION_RE.match(_block_text(b)):
            xs0.append(b["bbox"][0])
            xs1.append(b["bbox"][2])

    def modes(xs):
        xs, out = sorted(xs), []
        i = 0
        while i < len(xs):
            j = i
            while j + 1 < len(xs) and xs[j + 1] - xs[i] <= tol:
                j += 1
            if j - i + 1 >= 2:
                out.append(sum(xs[i : j + 1]) / (j - i + 1))
            i = j + 1
        return out

    return modes(xs0), modes(xs1)


def pymupdf_figures(pdf_path, fig_dir, dpi=200):
    """Caption-anchored cropping.

    Vector figures are drawing commands, not image objects, so plain image extraction misses
    them. Instead: find caption blocks ("Figure 3:"), then grow a region away from the caption
    through graphics (drawings + images) and short label text, stopping at body paragraphs.
    """
    doc = pymupdf.open(pdf_path)
    fig_dir = Path(fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)
    results, warnings, seen = [], [], set()

    for pno, page in enumerate(doc, 1):
        W, H = page.rect.width, page.rect.height
        blocks = [b for b in page.get_text("dict")["blocks"] if b.get("type") == 0]
        graphics = []
        for d in page.get_drawings():
            r = pymupdf.Rect(d["rect"])
            if r.width * r.height < 4 and max(r.width, r.height) < 8:
                continue  # dust
            if r.width > 0.95 * W and r.height > 0.95 * H:
                continue  # page background / frame
            graphics.append(r)
        for info in page.get_image_info():
            graphics.append(pymupdf.Rect(info["bbox"]))
        line_ws = sorted(l["bbox"][2] - l["bbox"][0] for b in blocks for l in b.get("lines", [])
                         if len(" ".join(sp["text"] for sp in l["spans"])) > 40)
        body_line_w = line_ws[int(len(line_ws) * 0.75)] if line_ws else 0.45 * W
        left_edges, right_edges = _column_edges(blocks)
        # "big" boxes: text inside them belongs to the figure (e.g. boxed algorithm summaries)
        big_boxes = [g for g in graphics if g.width > 40 and g.height > 25]

        captions = []
        for b in blocks:
            t = _block_text(b)
            m = CAPTION_RE.match(t)
            if m:
                captions.append((b, m, re.sub(r"\s+", " ", t)))

        for b, m, text in captions:
            kind, num = norm_kind(m.group("kind")), m.group("num")
            label = f"{kind.capitalize()} {num}"
            if label in seen:
                continue
            cap = pymupdf.Rect(b["bbox"])
            full_width = cap.width > 0.55 * W or (cap.x0 < 0.35 * W and cap.x1 > 0.65 * W)
            if full_width:
                xr = (0.03 * W, 0.97 * W)
            elif (cap.x0 + cap.x1) / 2 < W / 2:
                xr = (0.03 * W, W / 2 + 4)
            else:
                xr = (W / 2 - 4, 0.97 * W)

            def in_x(r):
                return r.x1 > xr[0] and r.x0 < xr[1] and (min(r.x1, xr[1]) - max(r.x0, xr[0])) > 0.3 * r.width

            def is_body(bl):
                r = pymupdf.Rect(bl["bbox"])
                if any(box.contains(r) or (box & r).get_area() > 0.8 * r.get_area() for box in big_boxes):
                    return False
                txt = _block_text(bl)
                if CAPTION_RE.match(txt):
                    return True
                nl = len(bl.get("lines", []))
                wide = sum(1 for l in bl.get("lines", []) if (l["bbox"][2] - l["bbox"][0]) > 0.92 * body_line_w)
                aligned_l = any(abs(r.x0 - e) <= 3 for e in left_edges)
                aligned_r = any(abs(r.x1 - e) <= 3 for e in right_edges)
                if left_edges and right_edges:
                    # justified paragraphs touch both column edges; table rows / labels don't
                    return (aligned_l and aligned_r and nl >= 2) or (aligned_l and wide >= 3)
                return wide >= 2 or (wide >= 1 and len(txt) > 350)

            def grow(direction):
                """direction=-1 grows upward from caption top, +1 downward from caption bottom."""
                items = [("g", g) for g in graphics if in_x(g)]
                items += [("t", pymupdf.Rect(bl["bbox"]), bl) for bl in blocks if bl is not b and in_x(pymupdf.Rect(bl["bbox"]))]
                GAP = 28
                if direction < 0:
                    items = [it for it in items if it[1].y1 <= cap.y0 + 3]
                    items.sort(key=lambda it: -it[1].y1)
                    edge = cap.y0
                else:
                    items = [it for it in items if it[1].y0 >= cap.y1 - 3]
                    items.sort(key=lambda it: it[1].y0)
                    edge = cap.y1
                chosen, has_graphic = [], False
                for it in items:
                    r = it[1]
                    near = (r.y1 >= edge - GAP) if direction < 0 else (r.y0 <= edge + GAP)
                    if not near:
                        break
                    if it[0] == "t" and is_body(it[2]):
                        break
                    chosen.append(r)
                    if it[0] == "g":
                        has_graphic = True
                    edge = min(edge, r.y0) if direction < 0 else max(edge, r.y1)
                return chosen, has_graphic

            # figures usually sit above their caption, tables below; try the likely side first
            order = (1, -1) if kind == "table" else (-1, 1)
            region = None
            for direction in order:
                chosen, has_graphic = grow(direction)
                if chosen and (has_graphic or kind == "table"):
                    region = _union(chosen)
                    if direction < 0:
                        region.y1 = min(region.y1, cap.y0 - 1)
                    else:
                        region.y0 = max(region.y0, cap.y1 + 1)
                    if region.height > 12:
                        break
                    region = None
            if region is None:
                warnings.append(f"{label} (page {pno}): no graphics found next to caption - crop manually")
                continue
            above = region.y1 <= cap.y0
            region = pymupdf.Rect(region.x0 - 4, region.y0 - 4, region.x1 + 4, region.y1 + 4)
            if above:
                region.y1 = min(region.y1, cap.y0 - 0.5)
            else:
                region.y0 = max(region.y0, cap.y1 + 0.5)
            region &= page.rect
            fname = f"{kind}_{num.replace('.', '_')}_p{pno}.png"
            page.get_pixmap(dpi=dpi, clip=region).save(fig_dir / fname)
            seen.add(label)
            results.append(
                dict(
                    id=f"{kind}_{num}",
                    kind=kind,
                    label=label,
                    number=num,
                    caption=text,
                    page=pno,
                    file=f"figures/{fname}",
                    source="pymupdf-crop",
                    bbox=[round(v, 1) for v in region],
                )
            )
    return results, warnings


# --------------------------------------------------------------------------- engine: mineru
def mineru_available():
    return shutil.which("mineru") is not None


def run_mineru(pdf_path, work_dir, backend=None, timeout=3600):
    cmd = ["mineru", "-p", str(pdf_path), "-o", str(work_dir)]
    if backend:
        cmd += ["-b", backend]
    print("[mineru] " + " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if proc.returncode != 0:
        raise RuntimeError(f"mineru failed ({proc.returncode}): {proc.stderr[-2000:]}")


def collect_mineru(work_dir, out_dir):
    """Map MinerU's *_content_list.json output into the unified layout."""
    work_dir, out_dir = Path(work_dir), Path(out_dir)
    lists = [p for p in work_dir.rglob("*_content_list.json")]
    if not lists:
        raise RuntimeError("mineru produced no *_content_list.json")
    cl_path = lists[0]
    base = cl_path.parent
    items = json.loads(cl_path.read_text(encoding="utf-8"))
    md_files = [p for p in base.glob("*.md")]
    md = md_files[0].read_text(encoding="utf-8") if md_files else ""

    fig_dir = out_dir / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    results, counter = [], {}
    for it in items:
        t = it.get("type")
        if t not in ("image", "table", "chart", "code") or not it.get("img_path"):
            if t == "code" and it.get("sub_type") == "algorithm":
                cap = " ".join(it.get("code_caption") or [])
                results.append(dict(id=f"algorithm_{len(results)}", kind="algorithm", label=cap[:40], number=None,
                                    caption=cap, page=it.get("page_idx", 0) + 1, file=None,
                                    source="mineru", bbox=it.get("bbox"), body=it.get("code_body")))
            continue
        cap_list = it.get(f"{t}_caption") or it.get("img_caption") or []
        caption = " ".join(cap_list).strip()
        m = CAPTION_RE.match(caption)
        kind = norm_kind(m.group("kind")) if m else ("table" if t == "table" else "figure")
        num = m.group("num") if m else None
        counter[kind] = counter.get(kind, 0) + 1
        src = base / it["img_path"]
        stem = f"{kind}_{num.replace('.', '_')}" if num else f"{kind}_u{counter[kind]:02d}"
        fname = f"{stem}_p{it.get('page_idx', 0) + 1}{src.suffix or '.png'}"
        if src.exists():
            shutil.copy(src, fig_dir / fname)
            md = md.replace(it["img_path"], f"figures/{fname}")
        entry = dict(id=stem, kind=kind, label=f"{kind.capitalize()} {num}" if num else None, number=num,
                     caption=caption, page=it.get("page_idx", 0) + 1, file=f"figures/{fname}",
                     source="mineru", bbox=it.get("bbox"))
        if t == "table" and it.get("table_body"):
            entry["table_html"] = it["table_body"]
        results.append(entry)
    (out_dir / "paper.md").write_text(md, encoding="utf-8")
    return results


# --------------------------------------------------------------------------- engine: arxiv source
def http_get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def unpack_source(blob, dest):
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    if blob[:4] == b"%PDF":
        return False  # arXiv only has the PDF for this paper
    try:
        with tarfile.open(fileobj=io.BytesIO(blob), mode="r:*") as tf:
            safe = [m for m in tf.getmembers() if not (m.name.startswith("/") or ".." in Path(m.name).parts)]
            tf.extractall(dest, members=safe)
        return True
    except tarfile.ReadError:
        data = gzip.decompress(blob) if blob[:2] == b"\x1f\x8b" else blob
        if b"\\documentclass" in data[:20000] or b"\\begin{document}" in data:
            (dest / "main.tex").write_bytes(data)
            return True
    return False


def find_main_tex(src):
    cands = []
    for p in Path(src).rglob("*.tex"):
        t = p.read_text(errors="ignore")
        if "\\documentclass" in t and "\\begin{document}" in t:
            cands.append((len(t), p))
    return max(cands)[1] if cands else None


def flatten_tex(path, root, depth=0):
    if depth > 8:
        return ""
    text = Path(path).read_text(errors="ignore")
    text = re.sub(r"(?<!\\)%.*", "", text)  # strip comments

    def repl(m):
        name = m.group(2)
        for cand in (root / name, root / f"{name}.tex", Path(path).parent / name, Path(path).parent / f"{name}.tex"):
            if cand.is_file():
                return flatten_tex(cand, root, depth + 1)
        return m.group(0)

    return re.sub(r"\\(input|include)\{([^}]+)\}", repl, text)


def _braced(s, start):
    """Return content of the brace group starting at s[start] == '{'."""
    depth, i = 0, start
    while i < len(s):
        if s[i] == "{" and (i == 0 or s[i - 1] != "\\"):
            depth += 1
        elif s[i] == "}" and s[i - 1] != "\\":
            depth -= 1
            if depth == 0:
                return s[start + 1 : i]
        i += 1
    return s[start + 1 :]


def tex_figures(flat, root, fig_dir, dpi=200):
    fig_dir = Path(fig_dir)
    fig_dir.mkdir(parents=True, exist_ok=True)
    gpaths = [root]
    for gp in re.findall(r"\\graphicspath\{((?:\{[^}]*\})+)\}", flat):
        gpaths += [root / g for g in re.findall(r"\{([^}]*)\}", gp)]
    results, warnings = [], []
    counters = {"figure": 0, "table": 0}
    for m in re.finditer(r"\\begin\{(figure\*?|table\*?|wrapfigure)\}(.*?)\\end\{\1\}", flat, re.S):
        env, body = m.group(1), m.group(2)
        kind = "table" if env.startswith("table") else "figure"
        counters[kind] += 1
        num = str(counters[kind])
        cap = ""
        ci = body.find("\\caption")
        if ci >= 0:
            bi = body.find("{", ci)
            if body[ci:bi].strip().endswith("]") or "[" in body[ci:bi]:
                bi = body.find("{", body.find("]", ci))
            cap = re.sub(r"\s+", " ", _braced(body, bi)).strip()
        label = re.search(r"\\label\{([^}]+)\}", body)
        files = []
        for g in re.finditer(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{([^}]+)\}", body):
            ref = g.group(1).strip()
            hit = None
            for gp in gpaths:
                for ext in ("", ".pdf", ".png", ".jpg", ".jpeg", ".eps"):
                    c = gp / f"{ref}{ext}"
                    if c.is_file():
                        hit = c
                        break
                if hit:
                    break
            if not hit:
                warnings.append(f"{kind} {num}: graphics file not found: {ref}")
                continue
            sub = chr(ord("a") + len(files)) if len(re.findall(r"\\includegraphics", body)) > 1 else ""
            out = fig_dir / f"{kind}_{num}{sub}.png"
            try:
                if hit.suffix.lower() == ".pdf":
                    d = pymupdf.open(hit)
                    d[0].get_pixmap(dpi=dpi).save(out)
                elif hit.suffix.lower() in (".png", ".jpg", ".jpeg"):
                    out = out.with_suffix(hit.suffix.lower())
                    shutil.copy(hit, out)
                elif hit.suffix.lower() == ".eps" and shutil.which("gs"):
                    subprocess.run(["gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dEPSCrop", "-sDEVICE=png16m",
                                    f"-r{dpi}", f"-sOutputFile={out}", str(hit)], check=True, capture_output=True)
                else:
                    warnings.append(f"{kind} {num}: cannot convert {hit.name}; will fall back to PDF crop")
                    continue
                files.append(f"figures/{out.name}")
            except Exception as e:  # noqa: BLE001
                warnings.append(f"{kind} {num}: conversion failed for {hit.name}: {e}")
        results.append(dict(id=f"{kind}_{num}", kind=kind, label=f"{kind.capitalize()} {num}", number=num,
                            caption=cap, tex_label=label.group(1) if label else None, page=None,
                            file=files[0] if len(files) == 1 else (files or None), source="arxiv-latex",
                            needs_pdf_crop=not files,
                            tex_body=body.strip() if kind == "table" else None))
    return results, warnings


# --------------------------------------------------------------------------- orchestration
def resolve_input(inp, out_dir, companion_pdf=None):
    """Return (pdf_path or None, arxiv_id or None, local_source_blob or None)."""
    p = Path(inp)
    if companion_pdf and p.is_file() and not p.suffix.lower() == ".pdf":
        dst = out_dir / "paper.pdf"
        shutil.copy(companion_pdf, dst)
        return dst, None, p.read_bytes()
    if p.is_file():
        if p.suffix.lower() == ".pdf":
            dst = out_dir / "paper.pdf"
            if p.resolve() != dst.resolve():
                shutil.copy(p, dst)
            return dst, None, None
        if p.name.endswith((".tar.gz", ".tgz", ".tar", ".gz")):
            return None, None, p.read_bytes()
    m = ARXIV_RE.search(inp)
    if m:
        return None, m.group("id"), None
    sys.exit(f"Cannot interpret input: {inp}")


def main_extract(args):
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    report = dict(input=args.input, engines_tried=[], engine_text=None, engine_figures=None, warnings=[])
    pdf, arxiv_id, src_blob = resolve_input(args.input, out, args.pdf)
    figures = []

    # ---- 1. arXiv source (original figures, exact captions)
    if args.engine in ("auto", "arxiv") and (arxiv_id or src_blob):
        report["engines_tried"].append("arxiv")
        try:
            if arxiv_id and not src_blob:
                src_blob = http_get(f"https://arxiv.org/e-print/{arxiv_id}", timeout=120)
            if arxiv_id and not pdf:
                (out / "paper.pdf").write_bytes(http_get(f"https://arxiv.org/pdf/{arxiv_id}", timeout=120))
                pdf = out / "paper.pdf"
            latex_dir = out / "latex"
            if unpack_source(src_blob, latex_dir):
                main_tex = find_main_tex(latex_dir)
                if main_tex:
                    flat = flatten_tex(main_tex, main_tex.parent)
                    (latex_dir / "main_flat.tex").write_text(flat, encoding="utf-8")
                    figures, w = tex_figures(flat, main_tex.parent, out / "figures")
                    report["warnings"] += w
                    report["engine_figures"] = "arxiv-latex"
                    report["main_tex"] = str(main_tex.relative_to(out))
                else:
                    report["warnings"].append("arXiv source has no main .tex file")
            else:
                report["warnings"].append("arXiv provides no LaTeX source for this paper (PDF only)")
        except Exception as e:  # noqa: BLE001
            report["warnings"].append(f"arXiv source step failed: {e}")
        if not pdf:
            if arxiv_id:
                report["warnings"].append("could not download PDF from arXiv")
            else:
                report["warnings"].append("source tarball given without PDF; pass the PDF too for page renders")

    if pdf is None:
        (out / "extraction_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    report["page_count"] = pymupdf.open(pdf).page_count
    report["scanned"] = is_scanned(pdf)
    if report["scanned"]:
        report["warnings"].append("PDF looks SCANNED (no text layer): use MinerU (OCR) or read pages/ images visually")

    # ---- 2. MinerU
    used_mineru = False
    if args.engine in ("auto", "mineru"):
        if mineru_available():
            report["engines_tried"].append("mineru")
            try:
                run_mineru(pdf, out / "_mineru", backend=args.mineru_backend, timeout=args.timeout)
                mfigs = collect_mineru(out / "_mineru", out)
                used_mineru = True
                report["engine_text"] = "mineru"
                if not figures:
                    figures = mfigs
                    report["engine_figures"] = "mineru"
                else:  # keep LaTeX originals, but store MinerU view too (has page numbers + table HTML)
                    (out / "figures_mineru.json").write_text(json.dumps(mfigs, indent=2, ensure_ascii=False))
            except Exception as e:  # noqa: BLE001
                report["warnings"].append(f"MinerU failed, falling back to PyMuPDF: {e}")
        elif args.engine == "mineru":
            report["warnings"].append("mineru not on PATH (pip install -U 'mineru[all]'); falling back to PyMuPDF")

    # ---- 3. PyMuPDF fallback / gap filling
    if not used_mineru:
        report["engines_tried"].append("pymupdf")
        (out / "paper.md").write_text(pymupdf_text(pdf), encoding="utf-8")
        report["engine_text"] = "pymupdf"
    need_crop = (not figures) or any(f.get("needs_pdf_crop") for f in figures)
    if need_crop and not report["scanned"]:
        crops, w = pymupdf_figures(pdf, out / "figures" if not figures else out / "figures_pdfcrop")
        report["warnings"] += w
        if not figures:
            figures = crops
            report["engine_figures"] = "pymupdf-crop"
        else:
            by_label = {c["label"]: c for c in crops}
            for f in figures:
                if f.get("needs_pdf_crop") and f["label"] in by_label:
                    c = by_label[f["label"]]
                    dst = out / "figures" / Path(c["file"]).name
                    shutil.move(str(out / "figures_pdfcrop" / Path(c["file"]).name), dst)
                    f.update(file=f"figures/{dst.name}", page=c["page"], bbox=c["bbox"], source="arxiv-latex+pdf-crop",
                             needs_pdf_crop=False)
            shutil.rmtree(out / "figures_pdfcrop", ignore_errors=True)

    render_pages(pdf, out / "pages", dpi=args.page_dpi)
    sheet = contact_sheet(figures, out, out / "figures_overview.png")
    if sheet:
        report["figures_overview"] = "figures_overview.png"
    (out / "figures.json").write_text(json.dumps(figures, indent=2, ensure_ascii=False))
    report["n_figures"] = sum(1 for f in figures if f["kind"] == "figure")
    report["n_tables"] = sum(1 for f in figures if f["kind"] == "table")
    report["missing_files"] = [f["label"] for f in figures if not f.get("file") and f["kind"] != "algorithm"]
    (out / "extraction_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))
    print(json.dumps(report, indent=2, ensure_ascii=False))


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "crop":
        ap = argparse.ArgumentParser(prog="extract_paper.py crop")
        ap.add_argument("cmd")
        ap.add_argument("pdf")
        ap.add_argument("--page", type=int, required=True, help="1-based page number")
        ap.add_argument("--bbox", type=float, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"),
                        help="PDF points (72/inch), origin top-left. A 150-dpi render pixel = pt * 150/72")
        ap.add_argument("-o", "--output", required=True)
        ap.add_argument("--dpi", type=int, default=200)
        a = ap.parse_args()
        print(crop_region(a.pdf, a.page, a.bbox, a.output, a.dpi))
        return
    if len(sys.argv) > 1 and sys.argv[1] == "render":
        ap = argparse.ArgumentParser(prog="extract_paper.py render")
        ap.add_argument("cmd")
        ap.add_argument("pdf")
        ap.add_argument("--pages", required=True, help="e.g. 3,5-7 (1-based)")
        ap.add_argument("-o", "--output", required=True)
        ap.add_argument("--dpi", type=int, default=150)
        a = ap.parse_args()
        for p in render_pages(a.pdf, a.output, parse_pages_arg(a.pages), a.dpi):
            print(p)
        return
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("input", help="PDF path, arXiv id/URL, or arXiv source tarball")
    ap.add_argument("-o", "--output", required=True)
    ap.add_argument("--engine", default="auto", choices=["auto", "arxiv", "mineru", "pymupdf"])
    ap.add_argument("--mineru-backend", default=None,
                    help="default: MinerU's own default (hybrid-auto-engine; picks CUDA/MPS). 'pipeline' = CPU-friendly")
    ap.add_argument("--pdf", default=None, help="PDF to pair with a local source tarball input")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--page-dpi", type=int, default=110)
    main_extract(ap.parse_args())


if __name__ == "__main__":
    main()
