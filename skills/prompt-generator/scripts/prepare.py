#!/usr/bin/env python3
"""
Data types and utilities for preparing training data.
"""

import json
import os
from dataclasses import dataclass


@dataclass
class TestCase:
    input: str           # concrete user message to send to the prompt under test
    criteria: list[str]  # verifiable conditions the response must satisfy


def save_test_cases(test_cases: list[TestCase], path: str) -> str | None:
    """
    Validate and write test cases to a JSONL file (one record per line).

    Iterates all test cases and collects every validation error before returning,
    so the caller gets a complete picture of what needs to be fixed.

    Returns:
        None  — all test cases are valid; file has been written.
        str   — one or more test cases are invalid; nothing was written.
                The returned string lists every problem, ready to show to the LLM.
    """
    errors: list[str] = []

    for i, tc in enumerate(test_cases):
        issues: list[str] = []

        if not isinstance(tc.input, str) or not tc.input.strip():
            issues.append('"input" must be a non-empty string')

        if not isinstance(tc.criteria, list) or len(tc.criteria) == 0:
            issues.append('"criteria" must be a non-empty list')
        elif not all(isinstance(c, str) and c.strip() for c in tc.criteria):
            issues.append('every item in "criteria" must be a non-empty string')

        if issues:
            errors.append(f"  test_cases[{i}] (input={tc.input!r:.40}): {'; '.join(issues)}")

    if errors:
        return "Invalid test cases — fix them before saving:\n" + "\n".join(errors)

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        for tc in test_cases:
            f.write(json.dumps({"input": tc.input, "criteria": tc.criteria}, ensure_ascii=False) + "\n")

    print(f"Saved {len(test_cases)} test cases → {path}")
    return None


