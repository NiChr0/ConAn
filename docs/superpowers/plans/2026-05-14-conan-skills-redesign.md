# ConAn Skills Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite the data-analyst and product-analyst skill prompts to be thorough and example-driven, create a consistent `product-analyst/` folder structure mirroring `data-analyst/`, and fix the Python runtime for both skills.

**Architecture:** Each skill lives in its own folder (`data-analyst/`, `product-analyst/`) with a `SKILL.md` orchestration file, step-specific `.md` prompt files, and a `references/` subfolder for auxiliary content. The Python runtime loads prompts from files at module level. Edge-case reference material for data-analyst is lazily appended to SQL context when the schema contains pre-aggregated columns.

**Tech Stack:** Python 3.12+, pathlib, existing `conan.llm.query_structured`, pytest

---

## File map

| Action | Path | Purpose |
|--------|------|---------|
| Modify | `conan/skills/data-analyst/SKILL.md` | Add design principles section |
| Rewrite | `conan/skills/data-analyst/sql.md` | Rules + reasoning + 3 worked examples |
| Rewrite | `conan/skills/data-analyst/analysis.md` | Ceiling-first confidence + 2 worked examples |
| Create | `conan/skills/data-analyst/references/edge-cases.md` | Weighted avg, date mismatch, schema miss patterns |
| Create | `conan/skills/data-analyst/references/confidence-guide.md` | Full scoring rubric with rationale |
| Create | `conan/skills/product-analyst/SKILL.md` | Orchestration + design principles |
| Create | `conan/skills/product-analyst/decompose.md` | Diagnostic query generation + example |
| Create | `conan/skills/product-analyst/synthesize.md` | Root cause synthesis format + example |
| Modify | `conan/skills/data_queries.py` | Lazy-load edge-cases.md for pre-aggregated schemas |
| Modify | `conan/skills/product_analyst.py` | Load prompts from files, raise max_tokens, all-fail recovery |
| Modify | `tests/test_data_queries.py` | Test edge-cases lazy loading |
| Modify | `tests/test_product_analyst.py` | Test all-queries-fail early return |

---

## Task 1: Create `references/` directory and `edge-cases.md`

**Files:**
- Create: `conan/skills/data-analyst/references/edge-cases.md`

- [ ] **Step 1: Create the references directory and edge-cases file**

```bash
mkdir -p conan/skills/data-analyst/references
```

Write `conan/skills/data-analyst/references/edge-cases.md`:

```markdown
# SQL Edge Cases Reference

## Weighted averages on pre-aggregated columns

The most common silent error in this schema. Pre-aggregated tables store one row per time period
(day/month), where each row already summarises many underlying records. When you aggregate further
across rows, you must account for the different weights.

**Rule:** If a column name starts with `avg_` and the table has a `*_count` column, always use a
weighted average.

Pattern:
```sql
SUM(avg_column * count_column) / SUM(count_column)
```

Example — `agg_monthly_lineitem_revenue` has `avg_discount` and `order_count`:
```sql
-- Wrong: treats March (1,000 orders) the same as January (10,000 orders)
SELECT AVG(avg_discount) FROM agg_monthly_lineitem_revenue

-- Right: weights each month's average by its volume
SELECT SUM(avg_discount * order_count) / SUM(order_count) FROM agg_monthly_lineitem_revenue
```

## Empty results and date range mismatches

If a query returns no rows, the most likely cause is a date filter outside the dataset's range.
This dataset covers historical data (ending 1998). Queries filtering for "last 30 days" or
"this year" will always return empty.

When this happens, do not try a different table — tell the user the data isn't available for
that period and suggest a historical equivalent.

## Schema miss (metric not in any table)

If the user asks for a metric that requires data not present in the schema, return a literal
SELECT explaining this rather than guessing. Do not join tables hoping to reconstruct missing
data — the result will be wrong.

Example — customer repeat rate requires individual order-level data:
```sql
SELECT
    'not_available' AS status,
    'Schema has no individual order history per customer' AS reason
```

## Date granularity mismatch

Use the right table for the right granularity:
- Daily question → `agg_daily_*` tables
- Monthly question → `agg_monthly_*` tables

Joining a daily question to a monthly table loses intra-month variation and vice versa.
```

- [ ] **Step 2: Verify the file was created**

```bash
cat conan/skills/data-analyst/references/edge-cases.md
```

Expected: the full file content printed without error.

- [ ] **Step 3: Commit**

