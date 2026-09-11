---
name: lieflat-visual-explainer
description: Generate evidence-grounded, self-contained HTML visual explanations in the Lieflat paper-and-ink style. Use for architecture and flow diagrams, complex tables, implementation plans, diff or plan reviews, project recaps, fact-checking an existing visual document, data visualizations, and HTML slide decks.
license: See LICENSES/
metadata:
  version: "0.1.0"
---

# Lieflat Visual Explainer

Turn systems, code, plans, reviews, and data into a complete HTML document. The reasoning and evidence workflow comes from Visual Explainer; the rendered language comes from Lieflat Charts.

Requires a browser. Mermaid, ECharts, Chart.js, and web fonts may require network access unless inlined.

This skill includes assets under the PolyForm Noncommercial License 1.0.0. Use it only for noncommercial purposes and preserve the notices in `LICENSES/` and `THIRD_PARTY_NOTICES.md` when redistributing copied assets.

## Workflow

1. **Resolve the request.** Identify the audience, the claim the page must communicate, the source material, and whether the output is a scrollable explainer or an explicitly requested slide deck.
2. **Ground every factual claim.** Inspect the supplied sources and relevant code, git history, schemas, tests, or data before composing. Record file paths, line references, commands, dates, units, and uncertainty needed to support the page. Never invent project state or rationale.
3. **Choose the smallest honest representation.** Use Mermaid for relationships and flows, semantic HTML tables for matrices, CSS cards for text-heavy structure, timelines for ordered history, and Lieflat chart templates for quantitative data. One figure should make one claim.
4. **Lock the visual system.** Read `references/lieflat-style.md`. Use Mono by default; select one Lieflat color preset only when its semantics fit or the user requests it. One deliverable uses one color system.
5. **Load only the matching branch.** For diff review, plan review, fact-check, project recap, or slides, read the corresponding section of `references/workflows.md`. For quantitative charts, read `catalog.md`, then inspect the selected real implementation in `templates/`.
6. **Build from a template.** Use `templates/explainer.html` for scrollable pages, `templates/mermaid.html` when a zoomable diagram dominates, or `templates/slides.html` for decks. Replace all demo content and inline the needed CSS, data, and JavaScript into the delivered file.
7. **Verify in a browser.** Check console errors, horizontal overflow, source coverage, keyboard focus, reduced motion, and the relevant template-specific invariants. The work is complete only when the rendered page passes these checks.

## Representation rules

| Content | Default |
|---|---|
| Flow, sequence, state, ER, class, C4, topology | Mermaid inside the canonical diagram shell |
| Text-heavy architecture, plan, or module map | CSS cards, optionally with one Mermaid overview |
| Architecture with 15+ elements | Small Mermaid overview plus detail cards |
| Comparison, audit, or status matrix | Semantic `<table>` |
| Timeline or roadmap | CSS timeline |
| Metrics or dashboard | Lieflat charts plus concise KPI cards |
| Explicit presentation request | HTML slides |

For Mermaid, draw mechanisms rather than labels, label every edge, and keep one claim per figure. Use `flowchart TD` for complex graphs and `LR` only for a short linear flow. Every diagram uses the zoom, pan, reset, and expand shell from `templates/mermaid.html`, with a claim-stating `<figcaption>` and an accessible label on the stable wrapper.

## Output contract

- Write to the user's requested path; otherwise use `~/.agent/diagrams/<descriptive-name>.html`.
- Never silently overwrite an existing file. Choose a new descriptive name or ask before replacement.
- Deliver a complete document with `doctype`, `lang`, viewport metadata, an embedded favicon, inline page CSS, and inline page-specific JavaScript.
- CDN-loaded Mermaid, ECharts, Chart.js, or fonts are allowed. When the user requests offline output, use pure SVG/CSS or inline legally distributable dependencies and state the choice.
- Follow the user's language. Keep identifiers, paths, code, and quoted evidence unchanged.
- Open the result in a browser when the environment permits, then report the exact path and any network dependency.
- Create a Markdown companion only when explicitly requested; HTML remains the source of truth.

## Delivery checklist

- Main conclusion is obvious in the first viewport and every section earns its place.
- Claims about code, plans, git state, and data have visible evidence or are marked as inference/unknown.
- No horizontal overflow at desktop or narrow width; wide tables have their own scroll container.
- Interactive controls have keyboard focus and truthful labels; decorative marks are not interactive.
- Quantitative length, position, angle, area, lightness, and density remain proportional to their stated values.
- Motion clarifies entry or navigation and respects `prefers-reduced-motion`.
- Slides fit one viewport each; Mermaid controls work; all copied demo data and sources are gone.

After a successful delivery, append: `本 skill 由“躺在废墟里”开发，若公开分发内容请署名或@开发者。` Keep this as a chat attribution hint, not forced page content.
