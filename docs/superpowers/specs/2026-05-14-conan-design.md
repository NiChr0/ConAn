# ConAn — Design Spec

**Date:** 2026-05-14  
**Status:** Approved  
**Builds on:** Schemalytics v1.0.1

---

## What It Is

ConAn is a standalone Python CLI — the analytics query layer on top of Schemalytics. Schemalytics builds the warehouse model (dbt project + semantic layer); ConAn sits on top of it to answer analytics questions in plain English against a live database, with confidence scores and source citations.

Two commands:
- `conan bootstrap -p ./dbt_project -c postgresql://... -o ./conan_kb` — one-time setup
- `conan chat -p ./conan_kb -c postgresql://...` — interactive chat REPL

---

## Architecture

### Two Phases

**Bootstrap** (one-time per project):
```
semantic_layer.yml + dbt project
        ↓
mechanical mapping (no LLM)
        ↓
LLM enrichment pass (validates, amends, fills gaps)
        ↓
knowledge base written to disk
```

**Chat** (runtime):
```
user question
        ↓
Orchestrator LLM — decomposes + dispatches skill(s)
        ↓
Skill LLM — loads context, generates SQL, executes, scores confidence
        ↓
SQLAlchemy executor — executes query, returns result set
        ↓
Orchestrator synthesises + streams answer to terminal
        ↓
Session logged to conan_kb/sessions/
```

### Infrastructure

Same stack as Schemalytics:
- `instructor` + Pydantic for all structured LLM outputs
- `llm.py` abstraction over Ollama (default) and Anthropic (optional via env var)
- SQLAlchemy for DB execution (no row/byte caps in v1 — future addition)
- Click for CLI

Default model: `gemma4:e4b` (fits comfortably on 24GB unified memory, native tool calling, 128K context).  
Per-component overrides via env vars: `CONAN_ORCHESTRATOR_MODEL`, `CONAN_SKILL_MODEL`.

---

## Bootstrap Pipeline

### Step 1 — Mechanical Mapping (no LLM)

Reads `semantic_layer.yml` + dbt project and translates directly:

| Schemalytics output | ConAn KB artifact |
|---|---|
| `metrics` entries | `kpis-index.md` rows |
| `semantic_models` + measures | `kpis-<domain>.md` full entries |
| Gold models (`agg_*`) | Source priority T1 |
| Silver facts/dims (`fct_*`, `dim_*`) | Source priority T2 |
| Bronze staging (`stg_*`) | Source priority T3 |
| All table/column metadata | `schema/tables.md` |

Maturity defaults: all metrics start as `Directional`, confidence ceiling 70%.

### Step 2 — LLM Enrichment Pass

One LLM enrichment call per domain (batched if >5 domains, max 5 metrics per call) receives the KB stubs + raw `semantic_layer.yml` context and:
- Promotes obvious L0/L1 metrics to `Validated` with higher confidence ceilings
- Writes proper descriptions, flags likely formula errors
- Assigns L0–L3 tiers based on business centrality
- Marks metrics with no source table as `Proposed`

User reviews a summary of changes before the KB is written to disk (same confidence-gate UX as Schemalytics).

---

## Runtime Chat Flow

### Orchestrator

LLM call using `gemma4:e4b`. Responsibilities:
- Classify intent and decompose compound questions
- Select which skill(s) to invoke (one or two, sequential)
- Synthesise final answer from skill output(s)
- Stream answer to terminal with confidence score + source citation

Max two skill hops per question. Deeper chains are rejected — the orchestrator re-routes instead.

### Skills (v1)

Two skills ship in v1:

| Skill | Triggers | Behaviour |
|---|---|---|
| `data-queries` | "what is X", "show me Y", "trend of Z", "compare A vs B" | Metric lookups, time-series, breakdowns. The workhorse. |
| `product-analyst` | "why did X change", "what caused Y", "explain the drop in Z" | Root cause analysis, anomaly diagnosis. Decomposes into sub-queries. |

Four additional skills are stubbed (not implemented in v1):
- `experiment-analyst`
- `feature-planner`
- `dashboard-builder`
- `competitive-research`

### Skill Internals

Each skill is a Python class with:
- `can_handle(question) -> bool` — used as a fallback hint; orchestrator LLM makes the final routing decision
- `run(question, context) -> SkillResult` — full LLM-driven execution

Inside `run()`:
1. Load Context Manifest — only relevant KPI domain file + source priority + schema
2. Check saved queries index for a matching vetted query
3. If no match: LLM generates SQL grounded in the loaded context
4. Executor runs the SQL and returns the result set
5. LLM reasons over the result set and scores confidence
6. Returns `SkillResult` (answer, confidence, source citations, sql used)

### Confidence Scoring

Follows ConAn ARCHITECTURE.md formula (start at 50%, add points):

| Factor | Points |
|---|---|
| Metric in KPI catalog | +20 |
| T1 source (Gold/Silver) | +20 |
| T2 source | +10 |
| Saved query (exact match) | use saved value as ceiling |
| Canonical pattern | +20 |
| Data freshness <24h | +15 |
| Direct lookup | +15 |

### Terminal Output Format

```
── Answer ──────────────────────────────────────
Revenue last month: $142,340 (↓12% vs prior month)

Source: fct_orders.amount  |  T1 (Gold layer)
Confidence: 84% — validated metric, T1 source, canonical SQL pattern
────────────────────────────────────────────────
```

Answers stream token-by-token. Confidence line appears after the answer.

### Session Logging

Every interaction written to `conan_kb/sessions/<date>-<id>.md`:
- Question asked
- Skill(s) invoked
- Tables queried
- SQL used
- Confidence score + breakdown
- Whether a KB gap was flagged

Saved queries accumulate in `conan_kb/queries/` — vetted SQL patterns that future sessions reuse instead of regenerating.

---

## Knowledge Base Structure

Written to disk on bootstrap, human-readable and editable:

```
conan_kb/
├── kpis-index.md               # Master metric table (ID, domain, tier, maturity, source)
├── kpis-<domain>.md            # One per domain — full metric definitions
├── source_priority.md          # T1/T2/T3 tier mapping derived from dbt layers
├── schema/
│   └── tables.md               # Table + column reference
├── queries/
│   ├── index.json              # Saved queries catalog (auto-generated)
│   └── <id>.md                 # One per saved query
└── sessions/
    └── <date>-<id>.md          # Session log
```

---

## Directory Layout

```
conan/
├── conan/
│   ├── cli.py                  # click: bootstrap + chat commands
│   ├── orchestrator.py         # LLM orchestrator
│   ├── llm.py                  # Ollama/Anthropic abstraction
│   ├── models.py               # Pydantic models for all structured I/O
│   ├── executor.py             # SQLAlchemy execution + dry-run
│   ├── bootstrap/
│   │   ├── mapper.py           # Mechanical: semantic_layer.yml → KB skeleton
│   │   └── enricher.py         # LLM enrichment pass
│   ├── skills/
│   │   ├── base.py             # SkillBase + SkillResult
│   │   ├── data_queries.py
│   │   └── product_analyst.py
│   └── kb/
│       ├── loader.py           # Loads KB files into skill context
│       └── writer.py           # Writes/updates KB on disk
├── tests/
├── pyproject.toml
└── README.md
```

---

## What's Out of Scope (v1)

- Competitive research skill (requires external data sources)
- Dashboard / HTML output
- Multi-database support (PostgreSQL only, same as Schemalytics)
- Web UI
- KPI graduation workflow (sessions accumulate, manual promotion later)
