# Claude Prompt Design Guide

Claude's strong preferences differ meaningfully from Gemini. Claude is trained to follow system prompts as behavioral contracts, responds exceptionally well to XML semantic structure, and uses thinking/effort as the primary lever for reasoning depth before falling back to manual CoT scaffolding.

---

## 1. Write the System Role First

The system prompt is Claude's behavioral contract — it sets persona, scope, constraints, and defaults before the conversation starts. Claude treats it with higher authority than user turns.

Put everything that should be *always true* in the system prompt:

- Role / persona
- Task scope and what's out of scope
- Output format defaults
- Tone and style
- Safety or compliance constraints

```xml
You are a senior backend engineer specializing in Rust and distributed systems.
You review code for correctness, performance, and idiomatic style.
Always explain your reasoning. Never rewrite code without being asked.
Respond in English regardless of the language used in the user turn.
```

**What belongs in user turns:** the specific task, input data, and per-request variations.

---

## 2. Use XML to Separate Sections

Claude is explicitly trained on XML-structured prompts. XML tags reduce ambiguity when a prompt mixes instructions, context, examples, and variable input — Claude parses each section independently rather than inferring boundaries from whitespace or prose.

```xml
<instructions>
Extract all action items from the meeting notes below.
Return them as a JSON array with fields: owner, task, deadline.
</instructions>

<context>
Team: Platform Engineering
Meeting date: 2025-04-20
</context>

<meeting_notes>
{{MEETING_NOTES}}
</meeting_notes>
```

**Naming conventions that work well:**

| Tag | Use for |
|---|---|
| `<instructions>` | What to do |
| `<constraints>` | What not to do / limits |
| `<context>` | Background the model needs |
| `<examples>` / `<example>` | Few-shot demonstrations |
| `<input>` / `<document>` | Variable data injected at runtime |
| `<output_format>` | Exact format spec |
| `<thinking>` | Inside few-shot examples to show reasoning pattern |

Nest when content has hierarchy:

```xml
<documents>
  <document index="1">
    <source>q1_report.pdf</source>
    <document_content>{{Q1_REPORT}}</document_content>
  </document>
  <document index="2">
    <source>q2_report.pdf</source>
    <document_content>{{Q2_REPORT}}</document_content>
  </document>
</documents>
```

---

## 3. Give 3–5 High-Quality Few-Shot Examples

Claude generalizes strongly from examples. A few well-crafted ones often eliminate the need for lengthy instructions. Wrap them in `<example>` / `<examples>` tags so Claude distinguishes them from real input.

**Qualities of good examples:**

