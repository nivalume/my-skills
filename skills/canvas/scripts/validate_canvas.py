#!/usr/bin/env python3
"""Check the Canvas template contract; not a JavaScript sandbox or visual audit."""
import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

TEMPLATE = Path(__file__).resolve().parents[1] / "assets" / "canvas.html"
VOID = {"meta", "br", "hr", "img", "input", "wbr", "col"}
TAGS = set("html head meta title style body a div header main nav section article aside footer h1 h2 h3 p ul ol li dl dt dd span strong em b i small code pre blockquote figure figcaption table caption colgroup col thead tbody tfoot tr th td details summary label input select option textarea button form fieldset legend output progress meter time abbr br hr img wbr script svg g defs marker path rect circle ellipse line polyline polygon text tspan desc".split())


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__(convert_charrefs=True)
        self.nodes, self.stack, self.errors = [], [], []
        self.doctype = False
        self.feed(source)
        self.close()
        if self.stack:
            self.errors.append("Unclosed elements: " + ", ".join(n["tag"] for n in self.stack))

    def handle_decl(self, decl):
        self.doctype = decl.lower() == "doctype html"

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if len(attributes) != len(attrs):
            self.errors.append(f"Duplicate attribute on <{tag}>")
        node = {"tag": tag, "attrs": attributes, "text": "", "parent": self.stack[-1] if self.stack else None}
        self.nodes.append(node)
        if tag not in VOID:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1]["tag"] != tag:
            self.errors.append(f"Mismatched closing tag: </{tag}>")
        else:
            self.stack.pop()

    def handle_data(self, data):
        for node in self.stack:
            node["text"] += data

    def select(self, tag, parent=None):
        return [n for n in self.nodes if n["tag"] == tag and (parent is None or n["parent"] and n["parent"]["tag"] == parent)]


