---
name: canvas
description: >-
  Create or edit standalone HTML canvases for analytical reports, charts,
  tables, timelines, architecture diagrams, API references, documentation
  walkthroughs, and interactive explorations using a shared HTML template.
  Use when the user requests a canvas or a durable visual artifact, including
  structured findings from tools. Follows Cursor Canvas design guidance,
  works with any agent, and supports an output path and content language.
---

# Canvas

A canvas is one self-contained `.html` file that opens directly in a browser, including offline. Preserve Cursor Canvas's flat, minimal, purposeful design and content-first composition. Author with standard HTML, CSS, inline SVG, and optional vanilla JavaScript; no editor runtime, SDK, build step, or agent-specific tool is required. “Canvas” names the artifact, not a requirement to use the HTML `<canvas>` element.

## Standard and template contract

Read [assets/canvas.html](assets/canvas.html) before authoring. This is the canonical implementation of the design system, not an optional visual reference. Start every new canvas from that file; keep its base stylesheet, metadata, and page shell unchanged. Both document and report layouts use this same template.

- Fill the template slots with content; compose the existing classes for sections, cards, tables, notices, forms, and SVG charts. Do not add stylesheets, inline styles, new component classes, or JavaScript that changes styles or injects CSS. Scripts may update content, native attributes such as `hidden`/`aria-pressed`, and toggle existing classes.
- SVG coordinates, paths, and dimensions may vary with the data. Use the template's chart/series classes and semantic token colors. Prefer a 600-unit-wide viewBox to match the template's minimum chart width; verify rendered labels stay readable. Wrap charts in `.chart-wrap` so narrow screens scroll instead of shrinking labels to illegibility. Give scrollable chart/table wrappers `tabindex="0"`, `role="region"`, and a localized accessible name for keyboard access.
- Keep one shared visual standard. If an explicitly requested design cannot be expressed with existing components, update the canonical template and its version deliberately, validate the change, and reuse it; do not quietly fork the stylesheet inside one output.
- Run [scripts/validate_canvas.py](scripts/validate_canvas.py) against every output. It checks the exact base CSS and metadata, fixed shell, known component classes, language metadata, IDs/anchors, basic table/SVG accessibility, and common external dependencies. The embedded Content Security Policy also blocks automatic network connections/resource loading; normal source links still work.
- Static checks do not prove correct data, good composition, complete translation, or arbitrary JavaScript behavior. Browser review remains part of delivery. This is a template contract, not a sanitizer or a pixel-identical rendering guarantee across browsers and system fonts.

The retained `sdk/*.d.ts` files are historical Cursor interface/design references only. They contain no runtime implementations and are not dependencies of generated HTML. Use the canonical template as the source of truth.

## Workflow

### 1. Decide whether to use a canvas

The trigger is **user intent**, not response shape. Would the user benefit from viewing this output as its own durable artifact outside the transcript?

Use a canvas for an explicit canvas request or new standalone analytical output:
- Quantitative analyses, metrics breakdowns, billing investigations, and financial reports.
- Security audits, architecture reviews, cross-system findings, and dependency diagrams.
- Structured tool results where the data itself is the deliverable.
- Large tables, timelines, interactive explorations, and repeatable local tools.
- Documentation overviews, architecture walkthroughs, API references, runbooks, and navigable versions of long documents.

Skip it for short factual answers, targeted debugging, code fixes, drafted messages, or tool queries that are only intermediate steps. Respect a requested deliverable or destination: “create a Datadog dashboard” means that dashboard. Do not create a second artifact when editing an existing one; when the existing artifact is an HTML canvas, update it in place.

### 2. Gather sources and choose the composition

Accept Markdown files/directories, a document URL, an inline outline, codebase material, or structured analytical data. Read the relevant source before composing the page; retain its hierarchy, examples, caveats, and cross-references. Clearly distinguish source facts from interpretation.

