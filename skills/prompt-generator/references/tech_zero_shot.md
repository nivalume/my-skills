# Zero-Shot Prompting

## Overview

Zero-shot prompting means the prompt does **not** contain any examples or demonstrations — the model is asked to perform a task based on instructions alone, relying entirely on knowledge acquired during training.

Large-scale instruction tuning and RLHF (Reinforcement Learning from Human Feedback) are what make zero-shot prompting effective. Models like Claude and GPT-4 are trained on massive instruction datasets that allow them to generalize to new tasks without needing examples in the prompt.

## When to Use Zero-Shot

Use zero-shot when:
- The task is well-defined and straightforward (classification, translation, summarization)
- The desired output format is simple and unambiguous
- You want to test the model's baseline capability before adding complexity
- Latency or token budget is a concern (no examples to include)

Fall back to **few-shot prompting** if zero-shot produces inconsistent or incorrect outputs.

## Example

**Prompt:**
```
Classify the text into neutral, negative or positive.

Text: I think the vacation is okay.
Sentiment:
```

**Output:**
```
Neutral
```

No examples were needed — the model understands "sentiment classification" from training alone.

## Prompt Design Tips for Zero-Shot

- **Be explicit about the task**: Use a clear verb + object + context structure. "Classify X as Y or Z" is better than "What do you think about X?"
- **Specify the output format**: Even without examples, tell the model how to format its answer (single word, JSON, numbered list, etc.)
- **Add a role if domain-specific**: "You are a financial analyst. Summarize the following earnings report in 3 bullet points."
- **Use a self-check instruction for accuracy-critical tasks**: "Think step by step before answering."

## Relationship to Other Techniques

| Situation | Recommended Technique |
|---|---|
| Task is clear, model likely knows it | Zero-shot |
| Output format is tricky or non-standard | Few-shot |
| Complex reasoning required | Chain-of-thought (zero-shot CoT: "Think step by step") |
| Rare domain or very specific style | Few-shot or fine-tuning |

## Further Reading

- Wei et al. (2022) — Instruction tuning paper: https://arxiv.org/pdf/2109.01652.pdf
- RLHF paper: https://arxiv.org/abs/1706.03741