```bash
git add conan/skills/data-analyst/references/edge-cases.md
git commit -m "feat(skills): add edge-cases reference for data-analyst"
```

---

## Task 2: Create `confidence-guide.md`

**Files:**
- Create: `conan/skills/data-analyst/references/confidence-guide.md`

- [ ] **Step 1: Write the file**

Write `conan/skills/data-analyst/references/confidence-guide.md`:

```markdown
# Confidence Scoring Guide

## The ceiling-first model

Start at the KPI catalog's `confidence_ceiling` for the metric being answered. If the metric is
not in the KPI catalog, start at 60.

This anchors the score to the known reliability of the metric before considering data quality.

## Penalties

Apply these deductions from the starting ceiling:

| Condition | Penalty |
|---|---|
| Result is empty or all nulls | −20 |
| Source is T3 (Bronze/staging) | −10 |
| SQL doesn't match a catalog-defined pattern | −10 |

## Hard caps

- Never exceed `confidence_ceiling` from the KPI catalog
- Never score above 60 for an empty or null result (regardless of source tier)

## Why ceiling-first?

An additive system (start at 50, add points for quality signals) can reach 95% for a
well-structured query that returns no data — that's misleading. Starting at the catalog ceiling
means the score reflects the metric's inherent reliability first, then degrades for data
quality problems.

## Examples

**Monthly revenue (REV-001, ceiling=90, T1 source, 12 data rows):**
- Start: 90 (catalog ceiling)
- No penalties apply
- Score: **90%**

**Daily revenue "last 30 days" (REV-001, ceiling=90, T1 source, empty result):**
- Start: 90
- −20 for empty result → 70
- Hard cap for empty results → **60%**

**Customer repeat rate (not in catalog, T1 source, not_available literal result):**
- Start: 60 (not in catalog)
- −20 for null/empty result
- Score: **40%**
```

- [ ] **Step 2: Verify**

```bash
cat conan/skills/data-analyst/references/confidence-guide.md
```

Expected: full file content.

- [ ] **Step 3: Commit**

```bash
git add conan/skills/data-analyst/references/confidence-guide.md
git commit -m "feat(skills): add confidence-guide reference for data-analyst"
```

---

## Task 3: Rewrite `sql.md`

**Files:**
- Modify: `conan/skills/data-analyst/sql.md`

- [ ] **Step 1: Replace the file**

Write `conan/skills/data-analyst/sql.md`:

```markdown
You are a senior data analyst. Your job is to write a single SQL query that correctly answers
the user's question using the available data.

## What you have access to

- **KPI catalog** — known metrics with their source tables and confidence ceilings
- **Source priority guide** — T1 (Gold/pre-aggregated), T2 (Silver/facts & dimensions), T3 (Bronze/staging)
- **Schema** — every available table and its exact columns

## Output format

Return structured output with these fields:
- `sql` — the complete, runnable query
- `source_table` — the primary table used
- `source_tier` — T1, T2, or T3
- `reasoning` — one sentence explaining your table and approach choice

## Rules

**Use only what exists in the schema.** If a table or column isn't listed, it doesn't exist.
Don't invent tables or columns.

**Match time granularity to the right table.** Daily questions → daily tables; monthly questions
→ monthly tables. Using a monthly table for a daily question loses intra-period variation.

**Prefer higher tiers.** T1 (Gold) tables are pre-aggregated and reliable — use them when the
metric is available at that level. T2 is correct when T1 doesn't cover the question.

**Weighted averages on pre-aggregated columns.** This is the most common source of silent errors.
If you're aggregating a column that's already an average (like `avg_discount`, `avg_price`),
you cannot use `AVG()`. Each row in a pre-aggregated table represents a different number of
underlying records — averaging those averages without weighting produces a misleading result.

- ❌ Wrong: `AVG(avg_discount)` — treats a month with 10,000 orders the same as one with 100
- ✅ Right: `SUM(avg_discount * order_count) / SUM(order_count)` — weights by volume

**Produce a direct answer.** The result set should directly answer the question, not a superset
that requires further filtering.

**If the metric can't be answered from the schema**, return a literal SELECT with an explanation
string rather than guessing or using the wrong tables. An honest "not available" is more useful
than a plausible-looking wrong answer.

## Worked examples

### Example 1: Simple aggregate (total revenue)

Question: "what is total revenue?"
KPI catalog: `total_revenue → SUM(extended_price) FROM agg_monthly_lineitem_revenue (T1, ceiling=90)`

```sql
SELECT SUM(extended_price) AS total_revenue
FROM agg_monthly_lineitem_revenue
```

source_table: `agg_monthly_lineitem_revenue`
source_tier: T1
reasoning: "total_revenue is a catalog metric at T1; SUM across all months gives lifetime total."

---

### Example 2: Pre-aggregated average (avg discount by month)

Question: "average discount rate by month"
Schema: `agg_monthly_lineitem_revenue` has columns `monthly_date`, `avg_discount`, `order_count`

```sql
SELECT
    DATE_TRUNC('month', monthly_date) AS month,
    ROUND(
        SUM(avg_discount * order_count) / SUM(order_count) * 100,
        2
    ) AS avg_discount_pct
