---
name: product-analyst
description: Root cause analysis, anomaly diagnosis, and why-did-X-change questions. Use when the user asks why a metric changed, what caused a drop or spike, or wants to diagnose an anomaly — not just look up a number.
---

# Product Analyst

This skill powers ConAn's diagnostic workflow for causal questions.

## When to use this skill vs data-analyst

- **data-analyst**: "What is total revenue?" — retrieve a known metric
- **product-analyst**: "Why did revenue drop in March?" — investigate a cause

The signal is the word "why" or any question about change, anomalies, or unexpected behaviour.

## Two-phase workflow

1. **Decompose** (`decompose.md`) — translate the question into 2–3 independent diagnostic SQL queries, each testing a different hypothesis
2. **Synthesize** (`synthesize.md`) — interpret results across all queries into a single coherent root cause finding

## Design principle

Each diagnostic query must test a **different hypothesis** — a distinct possible explanation.
Two queries probing the same angle (e.g. two time-trend queries) waste one of the diagnostic
slots. Good diagnostics cover different dimensions: time trend, segment breakdown, product mix,
geographic split, funnel step.

## Loading in Python

```python
from pathlib import Path
_SKILL_DIR = Path(__file__).parent / "product-analyst"
_SYSTEM_DECOMPOSE = (_SKILL_DIR / "decompose.md").read_text()
_SYSTEM_SYNTHESIZE = (_SKILL_DIR / "synthesize.md").read_text()
```
