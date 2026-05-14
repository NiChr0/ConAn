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