FROM agg_monthly_lineitem_revenue
GROUP BY 1
ORDER BY 1
```

source_table: `agg_monthly_lineitem_revenue`
source_tier: T1
reasoning: "avg_discount is pre-aggregated; weighted by order_count to avoid averaging-averages error."

---

### Example 3: Metric not in schema (customer repeat rate)

Question: "customer repeat order rate"
Schema: only `agg_daily_orders_totalprice` for customer data — pre-aggregated, no individual order history.

```sql
SELECT
    'not_available' AS status,
    'Schema has no individual order history — cannot distinguish first vs repeat orders' AS reason
```

source_table: `agg_daily_orders_totalprice`
source_tier: T1
reasoning: "Repeat rate requires per-order timestamps per customer. Pre-aggregated table loses that grain."
```

- [ ] **Step 2: Verify line count is reasonable**

```bash
wc -l conan/skills/data-analyst/sql.md
```

Expected: 60–90 lines.

- [ ] **Step 3: Commit**

```bash
git add conan/skills/data-analyst/sql.md
git commit -m "feat(skills): rewrite sql.md with reasoning and worked examples"
```

---

## Task 4: Rewrite `analysis.md`

**Files:**
- Modify: `conan/skills/data-analyst/analysis.md`

- [ ] **Step 1: Replace the file**

Write `conan/skills/data-analyst/analysis.md`:

```markdown
You are a data analyst presenting findings to a business stakeholder. You ran a SQL query and
have the results. Answer the question clearly and concisely.

## Format

Structure your response exactly like this:

**[One sentence leading with the key number and what it means in context. Lead with the insight,
not the methodology. The stakeholder reads this first — make it count.]**

[Markdown table of the result. If more than 20 rows, show the 10 most relevant. Format numbers
readably — commas for thousands, 2 decimal places for currency and percentages.]

**Confidence: [score]% — [one-line justification]**

## Empty or null results

Do not report null values or say "the value is null." Instead:
- State that data is not available for the requested period
- Explain the likely reason (e.g. the dataset covers a different time range)
- Suggest what period the data does cover so the user can reframe their question

## Confidence scoring

See the confidence-guide for the full rubric. Summary:
- Start at the KPI catalog's `confidence_ceiling` for this metric (or 60 if not in catalog)
- −20 if result is empty or all nulls
- −10 if source is T3
- −10 if SQL doesn't match a catalog pattern
- Never exceed the catalog's `confidence_ceiling`
- Never score above 60 for an empty result

## Worked examples

### Example 1: Good result (monthly revenue trend)

Question: "monthly revenue trend"
Source: `agg_monthly_lineitem_revenue` (T1). KPI catalog: `monthly_revenue`, ceiling=90.
Result: 12 months, Jan–Dec 1993.

---

**Monthly revenue held steady around $42M through mid-1993, then climbed to a peak of $51M in
November before a December dip.**

| Month | Revenue |
|---|---|
| 1993-01 | $41,892,345 |
| 1993-02 | $39,104,211 |
| 1993-03 | $40,872,003 |
| 1993-04 | $42,011,887 |
| 1993-05 | $43,200,441 |
| 1993-06 | $44,871,002 |
| 1993-07 | $45,102,334 |
| 1993-08 | $46,200,112 |
| 1993-09 | $47,900,003 |
| 1993-10 | $49,341,220 |
| 1993-11 | $51,344,892 |
| 1993-12 | $44,201,003 |

**Confidence: 90% — T1 Gold source, catalog metric REV-001, 12 months of actual data.**

---

### Example 2: Empty result (date mismatch)

Question: "daily revenue last 30 days"
Source: `agg_daily_lineitem_quantity` (T1). Result: empty (dataset ends 1998, query used current date).

---

**Data is not available for the last 30 days — this dataset covers an earlier period.**

The query returned no rows because it filtered for recent dates, but this dataset ends in 1998.
To see daily revenue data, try asking for a specific historical period, such as "daily revenue
in October 1998."

**Confidence: 30% — Empty result; dataset time range does not match the requested period.**
```

