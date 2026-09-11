# Gemini Prompt Design Guide

Key difference from Claude: Gemini prefers **short, direct, structurally separated** prompts. Claude prefers semantically rich XML tags wrapping content. When writing for Gemini, skip the preamble — just tell it what to do.

---

## 1. Be Direct, Short, and Explicit

Use the fewest words to express the clearest intent. Avoid warm-up language, explanatory framing, or hedged phrasing.

```
❌ I would really appreciate it if you could help me understand...

✅ Explain X in 2 sentences.
```

```
❌ Please make sure to only output JSON and nothing else if possible.

✅ Output JSON only. No other text.
```

---

## 2. Separate Task / Constraints / Output Format

Don't mix task description, constraints, and output format into a single paragraph. Splitting them increases instruction-following reliability.

**XML style (recommended for system prompts):**

```xml
<task>
Classify the sentiment of each review as positive, negative, or neutral.
</task>

<constraints>
- One word per review.
- No explanation.
</constraints>

<output_format>
Return a JSON array: [{"review_id": ..., "sentiment": ...}]
</output_format>
```

**Markdown style (suitable for user turns):**

```markdown
## Task
Summarize the following article.

## Constraints
- Max 3 sentences.
- No bullet points.

## Output format
Plain prose.
```

Both formats work. Pick one and use it consistently within a single prompt — don't mix styles.

---

## 3. Long Context: Put the Question Last; Repeat the Task Before the Query if Needed

Gemini weights content that appears **later in the context more heavily**. Place large documents, code, or data first; put the task last.

```
[Document / code / data goes here]

Based on the information above, answer the following:
Q: ...
```

When context is very long, the model may "forget" the original instruction after processing the material. **Repeat the core task requirement just before the query:**

```
[Large context block]

Reminder: answer only based on the text above, in one sentence.

Q: What caused the outage?
```

---

## 4. Use Few-Shot + Consistent Formatting for Stable Output

When output format is non-standard or classification labels need to be exact, few-shot examples are more reliable than instructions alone.

**Key rules:**

- All examples use identical delimiters, whitespace, and tag structure
- Sample labels from the true distribution — don't force one example per class
- 3–5 examples is usually enough; beyond 10, diminishing returns and risk of overfitting

```
Review: "Fast shipping, exactly as described."
Sentiment: positive

Review: "Broke after one use."
Sentiment: negative

Review: "It's fine, nothing special."
Sentiment: neutral

Review: "Best purchase I've made this year!"
Sentiment:
```

**Inconsistency anti-pattern** (causes output drift):

```
❌ Example 1 uses a colon, Example 2 uses a dash, Example 3 has no separator
```

---

## 5. Use Schema for Structured Output — Don't Rely on Natural Language Alone

When JSON or other structured formats are required, **passing a schema is more reliable than describing the format in prose**. Natural language constraints ("output valid JSON with fields X and Y") tend to drift; a schema is a hard constraint.

**Gemini API structured output (recommended):**

```python
import google.generativeai as genai
import typing_extensions as typing

class Review(typing.TypedDict):
    review_id: int
    sentiment: str  # "positive" | "negative" | "neutral"
    confidence: float

model = genai.GenerativeModel("gemini-2.0-flash")
result = model.generate_content(
    "Classify these reviews: ...",
    generation_config=genai.GenerationConfig(
        response_mime_type="application/json",
        response_schema=list[Review],
    ),
)
```

**When API schema is not available (prompt-only):** Use a completion prefix instead of describing the format — give the start of the output and let the model continue. More stable than "please output JSON":

```
Order: Give me a cheeseburger and fries.
Output:
{
  "cheeseburger": 1,
  "fries": 1
}

Order: Two burgers, a drink, and fries.
Output:
```

The model continues the established JSON pattern rather than free-forming the response.

---

## Quick Reference

| Scenario | Recommended approach |
|---|---|
| Simple single-step task | One-sentence direct instruction |
| Multiple constraints | Separate task / constraints / output_format sections |
| Stable output format needed | Few-shot + consistent formatting |
| JSON / structured data needed | Gemini API schema; or completion prefix |
| Long document Q&A | Context first, task last, repeat constraint before query |
| Reasoning / math tasks | Add "Think step by step" or few-shot CoT |