def validate(source):
    doc, base = Document(source), Document(TEMPLATE.read_text(encoding="utf-8"))
    errors = doc.errors[:]
    if not doc.doctype:
        errors.append("Missing HTML5 doctype")
    if re.search(r"\{\{[A-Z_]+\}\}", source):
        errors.append("Unfilled template slots")
    for tag in ("html", "head", "body", "title", "h1", "main"):
        if len(doc.select(tag, "head" if tag == "title" else None)) != 1:
            errors.append(f"Expected exactly one <{tag}>")
    for tag in ("title", "h1", "main"):
        if not any(n["text"].strip() for n in doc.select(tag, "head" if tag == "title" else None)):
            errors.append(f"Empty <{tag}>")
    html = doc.select("html")
    attrs = html[0]["attrs"] if html else {}
    if not re.fullmatch(r"[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*", attrs.get("lang") or ""):
        errors.append("Set a language tag on <html>")
    if attrs.get("dir") not in ("ltr", "rtl"):
        errors.append("Set dir to ltr or rtl")
    if attrs.get("data-canvas-layout") not in ("docs", "report"):
        errors.append("Choose docs or report layout")
    required_meta = [n["attrs"] for n in base.select("meta")]
    actual_meta = [n["attrs"] for n in doc.select("meta")]
    if actual_meta != required_meta:
        errors.append("Keep template metadata and offline CSP unchanged")
    styles = doc.select("style")
    canonical_css = base.select("style")[0]["text"]
    if len(styles) != 1 or styles[0]["attrs"] != {"id": "canvas-base"} or styles[0]["text"] != canonical_css:
        errors.append("Base CSS changed or extra stylesheet added; copy the template CSS verbatim")
    classes = set(re.findall(r"\.([a-z][a-z0-9-]*)", canonical_css))
    tokens = set(re.findall(r"(--[a-z0-9-]+)\s*:", canonical_css))
    ids = [n["attrs"]["id"] for n in doc.nodes if "id" in n["attrs"]]
    if len(ids) != len(set(ids)) or any(not i or re.search(r"\s", i) for i in ids):
        errors.append("IDs must be nonempty, unique, and contain no whitespace")
    if not any(n["attrs"].get("id") == "canvas-main" for n in doc.select("main")):
        errors.append("Keep main#canvas-main")
    for cls, tag, parent_class in (("page", "div", None), ("page-header", "header", "page"), ("layout", "div", "page"), ("content", "main", "layout"), ("skip-link", "a", None)):
        nodes = [n for n in doc.nodes if cls in (n["attrs"].get("class") or "").split()]
        if len(nodes) != 1 or nodes[0]["tag"] != tag:
            errors.append(f"Keep the template's {tag}.{cls}")
        elif parent_class and (not nodes[0]["parent"] or parent_class not in (nodes[0]["parent"]["attrs"].get("class") or "").split()):
            errors.append(f"Keep .{cls} inside .{parent_class}")
    for node in doc.nodes:
        tag, a = node["tag"], node["attrs"]
        if tag not in TAGS:
            errors.append(f"Unsupported element: <{tag}>")
        unknown = set((a.get("class") or "").split()) - classes
        if unknown:
            errors.append("Unknown component classes: " + ", ".join(sorted(unknown)))
        if any(k == "style" or k.startswith("on") or k in {"srcset", "background", "bgcolor", "font-size", "font-family", "font-weight"} for k in a):
            errors.append(f"Inline styling/event handler or resource override on <{tag}>")
        for key in ("color", "fill", "stroke"):
            value = a.get(key)
            if value and value not in {"none", "currentColor"} and not re.fullmatch(r"var\(--[a-z0-9-]+\)", value):
                errors.append(f"Use semantic tokens/currentColor for {key}")
            elif value and value.startswith("var(") and value[4:-1] not in tokens:
                errors.append(f"Undefined color token: {value}")
        if "src" in a and not (tag == "img" and (a["src"] or "").startswith("data:image/")):
            errors.append(f"External resource on <{tag}>")
        if tag == "img" and "alt" not in a:
            errors.append("Image needs alt text (empty for decorative images)")
        for key in ("href", "xlink:href"):
            if key not in a:
                continue
            href = a[key] or ""
            if tag != "a" or re.search(r"[\x00-\x20]", href) or urlsplit(href).scheme.lower() not in {"", "https", "http", "file", "mailto"}:
                errors.append(f"Unsupported link: {href}")
            if href.startswith("#") and unquote(href[1:]) not in ids:
                errors.append(f"Broken anchor: {href}")
        for key in ("aria-labelledby", "aria-describedby"):
            if key in a and any(ref not in ids for ref in (a[key] or "").split()):
                errors.append(f"Broken {key} reference")
        if tag == "th" and a.get("scope") not in {"col", "row", "colgroup", "rowgroup"}:
            errors.append("Table headers need scope")
        if tag == "svg" and (not a.get("viewbox") or not (a.get("aria-label") or a.get("aria-labelledby") or a.get("aria-hidden") == "true")):
            errors.append("SVG needs viewBox and an accessible name (or aria-hidden)")
        if tag == "script":
            if a.get("type", "") not in {"", "text/javascript", "application/json"}:
                errors.append("Use classic inline JavaScript or embedded JSON")
            # ponytail: literal lint only; computed JS needs browser review, not more regexes.
            if a.get("type") != "application/json" and re.search(r"\b(fetch|XMLHttpRequest|WebSocket|EventSource|importScripts|eval)\s*\(|\bimport\s*[(\"'{*]|\.style\b|\b(?:insertRule|adoptedStyleSheets)\b", node["text"]):
                errors.append("Script contains network/loading or style mutation; use native DOM interactions")
    if attrs.get("data-canvas-layout") == "docs":
        navs = [n for n in doc.select("nav") if "toc" in (n["attrs"].get("class") or "").split()]
        if len(navs) != 1 or not navs[0]["attrs"].get("aria-label"):
            errors.append("Docs layout needs one nav.toc with a localized aria-label")
        sections = [n for n in doc.select("section") if n["parent"] and n["parent"]["tag"] == "main"]
        for section in sections:
            section_id = section["attrs"].get("id")
            if not section_id:
                errors.append("Docs sections need IDs")
            elif not any(n["tag"] == "a" and n["attrs"].get("href") == "#" + section_id and ancestor(n, "nav") for n in doc.nodes):
                errors.append(f"Docs section missing from TOC: {section_id}")
        if not sections:
            errors.append("Docs layout needs content sections")
    return list(dict.fromkeys(errors))


def ancestor(node, tag):
    parent = node["parent"]
    while parent:
        if parent["tag"] == tag:
            return True
        parent = parent["parent"]
    return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("html", type=Path)
    args = parser.parse_args()
    try:
        errors = validate(args.html.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        errors = [str(exc)]
    print("\n".join("FAIL: " + e for e in errors) if errors else "PASS: Canvas template contract (visual, data, and script behavior need browser review)")
    raise SystemExit(bool(errors))