- [ ] **Step 2: Verify**

```bash
wc -l conan/skills/data-analyst/analysis.md
```

Expected: 65–95 lines.

- [ ] **Step 3: Commit**

```bash
git add conan/skills/data-analyst/analysis.md
git commit -m "feat(skills): rewrite analysis.md with ceiling-first confidence and examples"
```

---

## Task 5: Update `data-analyst/SKILL.md`

**Files:**
- Modify: `conan/skills/data-analyst/SKILL.md`

- [ ] **Step 1: Update the file**

Write `conan/skills/data-analyst/SKILL.md`:

```markdown
---
name: data-analyst
description: Data analyst skill for ConAn. Powers SQL generation and result analysis against any database schema. Use when answering data questions, generating SQL, or interpreting query results in a ConAn project.
---

# Data Analyst

This skill powers ConAn's two-phase analysis workflow:

1. **SQL Generation** (`sql.md`) — translates a natural language question into correct SQL using the available schema and KPI context
2. **Result Analysis** (`analysis.md`) — interprets the query result and presents a clear finding with data and a calibrated confidence score

## Design principles

The skill is dataset-agnostic. It works with whatever context is injected at runtime:
- KPI catalog — known metrics, source tables, confidence ceilings
- Source priority guide — T1 (Gold), T2 (Silver), T3 (Bronze) tier definitions
- Schema — available tables and their exact columns

Neither prompt references specific tables or columns. The analyst reads what is provided.

## Reference files

- `references/edge-cases.md` — loaded into SQL context when the schema contains pre-aggregated columns (detected by `avg_` or `agg_` column name prefixes). Covers weighted averages, date mismatches, schema misses.
- `references/confidence-guide.md` — always loaded into analysis context. Full confidence scoring rubric.

## Loading in Python

```python
from pathlib import Path
_SKILL_DIR = Path(__file__).parent / "data-analyst"
_SYSTEM_SQL     = (_SKILL_DIR / "sql.md").read_text()
_SYSTEM_ANALYZE = (_SKILL_DIR / "analysis.md").read_text()
_EDGE_CASES     = (_SKILL_DIR / "references" / "edge-cases.md").read_text()
_CONF_GUIDE     = (_SKILL_DIR / "references" / "confidence-guide.md").read_text()
```
```

- [ ] **Step 2: Commit**

```bash
git add conan/skills/data-analyst/SKILL.md
git commit -m "feat(skills): update data-analyst SKILL.md with reference file docs"
```

---

## Task 6: Update `data_queries.py` — lazy-load edge cases

**Files:**
- Modify: `conan/skills/data_queries.py`
- Modify: `tests/test_data_queries.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_data_queries.py`:

```python
def test_data_queries_appends_edge_cases_for_preaggregate_schema(skill, dispatch):
    """edge-cases.md should appear in the SQL generation context when schema has avg_ columns."""
    mock_sql = SQLGenerationResult(
        sql="SELECT SUM(avg_discount * order_count) / SUM(order_count) FROM agg_monthly",
        source_table="agg_monthly",
        source_tier=SourceTier.t1,
        reasoning="weighted avg",
    )
    mock_analysis = AnalysisResult(
        answer="Avg discount is 5%",
        confidence=80,
        confidence_justification="T1 source",
    )

    captured_user_msgs = []

    def capture_and_return(system, user, model_cls, **kwargs):
        captured_user_msgs.append(user)
        if model_cls.__name__ == "SQLGenerationResult":
            return mock_sql
        return mock_analysis

    with patch("conan.skills.data_queries.query_structured", side_effect=capture_and_return), \
         patch.object(skill.executor, "execute", return_value=[{"avg_discount_pct": 5.0}]), \
         patch.object(skill.kb_loader, "load_for_skill", return_value={
             "kpis_index": "avg_discount metric",
             "source_priority": "T1 > T2 > T3",
             "schema": "agg_monthly_lineitem_revenue: monthly_date, avg_discount, order_count",
         }):
        skill.run("average discount by month", dispatch)

    sql_user_msg = captured_user_msgs[0]
    assert "Edge Cases" in sql_user_msg or "Weighted" in sql_user_msg
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
pytest tests/test_data_queries.py::test_data_queries_appends_edge_cases_for_preaggregate_schema -v
```

