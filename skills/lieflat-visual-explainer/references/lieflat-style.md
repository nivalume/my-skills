# Lieflat visual language

Use this reference before writing HTML. `assets/mono-tokens.js` and `assets/color-presets.js` are the authoritative values; inline the selected values into the delivered single-file page.

## Page grammar

- Paper is `#F0EFEB`; ink is `#1C1C1A`. Use the seven-step grey ladder for hierarchy, darkest for the most important data.
- Use Inter with explicit 400/500/600/700/800 weights. Headings are 700, chart values 800, axis labels 600, and source rows uppercase with tracking.
- Cards use 24px radii, no border, no shadow, and no gradient. Separate regions with whitespace and real layout seams.
- A chart card has a conclusion-led heading, a subtitle containing legend/unit/time context, the visual, and a source row.
- Use solid materials. Opacity may encode real density; it is not decoration.
- Keep reading text at least 14px, secondary labels at least 11px, and code at least 12px. If chart labels do not fit, expose detail through truthful hover rather than unreadable type.
- Use one visual system across the whole file. Runtime palette or font pickers exist only when the user asks for them.

## Color systems

Mono is the fallback. A preset is a semantic tool, not an upgrade:

| Data or intent | Preset |
|---|---|
| Ordered or single-series values | porcelain or wire |
| Up to four unordered categories | palm |
| A restrained page with one focus | wire |
| More than six categories or unclear color meaning | Mono |

Use one of Mono, porcelain, palm, wire, or one explicit custom palette per deliverable. Palm supports up to four clean categories and six only with care. A custom palette requires user-provided colors or brand guidance and defines `BG`, `TXT`, `MUT`, `GRID`, and `DATA`, plus `HERO`, `RAMP`, or `CAT` only when needed. Text contrast is at least 4.5:1, large text 3:1, and meaningful boundaries 3:1. Color is never the sole cue.

## Quantitative integrity

- Length and position are directly proportional to value. Bar charts start at zero; use an honest full scale, a labeled detail inset, or a visibly torn bar rather than a broken axis.
- Area uses `sqrt(value)` for radius. Angle, lightness, and density state what they encode.
- Use deterministic sample data through the `rnd(i, k)` token helper. Never use `Math.random()` in a reference or delivered example.
- Titles state the finding rather than the chart type. Subtitles state units, legend, population, and time range.
- Interactive marks correspond to real records. Decorative texture has no hover. More than 50 records or multi-segment paths require hover/pin support with usable hit targets.

## Chart selection

Read `../catalog.md`, classify the data shape, and inspect at least the viable candidates. Default to Lupi Editorial, then Lupi Basics. Use Glance when those cannot encode the data honestly or the user explicitly wants a dashboard, monitoring view, weekly report, or three-second scan. Use Maps only after an explicit map or geographic-distribution request.

After selecting a chart, open its actual source in `../templates/` and reuse the matching card and renderer. Preserve its geometry, encoding, scale, and animation cadence while replacing all data, titles, annotations, legends, and sources. Build a new chart only when no catalog template can encode the data, and inherit the closest template's grammar.

For multiple charts, give each one a distinct claim, avoid repeating templates or silhouettes, and use at most one dark card per four cards. Delete redundant charts instead of filling a quota.

## Mermaid and explanatory layouts

Apply the same paper, ink, grey ladder, type, radius, and no-shadow rules to Mermaid, CSS cards, tables, timelines, and slides. Mermaid uses `theme: "base"` with Lieflat variables. Label every edge, keep diagrams inside the shell from `templates/mermaid.html`, and use dark cards only when the topology materially benefits from them.

Scrollable pages use a summary-first hierarchy and responsive navigation for four or more major sections. Tables retain semantic rows and columns inside an overflow wrapper. Code blocks and file trees are flat reference material, not elevated hero cards.

## Motion and accessibility

Use quick-in, quick-stop entrance motion. Reveal once when content enters the viewport and allow replay only when it helps interpretation. Clear timers before replay. Avoid continuous animation on static content.

Respect `prefers-reduced-motion`, preserve visible keyboard focus, use native buttons for controls, and provide text alternatives. Put each diagram in `<figure>` with a conclusion-led `<figcaption>`; set `role="img"` and the matching `aria-label` on the stable diagram wrapper.
