# OpenAI / ChatGPT Prompt Design Guide

Key difference from Claude and Gemini: OpenAI models are most sensitive to **instruction placement, structural separation, and conflict elimination**. GPT-5+ models follow instructions very literally — contradictory or underspecified prompts cause the model to spend reasoning tokens reconciling conflicts rather than doing the task.

---

## 1. Instructions First

Place the task instruction at the top, before any context or data. Separate the instruction block from the content using a structural delimiter (`###`, triple quotes, or XML-like markers).

```
Summarize the customer feedback below into 3 bullet points.
Focus on recurring complaints. Ignore praise.

###
{{CUSTOMER_FEEDBACK}}
```

```
Classify the following support ticket as: billing / technical / account / other.
Return only the category label.

"""
{{TICKET_TEXT}}
"""
```

Do not bury the instruction inside the context block or after the data — GPT models weight early content more heavily, and instruction retrieval degrades with distance from the top.

---

## 2. Specify Task, Constraints, and Output Format Explicitly

Vague instructions produce variable output. Write out the goal, length, format, style, and constraints precisely. Replace qualitative limits with concrete ones.

```
❌ Write a short summary.

✅ Write a summary in exactly 3 sentences. Use plain language. Do not include numbers or statistics.
```

```
❌ Don't make it too long.

✅ Response must be under 150 words.
```

**Eliminate conflicting rules.** GPT-5+ models follow instructions very precisely. If your prompt contains contradictory requirements (e.g., "be concise" and "cover all edge cases in detail"), the model spends reasoning tokens reconciling the conflict instead of completing the task. Audit prompts for contradictions before adding more rules.

---

## 3. Separate Context / Task / Output Format into Blocks

Mixing task description, background context, and format requirements into a single paragraph reduces instruction-following reliability. Use structural blocks to separate them.

**Using `###` delimiters:**

```
## Task
Extract all dates mentioned in the text below. Return them as a JSON array in ISO 8601 format.

## Constraints
- Include only explicit dates (not relative references like "last week").
- If no dates are found, return an empty array.

## Output format
["YYYY-MM-DD", ...]

## Text
###
{{INPUT_TEXT}}
###
```

**Using XML markers (also works well for GPT):**

```xml
<task>Translate the support message below to formal English.</task>
<constraints>Preserve all technical terms. Do not add information not present in the original.</constraints>
<input>{{MESSAGE}}</input>
```

Both styles work. The key is that each type of content has its own clearly bounded section.

---

## 4. Long Context: Query Last; Repeat Task Requirement Before the Query

Research on GPT-4o shows that performance degrades significantly with long context when the task instruction only appears at the top. At 64k tokens, accuracy can drop from 0.524 (no context) to 0.355 (instruction at top only) — and recover to 0.510 when the instruction is repeated just before the query.

Pattern:

```
<task>
Identify the root cause of the incident described in the logs below.
</task>

[Large log block — up to tens of thousands of tokens]

Reminder: identify only the root cause. Do not list symptoms or propose fixes.

Q: What caused the authentication failures starting at 03:42 UTC?
```

When to apply this:

- Any prompt where the context block exceeds ~5k tokens
- RAG pipelines with retrieved documents
- Code review over large codebases
- Multi-document analysis tasks

---

## 5. Give One Correct Format Example

For non-trivial output formats, show one complete correct example rather than describing the format in prose. A single well-formed example is more reliable than a paragraph of format instructions.

```
Extract action items from meeting notes. Return a JSON array.

Example output:
[
  {"owner": "Alice", "task": "Update deployment runbook", "deadline": "2025-05-01"},
  {"owner": "Bob", "task": "Review security audit findings", "deadline": "2025-05-03"}
]

Meeting notes:
{{NOTES}}
```

**One example is usually enough.** GPT models generalize the format quickly. Adding 3–5 examples helps for edge-case coverage (similar to Claude/Gemini few-shot best practices), but a single example already eliminates most format drift.

**Positive framing beats prohibition:**

```
❌ Do not return markdown. Do not include explanations. Do not add fields not listed.

✅ Return only a valid JSON array matching the structure shown in the example above.
   No markdown, no explanations, no extra fields.
```

---

## 6. Match Reasoning Effort to Task Complexity

For reasoning models (o3, o4-mini, GPT-5+), the `reasoning.effort` parameter controls how many reasoning tokens the model uses. Setting it higher than needed wastes tokens and adds latency without improving results. Setting it too low on complex tasks produces shallow reasoning.

| Effort | Suitable tasks |
|---|---|
| `none` / `low` | Simple extraction, routing, classification, format conversion |
| `medium` | Summarization, Q&A with context, moderate code generation |
| `high` | Multi-step planning, complex coding, synthesis across many sources |

```python
client.responses.create(
    model="o4-mini",
    reasoning={"effort": "medium"},
    input=[{"role": "user", "content": "..."}]
)
```

**Do not default to `high` for all tasks.** Unnecessary reasoning effort is the OpenAI equivalent of over-prompting — it costs more and can introduce overthinking on tasks that don't need it.

For non-reasoning GPT models (GPT-4o, GPT-4.1), effort is controlled through prompt design: keep instructions clean and unambiguous, and rely on few-shot examples for complex formats rather than elaborate instructions.

---

## What Not to Optimize

Research shows these are weak signals for GPT models — low priority or actively counterproductive:

- **Excessive politeness:** Neutral tone slightly outperforms very polite in some tasks. "Please" and "thank you" have no measurable benefit.
- **Repeating the same instruction multiple times:** Mechanically repeating a question 3–5 times does not reliably improve GPT-4o mini output.
- **Template micro-optimization:** Much of the perceived "magic template" effect is measurement artifact. Focus on structural clarity, not phrasing superstition.
- **Piling up absolute rules:** Multiple "MUST / NEVER / ALWAYS" constraints that partially conflict with each other cause reasoning degradation on GPT-5+. Fewer, cleaner rules outperform many conflicting ones.

---

## Quick Reference

| Preference | What to do |
|---|---|
| Instructions | Place at the top; separate from context with `###`, quotes, or XML markers |
| Specificity | Replace vague constraints with concrete ones (numbers, exact formats) |
| Structure | Separate task / constraints / output format / input into distinct blocks |
| Long context | Query last; repeat core instruction just before the query |
| Format examples | Give one complete correct example; use positive framing |
| Reasoning effort | Match to task complexity; don't default to max |
| Conflicts | Audit prompts for contradictory rules before adding new ones |