Expected: FAIL — assertion error (edge cases not yet injected).

- [ ] **Step 3: Update `data_queries.py`**

Replace `conan/skills/data_queries.py` with:

```python
# conan/skills/data_queries.py
import re
from pathlib import Path
from conan.skills.base import SkillBase
from conan.models import (
    SQLGenerationResult, AnalysisResult, SkillResult, OrchestratorDispatch, SourceTier,
)
from conan.llm import query_structured

_SKILL_DIR = Path(__file__).parent / "data-analyst"
_SYSTEM_SQL     = (_SKILL_DIR / "sql.md").read_text()
_SYSTEM_ANALYZE = (_SKILL_DIR / "analysis.md").read_text()
_EDGE_CASES     = (_SKILL_DIR / "references" / "edge-cases.md").read_text()
_CONF_GUIDE     = (_SKILL_DIR / "references" / "confidence-guide.md").read_text()

_PREAGG_PATTERN = re.compile(r"\bavg_\w+|\bagg_\w+", re.IGNORECASE)


class DataQueriesSkill(SkillBase):
    name = "data-queries"
    description = "Metric lookups, time-series, breakdowns, comparisons"

    def run(self, question: str, dispatch: OrchestratorDispatch) -> SkillResult:
        context = self.kb_loader.load_for_skill(question)
        saved = self.kb_loader.find_saved_query(question)

        if saved:
            sql_result = _sql_from_saved(saved)
        else:
            sql_result = self._generate_sql(question, context)

        rows = self.executor.execute(sql_result.sql)
        analysis = self._analyze(question, sql_result, rows, context)

        return SkillResult(
            answer=analysis.answer,
            sql=sql_result.sql,
            source_table=sql_result.source_table,
            source_tier=sql_result.source_tier,
            confidence=analysis.confidence,
            confidence_justification=analysis.confidence_justification,
        )

    def _generate_sql(self, question: str, context: dict) -> SQLGenerationResult:
        schema = context.get("schema", "")
        domain_section = f"\nDomain KPIs:\n{context['kpi_domain']}" if "kpi_domain" in context else ""
        edge_cases_section = f"\n\n---\n\n{_EDGE_CASES}" if _PREAGG_PATTERN.search(schema) else ""
        user = (
            f"Question: {question}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}\n\n"
            f"Source Priority:\n{context.get('source_priority', '')}\n\n"
            f"Schema:\n{schema}"
            f"{domain_section}"
            f"{edge_cases_section}"
        )
        return query_structured(_SYSTEM_SQL, user, SQLGenerationResult, model=self.model, max_tokens=4096)

    def _analyze(self, question: str, sql_result: SQLGenerationResult, rows: list[dict], context: dict) -> AnalysisResult:
        user = (
            f"Question: {question}\n\n"
            f"SQL: {sql_result.sql}\n"
            f"Source: {sql_result.source_table} ({sql_result.source_tier.value})\n\n"
            f"Result (first 20 rows):\n{rows[:20]}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}\n\n"
            f"---\n\n{_CONF_GUIDE}"
        )
        return query_structured(_SYSTEM_ANALYZE, user, AnalysisResult, model=self.model, max_tokens=4096)


def _sql_from_saved(saved_content: str) -> SQLGenerationResult:
    match = re.search(r"```sql\n(.*?)```", saved_content, re.DOTALL)
    sql = match.group(1).strip() if match else saved_content
    return SQLGenerationResult(
        sql=sql,
        source_table="saved_query",
        source_tier=SourceTier.t1,
        reasoning="Using saved (vetted) query",
    )
```

- [ ] **Step 4: Run all data_queries tests**

```bash
pytest tests/test_data_queries.py -v
```

Expected: all PASS including the new test.

- [ ] **Step 5: Commit**

```bash
git add conan/skills/data_queries.py tests/test_data_queries.py
git commit -m "feat(skills): lazy-load edge-cases for pre-aggregated schemas in data_queries"
```

---

## Task 7: Create `product-analyst/` skill folder

**Files:**
- Create: `conan/skills/product-analyst/SKILL.md`
- Create: `conan/skills/product-analyst/decompose.md`
- Create: `conan/skills/product-analyst/synthesize.md`

