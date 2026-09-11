# Specialized workflows

Read only the section matching the current request. All branches inherit the grounding, Lieflat style, output, and browser-verification rules in `SKILL.md`.

## General explainer

Use for architecture, a technical concept, a comparison, a timeline, or a data story without a more specific review mode.

1. State the page's main claim and audience.
2. Inventory the source facts and group them by relationship, comparison, sequence, or evidence.
3. Pick one dominant representation and add supporting cards or tables only where they reveal a different fact.
4. Cite source paths, links, or data provenance near the claim they support.

Completion: every source-backed claim is represented once, and removing any major visual would remove useful information.

## Diff review

Resolve the requested branch, commit, range, PR, or `HEAD`. With no argument, compare the working tree against the repository's default branch.

Gather diff stats, name-status, changed files, line counts, public API/type/function changes, dependencies/config, tests, docs, and commit messages. Read each changed file plus the surrounding paths needed to validate behavior.

Include:

1. Executive summary and factual scope.
2. Full changed-file map.
3. Architecture impact when relationships changed.
4. Before/after behavior.
5. Risks across correctness, tests, compatibility, security/privacy, performance, and maintainability.
6. Coupling or migration concerns.
7. Merge-readiness verdict, blockers, and bounded follow-ups.

Use red for removed/before, green for added/after, amber for modified/risk, and blue only for neutral context. These semantic colors are the exception to the page palette and must remain sparse and labeled.

Completion: every changed public contract and every material risk is tied to inspected evidence.

## Plan review

Read the plan in full. Extract its goals, assumptions, files, symbols, interfaces, migrations, tests, rollout notes, and stated risks. Inspect every referenced path plus likely importers or dependents.

Include:

1. Plan summary and scope.
2. Accuracy verdict: correct, stale, risky, unsupported, or missing.
3. Current affected architecture.
4. Matching proposed architecture.
5. Gap/risk matrix.
6. File-level corrections where needed.
7. A simpler corrected plan.
8. Approve, revise, or reject with evidence.

Completion: each proposed change is checked against current repository truth, including test style and compatibility impact.

## Fact-check an existing document

Read the target HTML or Markdown and extract verifiable claims about paths, symbols, behavior, architecture, data flow, APIs, commands, dependencies, tests, history, performance, and security. Skip subjective design opinions.

Classify each claim as verified, corrected, unsupported, or unverifiable. Reinspect the actual source or history for every classification. Preserve the document's structure and Lieflat style when correcting it. Add a compact verification summary listing what was checked and changed.

Completion: every extracted factual claim has a classification and supporting evidence; no unsupported claim remains presented as fact.

## Project recap

Inspect project identity files, top-level structure, current git state, recent commits, active branches, relevant TODO/FIXME markers, build/config files, and key entry points. Focus on what a returning developer needs to rebuild the mental model.

Include:

1. Project identity, stack, and entry points.
2. Current architecture snapshot.
3. Grouped recent activity.
4. Working-tree, branch, blocker, and TODO state.
5. Module, data-flow, test, and deploy mental model.
6. Risks and cognitive debt.
7. Useful commands and files.
8. Evidence-bounded likely next steps.

Completion: the recap distinguishes verified current state from inference and contains enough evidence to resume work without rereading raw history.

## HTML slides

Use slides only when the user explicitly requests a presentation or deck. Start from `templates/slides.html`.

Before writing, inventory the source, map every source item to a slide, choose a narrative arc, and assign a composition. Use title, divider, content, split, diagram, dashboard, table, code, quote, or full-bleed compositions as needed. Vary layouts; add slides instead of shrinking or dropping content.

Each slide is one `100dvh` viewport with no page scrolling. Preserve previous/next controls, count and progress, keyboard navigation, reader rail, outline/help dialogs, hash deep links, and resume state. At the target viewport and a short landscape viewport, fix every overflow marker before delivery.

Completion: all source items are mapped, every slide fits, navigation works by mouse and keyboard, and reduced motion preserves access to all content.