**Docs layout** (`data-canvas-layout="docs"`) incorporates the [Docs Canvas workflow](https://github.com/cursor/plugins/blob/main/docs-canvas/skills/docs-canvas/SKILL.md):
1. **Overview:** lead with the answer or purpose, then summarize scope and audience in the page header. Keep it compact.
2. **Navigation:** use one localized `nav.toc` with anchor links to every top-level body section. It is sticky on wide screens and moves above the content on narrow screens. Assign unique, stable IDs; convert links between included documents to anchors.
3. **Body:** put each logical unit in a direct child `<section id="…" class="section">` of `main`. Mix prose, small runnable code examples, architecture diagrams, parameter tables, callouts, and disclosures as the topic needs. Native links replace editor-specific code references; include repository/line permalinks when available. Use escaped code, with the existing tone classes for selective highlighting if helpful. Render diagrams as inline SVG rather than loading Mermaid at runtime.
4. **References:** place relevant docs, source files, RFCs, and external sources in a `footer.references`. Identify the input material when it has no URL. Omit the block only when no source material applies; never invent links.

**Report layout** (`data-canvas-layout="report"`) uses the same header and component styles without the documentation sidebar. Lead with the finding, give the primary plot/table most of the space, and place supporting context in `.main-aside`, `.grid`, or open sections. Preserve source captions and transformations. Do not force analytical output into a documentation outline.

Choose from the user's intent; an explicit layout choice takes precedence. Both layouts keep the same typography, colors, spacing, components, and output contract.

### 3. Resolve output location and language

Accept these options in natural language or as named values; they are instructions, not a CLI:

| Option | Behavior | Default |
| --- | --- | --- |
| `output_path` | An absolute or workspace-relative `.html` filename, or an output directory. For a directory, choose a descriptive kebab-case `.html` filename inside it. | `canvases/<descriptive-name>.html` under the current workspace, or current working directory when there is no workspace. |
| `layout` | `docs` for navigable documentation or `report` for analytical output. | Infer from the task. |
| `language` | Content language, such as `zh-CN`, `en`, `ja`, “简体中文”, or “English”. | The language of the user's request. |

- Honor the specified location; resolve relative paths from the workspace/current working directory, never the skill's installation folder. Expand `~` to the actual home directory when supported. Create missing parent directories using the environment's available file tools.
- When updating an existing canvas, keep its path and language unless the user requests a change. For a new artifact, avoid overwriting an unrelated existing file; choose a descriptive filename with a numeric suffix on collision.
- Set `<html lang="…">` to the resolved language tag; set `dir="rtl"` for right-to-left languages. Translate titles, prose, controls, chart labels, captions, tooltips, and accessibility labels consistently. Preserve identifiers, code, proper names, and source series names; add a translated explanation when useful.
- Format displayed numbers and dates for the output locale, using `Intl.NumberFormat` and `Intl.DateTimeFormat` when JavaScript is needed. Preserve source values, currency, units, and time zone; changing language does not convert the data.
- Do not ask for these options when defaults suffice. For example: “用 Canvas 展示这份分析，输出到 `reports/usage.html`，语言用英文” means that exact relative filename with English content.

### 4. Write the canvas

Actually create the file with the agent's available file-writing tools. Do not stop at a proposed path or a code snippet. If the environment cannot write files, provide the complete HTML for saving and state that no file was created.

Fill these slots in a copy of the template:

| Slot | Content |
| --- | --- |
| `LANG`, `DIR`, `LAYOUT` | Resolved language tag, `ltr`/`rtl`, and `docs`/`report`. |
| `TITLE`, `SKIP_LABEL` | Escaped plain text in the output language; `TITLE` fills both the browser title and H1. |
| `OVERVIEW` | Short introductory HTML with purpose, scope, and audience or the report's main finding. |
| `TOC` | Docs: a `nav.toc` with a localized `aria-label` and links to section IDs. Report: empty string. |
| `CONTENT` | The actual sections, using the template's component classes. |
| `REFERENCES` | A `footer.references` containing source references, or empty when inapplicable. |
| `SCRIPT` | Optional complete inline `<script>` element, otherwise empty. |

Replace slots in one pass so source text is not accidentally interpreted as another slot. Escape text before inserting it into HTML fragments, and never insert untrusted raw markup. All slots must be resolved before delivery; the template itself is not a deliverable.

Use explicit closing tags for non-void elements; the template checker intentionally requires properly nested source markup rather than relying on the browser to repair it.

**File rules:**
- Exactly one `.html` file per canvas. Include `<!doctype html>`, UTF-8 charset, viewport metadata, a meaningful `<title>`, and the resolved document language.
- Embed CSS in `<style>`, data inline, and any JavaScript in a classic inline `<script>`. Embed images as data URLs or inline SVG. Use system fonts.
- No external scripts, stylesheets, fonts, images, imports, packages, sidecar data, or network requests. No `fetch()`, CDN dependencies, React, JSX, or TypeScript requiring compilation. Source hyperlinks are allowed; the page must not load them to render.
- All initial content and interactions must work when the file is opened via `file://`. Gather any needed source data with the agent's available tools before writing; the delivered HTML is a snapshot, not a live connection.
- Use semantic HTML and native controls first. Add JavaScript only for useful filtering, sorting, selection, calculations, or other requested interactions. Do not imitate editor actions such as opening an agent conversation.
- Keep interaction state in memory by default. If persistence is requested, do not rely on browser storage being available for local files: handle storage failures and offer an explicit data download for user-authored content that must survive closing or moving the file.
- Escape source text and attribute values when generating markup. Insert untrusted strings with `textContent`, not `innerHTML`; allow only appropriate link protocols. When embedding serialized JSON in a script element, escape `<` as `\u003c` so source text cannot close the script tag.

**Never render empty artifacts.** Omit sections, charts, and tables with no underlying content. Do not fill space with placeholders, TODOs, invented sample data, zeroed rows, or empty chart frames. Real zero values are valid data. If the entire canvas lacks source content, explain what is missing and request it instead of producing an empty file. A user-applied filter may show a concise localized “no matches” message with a way to reset it.

**Label every plot.** A reader opening the file alone must understand what it shows:
- A title naming the specific metric, such as “API error rate by service”.
- Axis labels and units on both axes where axes exist; label categories and values for pies or other axis-free charts.
- A legend for multiple series, preserving their exact source names.
- A small caption with the source and time range, including the time zone where relevant. State transformations such as mean, p95, normalization, or smoothing. Do not invent unavailable provenance; identify what is unspecified.
- Tables need descriptive headers, units, and source context too.

### 5. Apply Cursor's design guidance

Be creative with composition, while keeping surfaces flat, minimal, and purposeful. Primary content gets more space, a stronger heading, and deliberate accent color. Supporting content stays compact. One thing should stand out when squinting at the page.

**Native equivalents of Cursor's building blocks:**

| Building block | HTML approach and retained guidance |
| --- | --- |
| Stack, Row, Grid | CSS flex columns/rows and Grid. Use Grid for aligned columns; collapse to a readable single column on narrow screens. |
| H1, H2, H3, Text | One page heading, then section/subsection headings and paragraphs. Use 24/30px, 18/24px, 16/22px heading size/line-height; body 14/20px, small text 12/16px. |
| Card, CardHeader, CardBody | A subtle bordered section for a named entity such as a file or service. Compact 12px header labels; no oversized or bold headings stuffed into headers. Do not nest cards or wrap every text section in a card. |
| Table | Native `<table>` with scoped headers, numeric alignment, and a horizontally scrollable wrapper when needed. Put directly under its heading; no extra card unless it belongs to a named entity. |
| Stat, Pill, Callout | Compact labeled metrics, neutral badges, and inline notices. Keep stats beside primary content; use a summary strip only when the data calls for it. Semantic color must carry consistent meaning. |
| CollapsibleSection | Native `<details>` / `<summary>`, borderless for ordinary disclosure rows. |
| Forms, Button, Toggle | Labeled native inputs, selects, textareas, checkboxes, and buttons. Buttons hug their text. Use visible focus outlines and keyboard access; label icon-only controls. |
| BarChart, LineChart, PieChart, UsageBar | Inline SVG for charts; CSS or SVG for proportional usage bars. Bars compare values, lines show trends, pies/donuts show non-negative parts of a whole. Use aligned series, clear scales, and labeled reference lines. |
| DAG layout | Position nodes and directed connectors in inline SVG. Keep hierarchy and reading direction clear; route cycles distinctly and avoid label/edge overlaps. No external layout runtime. |
| DiffView, TodoList | Escaped `<pre>`/`<code>` or structured rows for diffs; semantic lists and labeled checkboxes for tasks. Show status in text or symbols as well as color. |

**Color and spacing.** The template implements semantic CSS tokens, light/dark palettes, typography, spacing, and component styles. Reuse these unchanged instead of selecting a new palette per output. Use `var(--…)` or `currentColor` for SVG paint attributes and `.series-1` through `.series-4` for distinct series. Most elements stay neutral; use an accent or semantic tone only when it carries meaning.

Prefer a 4px spacing rhythm, with 2px for fine adjustments; typical gaps/padding are 8, 12, 16, and 24px. Keep corner radii restrained, usually 4–8px. Use system sans-serif text and tabular numerals for metrics. SVG charts need a responsive `viewBox`, readable labels, and an accessible title/description or equivalent data table. Do not communicate meaning through color or hover alone.

**Forbidden patterns:**
- Gradients, including gradient text.
- Emojis as icons, status indicators, bullets, or section markers.
- Box shadows; use flat surfaces.
- Walls of identical cards; mix open sections and bounded entities.
- Rainbow coloring; use color sparingly and purposefully.
- Text larger than the 24px H1 or oversized card headers.
- Decorative colored borders everywhere; borders should be subtle and structural.

### 6. Verify and deliver

Before delivery:
1. Check visual hierarchy and composition variety; remove forbidden patterns.
2. Check data, calculations, units, chart labels, sources, and language, including interaction-generated text. Omit unsupported content.
3. Run the template check, fixing failures before delivery:

   ```sh
   python3 <skill-dir>/scripts/validate_canvas.py <output.html>
   ```

   Resolve `<skill-dir>` to this skill's actual installation path; quote paths containing spaces. If Python is unavailable, perform the same checks manually and disclose that automated validation was not run. Do not call an unchecked output validated.
4. If browser tools are available, open the actual local file and inspect wide/narrow layouts, light/dark themes, readable charts/tables, keyboard focus, and every included interaction. Check for script errors and unintended network requests. Otherwise inspect the HTML/CSS/JavaScript and state that browser verification was unavailable; do not claim it was tested.

Return a short descriptive Markdown link to the `.html` file using its full resolved absolute path, or the environment's downloadable artifact link when applicable. Say that it can be opened directly in a browser. For the first canvas, briefly explain that it is a standalone visual artifact; for an unsolicited canvas, briefly explain why a durable visual artifact helps. One or two sentences total is enough.

If a canvas is blank or broken, check the saved HTML, script errors, DOM selectors, embedded data, and any accidental external dependencies. Fix and re-open the same file. Do not move it to an editor-managed directory or rely on editor-specific diagnostics.

When changing the template or validator itself, run the dependency-free regression check as well:

```sh
python3 <skill-dir>/scripts/test_validate_canvas.py
```

Docs-specific organization is adapted from Cursor's MIT-licensed Docs Canvas skill. Its license is retained in [LICENSES/docs-canvas-MIT.txt](LICENSES/docs-canvas-MIT.txt). The HTML template and validator here are local implementations, not the Cursor SDK.