- [ ] **Step 1: Create the directory**

```bash
mkdir -p conan/skills/product-analyst
```

- [ ] **Step 2: Write `SKILL.md`**

Write `conan/skills/product-analyst/SKILL.md`:

```markdown
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
```

- [ ] **Step 3: Write `decompose.md`**

Write `conan/skills/product-analyst/decompose.md`:

```markdown
You are a product analyst investigating a causal question. Your job is to generate 2–3 SQL
queries that each test a different possible cause of the phenomenon the user is asking about.

## What you have access to

- **KPI catalog** — known metrics with their source tables
- **Source priority guide** — T1 (Gold), T2 (Silver), T3 (Bronze)
- **Schema** — every available table and its exact columns

## Output format

Return structured output with a list of queries. Each query must have:
- `sql` — a complete, runnable query
- `source_table` — the primary table used
- `source_tier` — T1, T2, or T3
- `reasoning` — the hypothesis this query is testing

## Rules

**Each query tests a different hypothesis.** The goal is to triangulate a cause from multiple
angles. Two queries testing the same angle (e.g. two time-trend queries) waste a diagnostic
slot — this is not allowed.

**Cover different dimensions.** Good diagnostics span different explanatory dimensions:
- Time trend — is this a sustained change or a one-period spike?
- Segment breakdown — is it isolated to a region, customer group, or product category?
- Product mix — did the composition of orders change?
- Funnel — did a step in the conversion process fail?

**Use only tables and columns that appear in the schema.**

**Keep queries focused.** Each query should return the minimal result set needed to prove
or disprove its hypothesis.

## Worked example

Question: "Why did revenue drop in March?"

Query 1 — Time trend hypothesis (is this sustained or a one-month event?):
```sql
SELECT
    DATE_TRUNC('month', monthly_date) AS month,
    SUM(extended_price) AS revenue
FROM agg_monthly_lineitem_revenue
WHERE monthly_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '6 months'
GROUP BY 1
ORDER BY 1
```
reasoning: "Check if revenue drop is isolated to March or part of a sustained decline."

Query 2 — Supplier concentration hypothesis (did key suppliers pull back?):
```sql
SELECT
    l_suppkey,
    COUNT(*) AS order_count,
    SUM(l_extendedprice) AS revenue
FROM fct_lineitem
WHERE DATE_TRUNC('month', l_shipdate) = '1998-03-01'
GROUP BY 1
ORDER BY revenue DESC
LIMIT 10
```
reasoning: "Identify whether a small number of suppliers drove the drop."

Query 3 — Discount rate hypothesis (did margin compression reduce net revenue?):
```sql
SELECT
    DATE_TRUNC('month', monthly_date) AS month,
    SUM(avg_discount * order_count) / SUM(order_count) AS weighted_avg_discount
FROM agg_monthly_lineitem_revenue
WHERE monthly_date >= DATE_TRUNC('month', CURRENT_DATE) - INTERVAL '4 months'
GROUP BY 1
ORDER BY 1
```
reasoning: "Check if increasing discounts compressed net revenue in March."
```

- [ ] **Step 4: Write `synthesize.md`**

Write `conan/skills/product-analyst/synthesize.md`:

