# Chain-of-Thought (CoT) Prompting

## What It Is

Chain-of-thought (CoT) prompting, introduced in Wei et al. (2022), extends few-shot prompting by including **intermediate reasoning steps** in the examples — not just the final answer. The model learns to produce its own reasoning chain before arriving at a conclusion.

This is the key upgrade over standard few-shot prompting for tasks that require multi-step logic, arithmetic, or commonsense reasoning.

**Standard few-shot** (fails on reasoning):
```
The odd numbers in this group add up to an even number: 4, 8, 9, 15, 12, 2, 1.
A: False.

The odd numbers in this group add up to an even number: 15, 32, 5, 13, 82, 7, 1.
A:
```
→ Model often gets this wrong.

**CoT few-shot** (succeeds):
```
The odd numbers in this group add up to an even number: 4, 8, 9, 15, 12, 2, 1.
A: Adding all the odd numbers (9, 15, 1) gives 25. The answer is False.

The odd numbers in this group add up to an even number: 15, 32, 5, 13, 82, 7, 1.
A:
```
→ Model outputs: "Adding all the odd numbers (15, 5, 13, 7, 1) gives 41. The answer is False." ✓

The reasoning chain in the example teaches the model *how* to approach the problem, not just *what* to output.

> **Important:** CoT is an emergent capability. It arises with sufficiently large language models. It has little effect on small models.

---

## Three Variants

### 1. Few-shot CoT (classic)
Provide 2–8 examples, each with a full reasoning chain before the answer. One well-crafted example is often enough for simpler reasoning tasks.

**Format:**
```
<problem>
A: <step-by-step reasoning>. The answer is <final answer>.

<problem>
A: <step-by-step reasoning>. The answer is <final answer>.

<target problem>
A:
```

### 2. Zero-shot CoT
Add **"Let's think step by step."** to the end of the prompt. No examples needed. Proposed by Kojima et al. (2022).

```
I went to the market and bought 10 apples. I gave 2 to the neighbor and 2 to the
repairman. I then bought 5 more and ate 1. How many apples do I have left?

Let's think step by step.
```

Output: the model works through the steps explicitly and arrives at the correct answer (10).

Without the trigger phrase, the same prompt often yields the wrong answer directly.

Other effective trigger phrases:
- `"Let's think step by step."`
- `"Think through this carefully before answering."`
- `"Work through this step by step."`
- `"First, let's reason about this:"` (for Claude)

### 3. Auto-CoT (automated pipeline)
Proposed by Zhang et al. (2022) to eliminate hand-crafted examples. Two stages:

1. **Question clustering** — partition dataset questions into clusters by topic/type
2. **Demonstration sampling** — pick one representative question per cluster, generate its reasoning chain automatically using zero-shot CoT ("Let's think step by step"), then use those auto-generated chains as few-shot examples

Heuristics for quality control: prefer examples with ~60 token questions and ~5 reasoning steps. Diversity across clusters prevents the model from overfitting to one reasoning pattern.

This is most useful when building systematic pipelines over large task datasets.

---

## When to Use CoT

| Situation | Use CoT? |
|---|---|
| Multi-step arithmetic or algebra | ✅ Yes — zero-shot or few-shot CoT |
| Logical/symbolic reasoning (if-then, deduction) | ✅ Yes |
| Commonsense reasoning requiring inference | ✅ Yes |
| Simple factual lookup or classification | ❌ No — standard few-shot or zero-shot is faster |
| Format-sensitive structured output (JSON, tables) | ❌ No — standard few-shot; CoT adds noise |
| You have no examples to hand-craft | ✅ Zero-shot CoT ("Let's think step by step") |

**Rule of thumb:** if a human would need to show their work to get it right, the model probably does too.

---

## Prompt Design Guidelines for CoT

### Writing good reasoning chains in examples
- Show all steps explicitly, don't skip to the answer
- Use concrete intermediate values: "Adding 9 + 15 + 1 = 25" not just "the sum is 25"
- Keep each step on its own line for clarity
- End with a clear final answer statement: "The answer is False."

### One example is often enough
For many reasoning tasks, a single well-crafted example with a clear reasoning chain is sufficient. Don't over-engineer. Start with 1 example and add more only if the model still fails.

### Place reasoning before the answer
The reasoning must come **before** the final answer token. The model generates left-to-right, so the chain primes the answer — not the other way around.

```
# Correct
A: <reasoning steps>. Therefore the answer is X.

# Wrong — reasoning after answer doesn't help
A: X. Because <reasoning steps>.
```

### For zero-shot CoT: put the trigger at the end
The trigger phrase should appear at the end of the user turn, just before the model's response begins.

```
Question: <problem>

Let's think step by step.
```

### Self-check instruction for critical tasks
For accuracy-critical tasks (code correctness, math, medical), add a self-check after the reasoning:

```
Solve the problem step by step, then verify your answer before stating it.
```

---

## Relationship to Other Techniques

| Technique | Description | When |
|---|---|---|
| Zero-shot | Instruction only, no examples | Simple tasks |
| Few-shot | Examples with answers only | Format-sensitive tasks |
| Few-shot CoT | Examples with reasoning + answer | Reasoning tasks with examples available |
| Zero-shot CoT | "Let's think step by step" | Reasoning tasks, no examples needed |
| Auto-CoT | Auto-generated reasoning examples | Pipeline/dataset-scale applications |

---

## Key Research References

- **Wei et al. (2022)** — Introduced chain-of-thought prompting. arXiv:2201.11903
- **Kojima et al. (2022)** — Zero-shot CoT ("Let's think step by step"). arXiv:2205.11916
- **Zhang et al. (2022)** — Auto-CoT: automatic demonstration construction. arXiv:2210.03493