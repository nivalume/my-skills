# Prompt Engineering — Best Practices & Navigation

This file is the entry point for the prompt-generator skill's reference library.
Read this first, then follow links to model-specific or technique-specific files as needed.

---

## Navigation

### By Target Model

Different models have meaningfully different prompt preferences. When the user specifies a target model, read the corresponding file alongside this one.

| Model | Key preference | File |
|---|---|---|
| **Claude** | System role first · XML structure · 3–5 few-shot · thinking/effort before CoT | `model_claude.md` |
| **Gemini** | Direct + short · separate task/constraints/format · schema for structured output | `model_gemini.md` |
| **OpenAI / ChatGPT** | Instructions first · eliminate conflicts · one format example · match reasoning effort to task | `model_openai.md` |

If no model is specified, default to Claude conventions (XML tags, system prompt, examples in `<examples>` tags).

### By Technique

When the user's request calls for a specific prompting technique, read the relevant file for design details, examples, and when-to-use guidance.

| Technique | When to read | File |
|---|---|---|
| **Zero-shot** | No examples needed; task is well-known or simple | `technique_zero_shot.md` |
| **Few-shot** | Consistent format required; zero-shot is unreliable | `technique_few_shot.md` |
| **Chain-of-thought** | Multi-step reasoning, arithmetic, logic | `technique_chain_of_thought.md` |
| **Self-consistency** | CoT is set up but accuracy is still insufficient; math / logic tasks | `technique_self_consistency.md` |
| **Generated knowledge** | Commonsense / world knowledge tasks; model has the facts but doesn't surface them reliably | `technique_generated_knowledge.md` |
| **Meta prompting** | Well-defined solution structure; token budget is tight; model has domain knowledge but needs structural scaffolding | `technique_meta_prompting.md` |

**Technique selection order:** zero-shot → few-shot → CoT → self-consistency. Use generated knowledge when the task requires world knowledge that CoT alone doesn't reliably activate. Use meta prompting when structure matters more than content examples.

---

## Universal Principles

These apply regardless of model or technique.

### Be Clear and Direct

Specify the task, output format, length, constraints, and tone explicitly. Vague prompts produce variable output.

- Replace qualitative limits with concrete ones: "3–5 sentences" not "short."
- Use numbered steps when order matters.
- Golden rule: if a colleague with no context would be confused by your prompt, the model will be too.
- Request "above and beyond" explicitly: "Include as many relevant features as possible."

### Add Context / Motivation

Explain *why* a constraint exists. Models generalize from reasoning, not just rules.

```
❌ NEVER use ellipses

✅ Your response will be read aloud by a TTS engine — never use ellipses
   since the engine won't know how to pronounce them.
```

### Use Positive Framing

Tell the model what to do, not only what to avoid.

```
❌ Don't use markdown or bullet points.

✅ Write in smoothly flowing prose paragraphs.
   Reserve code blocks for code samples only.
```

### Long Context: Material First, Query Last

Across all major models, placing long documents or data above the query improves response quality. For Claude this can be up to 30%; for GPT-4o the gain at 64k tokens can recover ~15 percentage points of accuracy.

When context is very long, repeat the core task requirement just before the query:

```
[Large context block]

Reminder: answer only based on the text above, in one sentence.

Q: What caused the authentication failure?
```

---

## Output Format Control

### Enforce format via structure, not prohibition

Three reliable patterns (all models):

**1. Positive prose instruction:**

```
Write in clear, flowing prose. Use plain text only.
Reserve markdown for inline code and code blocks exclusively.
```

**2. XML output container (Claude-preferred):**

```
Write your analysis in <analysis> tags, followed by your recommendation in <recommendation> tags.
```

**3. Completion prefix (locks format):**

```
Classify the ticket and return:

{
  "category":
```

### Avoid preambles

```
Respond directly without preamble.
Do not start with "Here is...", "Based on...", "Certainly!", or similar phrases.
```

---

## Examples (Few-Shot)

- **3–5 examples** dramatically improve accuracy and consistency for format-sensitive tasks.
- Wrap in `<example>` / `<examples>` tags (Claude convention; also works for GPT and Gemini).
- Make examples **relevant** (mirror real use case), **diverse** (cover edge cases), **consistent** (identical formatting across all examples).
- For reasoning tasks, include reasoning steps in examples — Claude uses `<thinking>` tags; GPT/Gemini accept inline step-by-step reasoning.

---

## Reasoning Depth

All three major models now have a reasoning depth control. Match it to task complexity — over-provisioning wastes tokens without improving results.

| Model | Parameter | Simple tasks | Complex tasks |
|---|---|---|---|
| Claude | `effort` via API | `low` / `medium` | `high` / `xhigh` |
| OpenAI reasoning models | `reasoning.effort` | `none` / `low` | `medium` / `high` |
| Gemini 3 | temperature (keep at 1.0) | — | "Think step by step" in prompt |

When reasoning controls are not available (prompt-only), add `"Think step by step."` as a zero-shot CoT trigger. For higher reliability, use few-shot CoT examples. See `technique_chain_of_thought.md`.

---

## Prompt Component Checklist

When generating a complete prompt, consider:

- [ ] **Role** — Who is the model in this context? (system prompt for Claude; instruction block for GPT/Gemini)
- [ ] **Context / Background** — Why does this task matter?
- [ ] **Instructions** — What exactly should the model do? (numbered steps if sequential)
- [ ] **Constraints** — What must be avoided or respected? (no conflicts between rules)
- [ ] **Examples** — 3–5 diverse examples wrapped in `<examples>` tags
- [ ] **Input placeholder** — `{{USER_INPUT}}` or `<input>` tag for template prompts
- [ ] **Output format** — Format, length, wrapping tags or schema
- [ ] **Self-check** — Ask the model to verify before finishing (accuracy-critical tasks)

---

## Prompt Types Reference

| Type | Use when | Key pattern |
|---|---|---|
| **System prompt** | Persistent behavior across a session | Role + constraints + format defaults |
| **User turn prompt** | Single task or query | Context → task → output format |
| **Few-shot prompt** | Consistent format or tone required | `<examples>` with 3–5 input/output pairs |
| **Chain-of-thought** | Complex reasoning, math, logic | Reasoning steps in examples; or "Think step by step" |
| **Self-consistency** | CoT accuracy insufficient | Multiple sampled paths + majority vote |
| **Agentic prompt** | Multi-step autonomous tasks | State management + tool use + safety guardrails |
| **RAG / long-context** | Document-grounded answers | Docs first, query last, repeat constraint before query |
| **Structured output** | JSON / schema-constrained response | Schema definition + "return only valid JSON" |