```markdown
You are a product analyst synthesising evidence from multiple diagnostic queries into a single
root cause finding. Present your conclusion clearly to a business stakeholder.

## What you receive

- The original question
- Results from 2–3 diagnostic queries, each tagged with its hypothesis
- The KPI catalog for confidence context

## Format

Structure your response exactly like this:

**Finding:** [One sentence — the most likely cause, stated directly. Lead with the cause.]

**Evidence:**
- [Hypothesis 1]: [What the data showed — cite specific numbers]
- [Hypothesis 2]: [What the data showed — cite specific numbers]
- [Hypothesis 3]: [What the data showed — cite specific numbers]

**Ruled out:** [Hypotheses the data contradicted, and why]

**Confidence: [score]% — [one-line justification]**

## Rules

**Name the most likely cause first.** Don't bury it. The finding sentence is the conclusion.

**Cite specific numbers.** "Revenue fell 18% in March" beats "revenue declined." Numbers let
the stakeholder decide whether to act.

**Explicitly rule out alternatives.** If a hypothesis was tested and the data contradicted it,
say so. Absence of evidence is informative — it narrows the cause.

**If all queries failed**, state that the investigation could not proceed due to data access
errors and recommend what data would be needed to answer the question.

## Confidence scoring

Start at 50. Apply:
- +20 if source is T1 or T2
- +20 if the primary metric is in the KPI catalog
- +15 if results contain actual data rows
- +5 per successful diagnostic query beyond the first

Cap at 85. Do not exceed 50 if all queries returned errors or empty results.

## Worked example

Question: "Why did revenue drop in March?"
- Time trend: Revenue flat Jan–Feb, dropped 18% in March, partially recovered in April.
- Supplier concentration: Top 3 suppliers placed 40% fewer orders in March; Supplier #42 fell from $1.2M to $0.2M.
- Discount rate: Stable at ~5% through March. No change.

---

**Finding:** The March revenue drop was driven by a sudden reduction in orders from a small number of key suppliers, not by pricing pressure or a sustained trend.

**Evidence:**
- Time trend: Revenue dropped 18% in March only and partially recovered in April — confirming a one-month event, not a drift
- Supplier concentration: The top 3 suppliers placed 40% fewer orders; Supplier #42 alone fell from $1.2M to $0.2M
- Discount rate: Held steady at ~5% through March — margin compression is not a factor

**Ruled out:** Gradual revenue drift (time trend was flat before March); pricing pressure (discount rates unchanged)

**Confidence: 75% — T2 sources, catalog metric, 3 successful queries, directional finding**
```

- [ ] **Step 5: Verify all three files exist**

```bash
ls -la conan/skills/product-analyst/
```

Expected: `SKILL.md`, `decompose.md`, `synthesize.md`

- [ ] **Step 6: Commit**

```bash
git add conan/skills/product-analyst/
git commit -m "feat(skills): add product-analyst skill folder with decompose and synthesize prompts"
```

---

## Task 8: Refactor `product_analyst.py`

**Files:**
- Modify: `conan/skills/product_analyst.py`
- Modify: `tests/test_product_analyst.py`

- [ ] **Step 1: Write the failing test for all-queries-fail early return**

Add to `tests/test_product_analyst.py`:

```python
def test_product_analyst_returns_early_when_all_queries_fail(skill, dispatch):
    """When every diagnostic query fails, return a SkillResult without calling synthesize."""
    from conan.executor import ExecutorError
    mock_diagnostic = DiagnosticQueries(
        queries=[
            SQLGenerationResult(
                sql="SELECT SUM(amount) FROM nonexistent_a",
                source_table="nonexistent_a",
                source_tier=SourceTier.t3,
                reasoning="Try source A",
            ),
            SQLGenerationResult(
                sql="SELECT SUM(amount) FROM nonexistent_b",
                source_table="nonexistent_b",
                source_tier=SourceTier.t3,
                reasoning="Try source B",
            ),
        ],
        reasoning="Diagnostic attempt",
    )

    call_count = {"n": 0}

    def side_effect(system, user, model_cls, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return mock_diagnostic
        raise AssertionError("synthesize should not be called when all queries fail")

    with patch("conan.skills.product_analyst.query_structured", side_effect=side_effect), \
         patch.object(skill.executor, "execute", side_effect=ExecutorError("table not found")):
        result = skill.run("why did revenue drop?", dispatch)

    assert result.confidence <= 30
    assert "not" in result.answer.lower() or "unavailable" in result.answer.lower() or "failed" in result.answer.lower()
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
pytest tests/test_product_analyst.py::test_product_analyst_returns_early_when_all_queries_fail -v
```

Expected: FAIL — either AssertionError (synthesize is called) or the answer/confidence doesn't match.

- [ ] **Step 3: Replace `product_analyst.py`**

Write `conan/skills/product_analyst.py`:

```python
# conan/skills/product_analyst.py
from pathlib import Path
from conan.skills.base import SkillBase
from conan.models import (
    DiagnosticQueries, AnalysisResult, SkillResult, OrchestratorDispatch,
)
from conan.executor import ExecutorError
from conan.llm import query_structured

_SKILL_DIR = Path(__file__).parent / "product-analyst"
_SYSTEM_DECOMPOSE = (_SKILL_DIR / "decompose.md").read_text()
_SYSTEM_SYNTHESIZE = (_SKILL_DIR / "synthesize.md").read_text()


class ProductAnalystSkill(SkillBase):
    name = "product-analyst"
    description = "Root cause analysis, anomaly diagnosis, why-did-X-change questions"

    def run(self, question: str, dispatch: OrchestratorDispatch) -> SkillResult:
        context = self.kb_loader.load_for_skill(question)
        diagnostic = self._decompose(question, context)

        results = []
        for q in diagnostic.queries:
            try:
                rows = self.executor.execute(q.sql)
                results.append({"sql": q.sql, "source": q.source_table, "rows": rows[:20]})
            except ExecutorError as e:
                results.append({"sql": q.sql, "error": str(e)})

        if all("error" in r for r in results):
            return SkillResult(
                answer=(
                    "Could not diagnose — all diagnostic queries failed due to data access errors. "
                    "Check that the required tables are available in the schema."
                ),
                sql=diagnostic.queries[0].sql if diagnostic.queries else None,
                source_table=None,
                source_tier=None,
                confidence=20,
                confidence_justification="All diagnostic queries failed; no data available.",
            )

        analysis = self._synthesize(question, results, context)
        primary = diagnostic.queries[0] if diagnostic.queries else None

        return SkillResult(
            answer=analysis.answer,
            sql=primary.sql if primary else None,
            source_table=primary.source_table if primary else None,
            source_tier=primary.source_tier if primary else None,
            confidence=analysis.confidence,
            confidence_justification=analysis.confidence_justification,
        )

    def _decompose(self, question: str, context: dict) -> DiagnosticQueries:
        domain_section = f"\nDomain KPIs:\n{context['kpi_domain']}" if "kpi_domain" in context else ""
        user = (
            f"Question: {question}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}\n\n"
            f"Source Priority:\n{context.get('source_priority', '')}\n\n"
            f"Schema:\n{context.get('schema', '')}"
            f"{domain_section}\n\n"
            "Generate 2-3 diagnostic SQL queries to investigate this question."
        )
        return query_structured(_SYSTEM_DECOMPOSE, user, DiagnosticQueries, model=self.model, max_tokens=2048)

    def _synthesize(self, question: str, results: list[dict], context: dict) -> AnalysisResult:
        user = (
            f"Question: {question}\n\n"
            f"Diagnostic results:\n{results}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}"
        )
        return query_structured(_SYSTEM_SYNTHESIZE, user, AnalysisResult, model=self.model, max_tokens=2048)
```

- [ ] **Step 4: Run all product_analyst tests**

```bash
pytest tests/test_product_analyst.py -v
```

Expected: all 3 tests PASS (existing 2 + new all-fail test).

- [ ] **Step 5: Run the full test suite**

```bash
pytest -v
```

Expected: all tests PASS, no regressions.

- [ ] **Step 6: Commit**

```bash
git add conan/skills/product_analyst.py tests/test_product_analyst.py
git commit -m "feat(skills): refactor product_analyst to load prompts from files, raise token limits, add all-fail recovery"
```

---

## Task 9: Final verification

- [ ] **Step 1: Confirm folder structure matches spec**

```bash
find conan/skills/data-analyst conan/skills/product-analyst -type f | sort
```

Expected output:
```
conan/skills/data-analyst/SKILL.md
conan/skills/data-analyst/analysis.md
conan/skills/data-analyst/references/confidence-guide.md
conan/skills/data-analyst/references/edge-cases.md
conan/skills/data-analyst/sql.md
conan/skills/product-analyst/SKILL.md
conan/skills/product-analyst/decompose.md
conan/skills/product-analyst/synthesize.md
```

- [ ] **Step 2: Confirm prompts load without errors**

```bash
python -c "
from conan.skills.data_queries import DataQueriesSkill, _SYSTEM_SQL, _SYSTEM_ANALYZE, _EDGE_CASES, _CONF_GUIDE
from conan.skills.product_analyst import ProductAnalystSkill, _SYSTEM_DECOMPOSE, _SYSTEM_SYNTHESIZE
assert len(_SYSTEM_SQL) > 500, 'sql.md too short'
assert len(_SYSTEM_ANALYZE) > 500, 'analysis.md too short'
assert len(_EDGE_CASES) > 200, 'edge-cases.md too short'
assert len(_CONF_GUIDE) > 200, 'confidence-guide.md too short'
assert len(_SYSTEM_DECOMPOSE) > 500, 'decompose.md too short'
assert len(_SYSTEM_SYNTHESIZE) > 500, 'synthesize.md too short'
print('All skill files load correctly')
"
```

Expected: `All skill files load correctly`

- [ ] **Step 3: Full test suite**

```bash
pytest -v
```

Expected: all tests PASS.