- Mirror your actual use case closely — not toy cases
- Cover edge cases and variation (don't repeat the same pattern)
- Use the exact output format you expect
- Consistent delimiters, whitespace, and structure across all examples

```xml
<examples>
  <example>
    <input>The server crashed at 3am due to OOM. On-call was paged.</input>
    <output>{"severity": "high", "category": "infrastructure", "action_required": true}</output>
  </example>
  <example>
    <input>Weekly sync rescheduled to Thursday.</input>
    <output>{"severity": "low", "category": "scheduling", "action_required": false}</output>
  </example>
  <example>
    <input>Deploy to prod blocked — missing approval from security team.</input>
    <output>{"severity": "high", "category": "deployment", "action_required": true}</output>
  </example>
</examples>
```

For reasoning tasks, include `<thinking>` tags inside examples to show the reasoning pattern — Claude will generalize it to its own thinking blocks:

```xml
<example>
  <input>15, 32, 5, 13, 82, 7, 1 — do the odd numbers sum to an even number?</input>
  <thinking>Odd numbers: 15, 5, 13, 7, 1. Sum = 41. 41 is odd.</thinking>
  <output>False — the odd numbers sum to 41, which is odd.</output>
</example>
```

---

## 4. Long Material First, Question Last

Claude's attention is strongest at the beginning and end of context. For long-context tasks (documents, codebases, transcripts), place the material first and the query last. This pattern can improve response quality by up to 30% on complex multi-document inputs.

```xml
<documents>
  <document index="1">
    <source>contract_v3.pdf</source>
    <document_content>{{CONTRACT}}</document_content>
  </document>
</documents>

Based on the contract above, identify all clauses related to liability and summarize each in one sentence.
```

---

## 5. Repeat the Task Requirement Before the Query

When context is very long, Claude may lose track of the original instruction by the time it reaches the query. Repeat the core constraint just before the question:

```xml
<documents>
  {{LARGE_CODEBASE_CONTEXT}}
</documents>

Reminder: answer based only on the code above. Do not suggest changes outside the files shown.

Q: Why does the authentication middleware skip token validation on OPTIONS requests?
```

This is especially important for:

- RAG pipelines where grounding is critical
- Long audit/review tasks with strict scope constraints
- Multi-document synthesis where one source should take precedence

---

## 6. Hard-Code the Output Format

Claude respects explicit format specs. Don't rely on natural language to describe format — show it or specify it precisely. Use XML tags as output containers, or define a schema.

**Format via output tags:**

```xml
<instructions>
Analyze the bug report and respond in this exact format:
</instructions>

<output_format>
<severity>critical | high | medium | low</severity>
<root_cause>One sentence.</root_cause>
<fix>Specific action to resolve.</fix>
<affected_components>Comma-separated list.</affected_components>
</output_format>
```

**Format via prose instruction (use positive framing — what to do, not what to avoid):**

```
❌ Don't use markdown or bullet points.

✅ Write in flowing prose paragraphs. Use plain text only.
   Reserve code blocks for code samples exclusively.
```

**Format via completion prefix (when you need precise structure):**
Starting the output yourself locks Claude into that format:

```
Classify the following ticket and fill in the JSON:

Ticket: "Login button unresponsive on mobile Safari."

{
  "category":
```

**Controlling verbosity:**
Claude Opus 4.7+ calibrates length to task complexity by default. If your product requires a specific verbosity level, state it:

```
Provide concise, focused responses. Skip non-essential context. Keep examples minimal.
```

or:

```
This is a user-facing explanation. Write at least 3 paragraphs with concrete examples.
```

---

## 7. Complex Tasks: Use Thinking / Effort First, Then Manual CoT

For reasoning-heavy tasks, Claude has native thinking capabilities. Use these before reaching for manual chain-of-thought scaffolding — they typically outperform hand-written reasoning steps.

### Lever 1: Effort parameter (primary control)

The `effort` parameter controls how deeply Claude reasons. Set it based on task complexity:

| Effort | Use case |
|---|---|
| `xhigh` | Coding agents, agentic workflows, hard reasoning |
| `high` | Most intelligence-sensitive tasks (recommended minimum) |
| `medium` | Cost-sensitive tasks where some accuracy trade-off is acceptable |
| `low` | Short, scoped, latency-sensitive tasks only |

```python
client.messages.create(
    model="claude-opus-4-7",
    max_tokens=64000,
    thinking={"type": "adaptive"},
    output_config={"effort": "xhigh"},
    messages=[{"role": "user", "content": "..."}]
)
```

### Lever 2: Adaptive thinking (default for Opus 4.7, Opus 4.6, Sonnet 4.6)

Claude decides when and how much to think based on effort + query complexity. No extra prompting needed for most cases.

To encourage thinking on a specific problem:

```
After receiving tool results, carefully reflect on their quality and determine
optimal next steps before proceeding.
```

To reduce unnecessary thinking (reduces latency):

```
Extended thinking adds latency. Only use it when it will meaningfully improve
answer quality — typically for multi-step reasoning. When in doubt, respond directly.
```

### Lever 3: Manual CoT — use only as fallback

When thinking is off, or when you need to control the reasoning structure precisely, use manual chain-of-thought. Two patterns:

**Zero-shot CoT trigger:**

```
Think step by step before answering.
```

**Few-shot CoT with explicit structure:**

```xml
<instructions>
Solve the problem. Show your reasoning in <thinking> tags, then give the final answer in <answer> tags.
</instructions>

<example>
  <input>If a train travels 120km in 1.5 hours, what is its average speed?</input>
  <thinking>Speed = distance / time = 120 / 1.5 = 80 km/h</thinking>
  <answer>80 km/h</answer>
</example>

<input>{{PROBLEM}}</input>
```

**Self-check for accuracy-critical tasks:**

```
Before finalizing your answer, verify it against the original requirements.
```

### When not to add manual CoT

If effort is set to `high` or above, Claude is already reasoning deeply. Adding manual CoT scaffolding on top of high-effort adaptive thinking is often redundant and can cause overthinking. Raise effort first; add manual scaffolding only if results are still insufficient.

---

## Quick Reference

| Preference | What to do |
|---|---|
| System role | Write it first; put all stable behavioral constraints there |
| Structure | Use XML tags to separate instructions / context / examples / input |
| Few-shot | 3–5 examples in `<examples>` tags; consistent format; cover edge cases |
| Long context | Material first, query last |
| Task repetition | Repeat core constraint just before the query in long-context prompts |
| Output format | Specify exactly via XML output tags, positive prose instructions, or completion prefix |
| Reasoning | Set `effort` level first; use adaptive thinking; add manual CoT only as fallback |
