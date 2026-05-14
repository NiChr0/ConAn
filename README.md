# ConAn

AI analytics partner for [Schemalytics](https://github.com/NiChr0/schemalytics) projects. ConAn sits on top of your dbt semantic layer and lets you ask plain-English questions against a live PostgreSQL database — returning answers with SQL, source provenance, and a confidence score.

## How it works

```
Schemalytics output          ConAn
(semantic_layer.yml)   →   bootstrap   →   Knowledge Base (KB)
                                                  ↓
                           conan chat   →   Orchestrator LLM
                                          ↙              ↘
                                data-queries      product-analyst
                                    ↓                    ↓
                              SQL generation       Multi-query
                              + analysis           root cause
                                    ↓                    ↓
                               PostgreSQL          PostgreSQL
                                    ↓                    ↓
                              Answer + confidence score
```

**Bootstrap** (one-time): reads `semantic_layer.yml`, maps metrics to a KPI catalog, runs an LLM enrichment pass to validate maturity/tier/descriptions, and writes the KB to disk.

**Chat** (runtime): an LLM orchestrator classifies each question and routes it to the right skill — metric lookups go to `data-queries`, root-cause questions go to `product-analyst`. Each skill generates SQL, executes it, and scores confidence against the KB.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com) running locally with `gemma4:e4b` pulled (`ollama pull gemma4:e4b`)
- A Schemalytics dbt project with `semantic_layer.yml`
- A live PostgreSQL database

## Installation

```bash
pip install -e .
```

## Usage

### 1. Bootstrap the knowledge base

```bash
conan bootstrap \
  -p /path/to/schemalytics/output \
  -c "postgresql://user:pass@localhost/mydb" \
  -o ./conan_kb
```

This reads your semantic layer, maps all metrics, runs an LLM enrichment pass (you'll be prompted to confirm changes), and writes the KB to `./conan_kb`.

### 2. Chat with your data

```bash
conan chat \
  -p ./conan_kb \
  -c "postgresql://user:pass@localhost/mydb"
```

```
ConAn ready. Type your question (Ctrl+C to exit).

You: what was revenue last month?

── Answer ────────────────────────────────────────────
Revenue last month was $1,243,820.

Source: agg_daily_revenue  |  T1
Confidence: 88% — validated metric, T1 gold source
────────────────────────────────────────────────────

You: why did revenue drop in April?

── Answer ────────────────────────────────────────────
Revenue dropped 14% in April, driven primarily by a
decline in the EMEA region (-31%) and fewer new
customer conversions in the SMB segment.

Source: fct_orders  |  T2
Confidence: 71% — directional, T2 source, multi-query
────────────────────────────────────────────────────
```

## Configuration

| Env variable | Default | Description |
|---|---|---|
| `CONAN_LLM_PROVIDER` | `ollama` | `ollama` or `anthropic` |
| `CONAN_SKILL_MODEL` | `gemma4:e4b` | Model for skill LLM calls |
| `CONAN_ORCHESTRATOR_MODEL` | `gemma4:e4b` | Model for orchestrator dispatch |
| `ANTHROPIC_API_KEY` | — | Required if provider is `anthropic` |

To use Anthropic Claude instead of Ollama:

```bash
export CONAN_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export CONAN_SKILL_MODEL=claude-haiku-4-5-20251001
```

## Knowledge Base structure

```
conan_kb/
├── kpis-index.md          # All KPIs — ID, metric, domain, tier, maturity
├── kpis-revenue.md        # Per-domain KPI detail (formula, description, notes)
├── kpis-users.md
├── source_priority.md     # T1/T2/T3 table routing rules
├── schema/
│   └── tables.md          # All tables with tier and description
├── queries/
│   └── index.json         # Saved vetted queries (reused automatically)
└── sessions/
    └── *.md               # Session logs
```

## Confidence scoring

ConAn scores every answer 0–100 based on:

- Metric in KPI catalog (+20)
- T1 Gold source (+20), T2 Silver (+10)
- SQL matches catalog pattern (+20)
- Live data available (+15)
- Direct lookup / multiple diagnostic queries (+5–15)

Capped by the metric's `confidence_ceiling` from the KB (default 70 for new metrics, up to 95 for validated north-stars).

## Skills

| Skill | When used | Approach |
|---|---|---|
| `data-queries` | "What is X?", trends, breakdowns | Single SQL generation + analysis |
| `product-analyst` | "Why did X change?", anomalies | 2-3 diagnostic queries + synthesis |

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```
