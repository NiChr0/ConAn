# ConAn Skills Redesign

**Date:** 2026-05-14  
**Scope:** data-analyst and product-analyst skills — structure and prompt quality  
**Status:** Approved

---

## Problem

The existing skills are structurally inconsistent and too thin to reliably enforce correct behavior:

- `sql.md` and `analysis.md` have rules but no examples and no explanations of *why*, leading to compliance failures (e.g. plain `AVG()` on pre-aggregated columns despite an explicit rule against it)
- `product_analyst.py` hardcodes system prompts as inline strings instead of `.md` files, breaking the pattern used by data-analyst
- `product_analyst.py` sets `max_tokens=512` for synthesis — dangerously low for root cause analysis
- No consistent folder structure between the two skills

---

## Design

### Approach: Layered reference architecture (Option B)

Each skill gets its own folder with a `SKILL.md` orchestration file, step-specific prompt files, and a `references/` directory for auxiliary content loaded on demand. The Python runtime stays two-phase for both skills.

---

### Folder structure

```
conan/skills/
├── data-analyst/
│   ├── SKILL.md                  # orchestration + design principles
│   ├── sql.md                    # SQL generation — rules, reasoning, 3 worked examples
│   ├── analysis.md               # result interpretation — format, confidence, 2 worked examples
│   └── references/
│       ├── edge-cases.md         # weighted avg, empty results, date mismatches, schema misses
│       └── confidence-guide.md   # full scoring rubric with rationale
│
├── product-analyst/              # NEW — mirrors data-analyst structure
│   ├── SKILL.md                  # orchestration + design principles
│   ├── decompose.md              # diagnostic query generation — rules, examples
│   └── synthesize.md            # root cause synthesis — format, confidence, examples
│
├── data_queries.py               # minor: lazy-load edge-cases.md for pre-aggregated schemas
├── product_analyst.py            # refactored: load from files, higher token limits, error recovery
└── base.py                       # unchanged
```

---

### data-analyst/sql.md

Four sections:

1. **Role & context** — what this phase produces and why it's separate from analysis. The SQL is an independently verifiable intermediate artifact.

2. **Rules with reasoning** — each rule includes a one-line *why*. The weighted average rule is prominent with a wrong/right inline comparison:
   > Never `AVG()` a pre-aggregated average column. Pre-aggregated rows represent different group sizes — averaging them without weighting produces a misleading result.
   > - Wrong: `AVG(avg_discount)`
   > - Right: `SUM(avg_discount * order_count) / SUM(order_count)`

3. **Output format** — explicit structured schema: `sql`, `source_table`, `source_tier`, `reasoning`.

4. **Worked examples** (3):
   - Simple aggregate (total revenue) — shows tier selection logic
   - Time-series with pre-aggregated column (avg discount) — enforces weighted avg
   - Unanswerable question (metric not in schema) — graceful no-SQL response

---

### data-analyst/analysis.md

Four sections:

1. **Role & framing** — analyst presenting to a business stakeholder. Tone and clarity matter as much as correctness.

2. **Format template** — kept from current version, with annotations explaining *why* each element exists (leading number gives the answer before the table; confidence lets the reader calibrate action).

3. **Confidence scoring** — replaced with ceiling-first rubric:
   - Start at the KPI catalog's `confidence_ceiling` if the metric is known, else 60
   - Apply penalties: −20 for empty result, −10 for wrong granularity, −10 for no catalog match
   - Never exceed the ceiling

4. **Worked examples** (2):
   - Good result: monthly revenue trend — correct format applied end-to-end
   - Bad result: empty result due to date mismatch — what to say when data isn't there

---

### data-analyst/references/edge-cases.md

Covers patterns that are easy to get wrong:
- Weighted average on pre-aggregated columns (detailed expansion of the sql.md rule)
- Empty result handling (dataset covers different date range than requested)
- Schema miss (requested metric has no source table)
- Date granularity mismatch (daily question → monthly table)

Loaded and appended to the SQL generation context when the schema contains `avg_` or `agg_` prefixed columns.

---

### data-analyst/references/confidence-guide.md

Full confidence scoring reference with rationale for each factor. The ceiling-first model means the analyst always starts calibrated to the KPI's known reliability, then adjusts down for data quality issues. This is more honest than an additive system that can reach 95% for a well-structured but empty result.

Always appended to the analysis context (it's short and always relevant).

---

### product-analyst/SKILL.md

Distinguishes this skill from data-analyst:
- data-analyst: "what is X" — known metric, direct query
- product-analyst: "why did X change" — unknown cause, diagnostic investigation

Design principle: generate 2-3 queries testing *independent hypotheses*, not variations of the same query. Each diagnostic angle should be falsifiable.

---

### product-analyst/decompose.md

Role: detective generating hypotheses, not just queries.

Rules:
- Each query tests a different hypothesis (time trend, segment breakdown, funnel step, external factor)
- Two queries testing the same thing is wasted work — explicitly forbidden
- Name the hypothesis each query is testing

Output format: `sql`, `source_table`, `source_tier`, `hypothesis` (what this query is trying to prove or disprove).

Worked example: "why did revenue drop in March?" → three queries:
1. Time trend — is this a sustained decline or a one-month spike?
2. Top-customer concentration — did a few large customers churn?
3. Product mix — did high-margin product orders fall while low-margin held?

---

### product-analyst/synthesize.md

Role: synthesizing evidence from multiple queries into one coherent explanation.

Rules:
- Name the most likely cause first
- Cite specific numbers from diagnostic results (not vague references)
- Explicitly note which hypotheses were ruled out and why — absence of evidence is evidence

Format template:
```
**Finding:** [one sentence — the most likely cause]

**Evidence:**
- [Query 1 hypothesis]: [what the data showed]
- [Query 2 hypothesis]: [what the data showed]
- [Query 3 hypothesis]: [what the data showed]

**Ruled out:** [hypotheses the data contradicted and why]

**Confidence: [score]% — [one-line justification]**
```

Worked example showing the full structure applied to the March revenue drop scenario.

---

### Python runtime changes

**`product_analyst.py`:**
- Load `decompose.md` and `synthesize.md` from `product-analyst/` at module level
- `max_tokens` for decompose: 2048 (was 1024)
- `max_tokens` for synthesize: 2048 (was 512)
- Error recovery: if all diagnostic queries fail, return a `SkillResult` with a clear unavailable message rather than passing empty results to synthesis

**`data_queries.py`:**
- Lazy-load `references/edge-cases.md` and append to SQL context when schema contains pre-aggregated columns (detected by `avg_` or `agg_` prefix patterns in schema/kpis context)
- Otherwise unchanged

---

## Success criteria

- `sql.md` weighted average rule is followed in the avg-discount eval without additional prompting
- `product_analyst.py` system prompts are loaded from files, not hardcoded
- Synthesis never truncates (max_tokens raised)
- All 9 existing evals still pass or improve
- A failed-all-queries scenario returns a clean SkillResult rather than an error
