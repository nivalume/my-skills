---
name: prompt-generator
description: >
  Generates high-quality, best-practice prompts from a user's intent. Use this skill
  whenever the user wants to: write a prompt, create a system prompt, design a user-turn
  prompt, improve an existing prompt, build a few-shot prompt, craft an agentic task
  prompt, or generally get help turning an idea into a well-structured Claude prompt.
  Also trigger when the user says things like "help me prompt Claude to...", "write a
  prompt that...", "how do I ask Claude to...", "create instructions for...", or "I want
  Claude to behave like...". If the intent is vague or ambiguous, this skill will surface
  clarifying questions with recommended options before generating.
---

# Prompt Generator Skill

Turn a user's intent into a clear, high-quality and follow best-practice prompt.

## Step 1 - Assess Intent Clarity

Before generating anything, evaluate the user's input on two axes:

- **A. Specificity** — Do you know *what task* the prompt should accomplish?
- **B. Context** — Do you know *where* and *how* this prompt will be used?

### When to clarify (ask before generating)

Clarify if **any** of the following are true:

- The task is described in fewer than ~10 words with no examples
- The domain is ambiguous (e.g., "write a helpful prompt" — helpful for what?)
- The output format is unspecified and non-obvious
- The user's own role or audience is unknown and would affect tone/style

**How to ask:** Present 2–4 concrete options per question. Do not ask more than 3 questions at once. Prefer `ask_user_input_v0` for interactive clarification when the tool is available.

**Recommended clarifying questions (pick only what's needed):**

1. **Task domain:** "What should Claude do in this prompt?"
   - Generate / write content
   - Analyze / summarize / extract data
   - Code / debug / refactor
   - Answer questions / research
   - Role-play / take on a persona
   - Other (ask to describe)

2. **Output format:** "How should format its response?"
   - Free prose / conversational
   - Structured (JSON, YAML, XML)
   - Markdown with headers/lists
   - Code only
   - Mixed (prose + code)

3. **Audience / tone:** (only if domain-sensitive)
   - Technical expert
   - General public / non-technical
   - Business / formal
   - Casual / friendly

### When to generate immediately (skip clarification)

Generate without asking if the intent contains:

- A clear task description (verb + object + context)
- Explicit output format or domain
- An example of what good output looks like
- Enough detail that asking would just delay the user

When generating immediately, state any assumptions you make inline at the top of the output.

---

## Step 2 — Read Best Practices

Before generating the prompt, always read:
`/mnt/skills/user/prompt-generator/references/best_practices.md`

This file is the **single entry point** for the reference library. It contains:

- Universal principles that apply across all models
- Navigation table → 3 model-specific files: `model_claude.md`, `model_gemini.md`, `model_openai.md`
- Navigation table → 6 technique files: zero-shot, few-shot, CoT, self-consistency, generated knowledge, meta prompting
- The full prompt component checklist and prompt type reference
**After reading `best_practices.md`**, follow its navigation to read:
- The model-specific file matching the target model (or `model_claude.md` if unspecified)
- Any technique-specific file relevant to the user's request
Do not generate the prompt until you have read the relevant reference files.

---

## Step 3 — Generate the Prompt

### Structure the output as follows

1. **Brief preamble** (1–3 sentences): State the prompt type, target model, any assumptions made, and which optional components were included and why.
2. **The prompt itself**: Presented in a clearly labeled code block (` ```text `) so the user can copy it directly.
3. **Component annotations** (optional, recommended for complex prompts): A short list explaining the key sections and why they were included. Skip for simple prompts.
4. **Suggested variations** (optional): If there are 1–2 meaningful alternative approaches (e.g., a version for a different model, or a lighter version without few-shot), briefly describe and offer to generate one.

---

### Generation rules

#### Universal rules (all models)

- Always include a **clear task description** — verb + object + context
- Always include an **output format specification** — length, structure, tags, or schema
- Always include **context / motivation** when the constraint isn't self-explanatory
- Use **positive framing**: "write in flowing prose" not "don't use bullets"
- Place long input documents / context **above** the query in the prompt
- For templates: include an **input placeholder** (`{{USER_INPUT}}` or `<input>` tag)
- For accuracy-critical tasks: add a **self-check instruction** ("verify before finalizing")
- Eliminate conflicting or contradictory rules — resolve them before generating

#### Claude-specific rules

- Write the **system role first**; put all stable behavioral constraints there
- Use **XML tags** to separate sections: `<instructions>`, `<context>`, `<constraints>`, `<examples>`, `<output_format>`
- Wrap examples in `<example>` / `<examples>` tags; include `<thinking>` tags for CoT examples
- For reasoning tasks: set `effort` level via API before adding manual CoT scaffolding

#### Gemini-specific rules

- Keep instructions **short and direct** — no warm-up phrasing
- Separate task / constraints / output format into **distinct labeled blocks**
- For structured output: define a **schema**, not just a natural language description
- Long context: material first, task last; repeat task requirement before the query

#### OpenAI-specific rules

- Place **instructions at the top**, before any context or data; use `###` or quotes as separators
- Provide **one complete format example** rather than describing the format in prose
- Match `reasoning.effort` to task complexity — do not default to max
- Audit for **conflicting rules** — GPT-5+ models spend reasoning tokens reconciling contradictions

#### Agentic / long-horizon prompts (any model)

- Include **safety guardrails**: ask before irreversible or destructive actions
- Include **state management** guidance: how to track progress across steps
- Define **completion criteria** explicitly

---

## Step 4 — Offer Iteration

After delivering the prompt, always end with a brief offer to refine:

> "Want me to adjust the tone, add few-shot examples, or adapt this for a specific API setup (e.g., system prompt vs. user turn)?"

Do not ask multiple follow-up questions at once — one targeted offer is enough.

---

## Step 5 — Automated Optimization (when explicitly requested)

If the user explicitly asks to **iterate**, **optimize**, or **improve the prompt automatically** (e.g. "run optimization", "iterate on this", "make it better automatically"), switch to the optimization flow:

Read `references/optimizer.md` and follow it end to end.

**Trigger phrases (examples):**

- "optimize this prompt"
- "run the training loop"
- "iterate on it"
- "automatically improve this"
- "run optimization"

**Do not trigger this step** for casual refinement requests like "make it shorter" or "change the tone" — handle those inline as normal edits.

---

## Quick Reference: Prompt Component Checklist

| Component | Include when |
|---|---|
| Role / persona | Task is domain-specific or tone consistency matters |
| Context / motivation | Instructions aren't self-explanatory |
| Numbered steps | Task is sequential or order matters |
| XML section tags | Prompt is long or mixes multiple content types (Claude) |
| `###` / quote separators | Separating instruction from context (OpenAI / Gemini) |
| `<examples>` / few-shot | Format or style consistency is critical |
| Schema / output spec | Structured output required (JSON, YAML, etc.) |
| Input placeholder | Prompt will be reused as a template |
| Self-check instruction | Accuracy, math, or code correctness is critical |
| Safety guardrails | Agentic tasks with irreversible actions |
| Quote-first instruction | Long document / RAG tasks |
| Reasoning effort note | API call for reasoning-heavy tasks (Claude / OpenAI) |

For full details on each component, see `references/best_practices.md`.

