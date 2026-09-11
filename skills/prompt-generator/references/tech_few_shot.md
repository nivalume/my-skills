# Few-Shot Prompting

## What It Is

Few-shot prompting is an **in-context learning** technique where you provide a small number of worked examples (demonstrations) directly inside the prompt. The model uses these examples as conditioning to infer the task format, output style, and desired behavior — without any gradient updates or fine-tuning.

The term comes from Brown et al. (2020), the GPT-3 paper, which formalized a spectrum:

| Setting | Demonstrations | Typical use |
|---|---|---|
| Zero-shot | None — instruction only | Simple, well-known tasks |
| One-shot | 1 example | When format needs clarification |
| Few-shot | 2–100 examples (commonly 3–5) | Complex format, rare domain, reasoning tasks |

---

## When to Use Few-Shot

Use few-shot prompting when:

- **Output format is non-standard or precise**: The model needs to see the exact format (structured JSON, specific label strings, a creative style) to reproduce it reliably.
- **Zero-shot gives inconsistent results**: The task is under-specified by instructions alone.
- **The domain is unusual**: Rare terminology, specialized jargon, or tasks unlikely to appear frequently in training data.
- **Style or tone must be matched**: Mimicking a writing voice, a classification taxonomy, or a brand's output pattern.
- **Complex reasoning with intermediate steps**: Showing worked reasoning chains (leads naturally into chain-of-thought — see below).

**Key insight from Min et al. (2022)**: The label space and input distribution shown in examples matter more than whether individual labels are correct. Even random labels help — what the model is really learning is the format and pattern, not just correct answers.

---

## How to Construct Good Examples

### Number of examples
Start with 3–5 examples. For harder tasks, scale up to 10–20. constrained only by context window size. More examples generally improve performance, especially for larger models.

### Example diversity
Cover the range of input types the model will encounter. If classifying sentiment, include positive, negative, and neutral examples — not just easy cases.

### Format consistency
Use a consistent delimiter and structure across all examples. Common patterns:

```
Input: <text>
Output: <label>
```

or

```
Q: <question>
A: <answer>
```

Even when using random/incorrect labels (for research), the consistent format itself carries useful signal.

### Label distribution
Draw labels from the true distribution, not uniformly. If 70% of your real outputs are "positive", your examples should reflect that.

### Example placement
Place examples **before** the final prompt (the task instance the model should complete). The model completes the pattern.

```
<example 1>
<example 2>
<example 3>
<final input for model to complete>
```

### XML tagging for complex prompts
For multi-field structured examples, use `<example>` / `<examples>` tags:

```xml
<examples>
  <example>
    <input>I loved this product!</input>
    <output>positive</output>
  </example>
  <example>
    <input>Complete waste of money.</input>
    <output>negative</output>
  </example>
</examples>
```

---

## Advanced Example Selection Strategies

When you have a pool of candidate examples to choose from, which ones you pick matters. Research shows two principles dominate: **relevance** (examples similar to the current input condition the model better) and **diversity** (redundant examples waste slots). The following are reasoning-based heuristics that translate these principles into actions an LLM can perform without any computation.

### 1. Match the test input's key characteristics
Before selecting, identify what makes the current input distinctive: its topic, length, complexity, output type, edge-case nature. Then scan the candidate pool and prefer examples that share those characteristics. This is the reasoning equivalent of semantic similarity — you are doing the matching judgment yourself.

*Research basis: Liu et al. (2021) showed that semantically similar examples outperform random selection. The same principle applies when the similarity judgment is made by reasoning rather than by embeddings.*

### 2. Avoid near-duplicate selections
After picking one example, check whether the next candidate is essentially the same case rephrased. If so, skip it. Each example slot should add new information — a different output category, a different input structure, or a different kind of reasoning step.

*Research basis: Su et al. (2022) showed that diversity across examples matters independently of individual relevance. Selecting near-duplicates hurts because the model receives the same signal K times instead of K distinct signals.*

### 3. Cover the output space, not just the input space
Ensure your selected examples collectively represent the full range of possible outputs. For a classification task, include examples for each label. For a generation task, include examples that span the range of lengths, tones, or structures the task might require.

*Research basis: Min et al. (2022) found that label space coverage is one of the strongest drivers of few-shot performance — more important than whether any individual label is even correct.*

### 4. Prioritize examples where the correct answer is non-obvious
Prefer examples where a naive or pattern-matching approach would fail. These are the cases where seeing the worked answer is most informative — they constrain the model's behavior on hard inputs, not just easy ones.

*Research basis: Diao et al. (2023) showed that high-uncertainty inputs (where models disagree) carry the most information when used as examples. Trivial examples teach the model nothing it doesn't already know.*

---

## Limitations of Few-Shot Prompting

Few-shot prompting has real limits, particularly for **multi-step reasoning**:

**Example of failure:**
```
The odd numbers in this group add up to an even number: 15, 32, 5, 13, 82, 7, 1. A:
```

Even with several examples showing the format, the model can give the wrong answer because the task requires step-by-step arithmetic, not pattern matching. For tasks like this, few-shot alone isn't enough — you need **chain-of-thought prompting** (showing reasoning steps in your examples, not just final answers).

**When to escalate beyond few-shot:**
- Multi-step arithmetic or logical reasoning → Chain-of-thought (CoT) prompting
- Task requires deep domain adaptation with many examples → Fine-tuning
- Context window exhausted before sufficient examples → Retrieval-augmented generation or fine-tuning

---

## Practical Prompt Design Tips

### Task description + examples
Always include a natural language task description before the examples. The GPT-3 paper showed that a natural language prompt combined with examples outperforms examples alone.

```
Classify the sentiment of the following customer reviews as positive, negative, or neutral.

Review: "Fast shipping and exactly as described."
Sentiment: positive

Review: "Broke after one use. Very disappointed."
Sentiment: negative

Review: "It's fine, nothing special."
Sentiment: neutral

Review: "Best purchase I've made this year!"
Sentiment:
```

### Format the final instance identically
The last entry (the one you want completed) must match the exact format of all prior examples, up to the point where the model should generate.

### Use natural separators
Newlines, `//`, `---`, or consistent punctuation between examples all work. Pick one and use it consistently.

### Calibrate K to the task
- Simple classification: 3–5 examples usually sufficient
- Complex structured output: 5–10 examples
- Rare tasks or unusual formats: 10–20 examples

---

## Key Research References

- **Brown et al. (2020)** — "Language Models are Few-Shot Learners" (GPT-3 paper). Formalized zero/one/few-shot taxonomy, demonstrated scaling of in-context learning. arXiv:2005.14165
- **Min et al. (2022)** — Showed that label correctness in examples matters less than format and label space coverage. arXiv:2202.12837
- **Kaplan et al. (2020)** — Scaling laws showing that few-shot capability emerges with model scale. arXiv:2001.08361