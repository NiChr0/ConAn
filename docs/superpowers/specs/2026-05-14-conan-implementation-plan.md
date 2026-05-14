# ConAn Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build ConAn — a standalone Python CLI that bootstraps a knowledge base from a Schemalytics dbt project and provides an interactive AI chat interface for analytics questions against a live PostgreSQL database.

**Architecture:** Two phases — bootstrap (one-time: reads semantic_layer.yml, maps to KB, LLM enrichment pass) and chat (runtime: orchestrator LLM dispatches to skill LLMs that generate SQL, execute it, and score confidence). Same llm.py abstraction as Schemalytics (instructor + Pydantic over Ollama/Anthropic).

**Tech Stack:** Python 3.11+, Click, instructor, Pydantic v2, SQLAlchemy 2, psycopg2-binary, PyYAML, rich, pytest, pytest-mock. Default model: `gemma4:e4b` via Ollama.

**Spec:** `2026-05-14-conan-design.md` (same directory as this file)

---

## File Map

```
conan/
├── conan/
│   ├── __init__.py
│   ├── cli.py                       # Click: bootstrap + chat commands
│   ├── llm.py                       # Ollama/Anthropic abstraction (mirrors Schemalytics)
│   ├── models.py                    # All Pydantic models
│   ├── executor.py                  # SQLAlchemy query execution
│   ├── orchestrator.py              # LLM orchestrator: dispatch + synthesise
│   ├── bootstrap/
│   │   ├── __init__.py
│   │   ├── mapper.py                # Mechanical: semantic_layer.yml → KB skeleton
│   │   └── enricher.py             # LLM enrichment pass
│   ├── skills/
│   │   ├── __init__.py
│   │   ├── base.py                  # SkillBase abstract class
│   │   ├── data_queries.py          # Metric lookups, trends, breakdowns
│   │   └── product_analyst.py       # Root cause, anomaly diagnosis
│   └── kb/
│       ├── __init__.py
│       ├── loader.py                # Load KB files into skill context
│       └── writer.py                # Write/update KB markdown files on disk
├── tests/
│   ├── conftest.py                  # Shared fixtures
│   ├── test_models.py
│   ├── test_executor.py
│   ├── test_mapper.py
│   ├── test_kb_writer.py
│   ├── test_kb_loader.py
│   ├── test_enricher.py
│   ├── test_data_queries.py
│   ├── test_product_analyst.py
│   ├── test_orchestrator.py
│   └── test_cli.py
├── pyproject.toml
└── README.md
```

---

## Task 1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `conan/__init__.py`
- Create: `conan/bootstrap/__init__.py`
- Create: `conan/skills/__init__.py`
- Create: `conan/kb/__init__.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create directory structure**

```bash
mkdir -p conan/conan/bootstrap conan/conan/skills conan/conan/kb conan/tests
touch conan/conan/__init__.py conan/conan/bootstrap/__init__.py conan/conan/skills/__init__.py conan/conan/kb/__init__.py conan/tests/__init__.py
```

- [ ] **Step 2: Write pyproject.toml**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "conan"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "click>=8.0",
    "instructor>=1.0",
    "openai>=1.0",
    "anthropic>=0.20",
    "sqlalchemy>=2.0",
    "psycopg2-binary>=2.9",
    "pydantic>=2.0",
    "pyyaml>=6.0",
    "rich>=13.0",
]

[project.optional-dependencies]
dev = ["pytest>=8.0", "pytest-mock>=3.0"]

[project.scripts]
conan = "conan.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["conan"]
```

- [ ] **Step 3: Install in dev mode**

```bash
cd conan && pip install -e ".[dev]"
```

Expected: `Successfully installed conan-0.1.0`

- [ ] **Step 4: Commit**

```bash
git init && git add pyproject.toml conan/ tests/
git commit -m "feat: project scaffold"
```

---

## Task 2: Core Models

**Files:**
- Create: `conan/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_models.py
import pytest
from conan.models import (
    SemanticLayer, SemanticModel, SemanticMeasure, SemanticMetric,
    KPIEntry, KPIMaturity, KPITier, SourceTier,
    KnowledgeBase, TableSource, SkillResult,
)


SAMPLE_YAML = """
version: 2
semantic_models:
  - name: fct_orders
    description: Order facts
    model: ref('fct_orders')
    entities:
      - name: order_id
        type: primary
        expr: order_id
    dimensions:
      - name: order_date
        type: time
        expr: order_date
        description: Order date
    measures:
      - name: total_revenue
        agg: sum
        expr: amount
        description: Total revenue
metrics:
  - name: monthly_revenue
    label: Monthly Revenue
    description: Revenue per month
    type: simple
    type_params:
      measure: total_revenue
"""


def test_semantic_layer_parses_from_yaml_string():
    layer = SemanticLayer.from_yaml_string(SAMPLE_YAML)
    assert len(layer.semantic_models) == 1
    assert layer.semantic_models[0].name == "fct_orders"
    assert layer.semantic_models[0].measures[0].name == "total_revenue"
    assert len(layer.metrics) == 1
    assert layer.metrics[0].name == "monthly_revenue"


def test_semantic_layer_from_yaml_file(tmp_path):
    f = tmp_path / "semantic_layer.yml"
    f.write_text(SAMPLE_YAML)
    layer = SemanticLayer.from_yaml_file(f)
    assert layer.metrics[0].label == "Monthly Revenue"


def test_kpi_entry_defaults():
    kpi = KPIEntry(id="REV-001", metric="monthly_revenue", domain="revenue")
    assert kpi.maturity == KPIMaturity.directional
    assert kpi.confidence_ceiling == 70
    assert kpi.tier == KPITier.l2


def test_skill_result_requires_confidence():
    result = SkillResult(
        answer="Revenue was $142,340",
        confidence=84,
        confidence_justification="validated metric, T1 source",
    )
    assert result.confidence == 84
    assert result.sql is None
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd conan && pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.models'`

- [ ] **Step 3: Write models.py**

```python
# conan/models.py
from __future__ import annotations
from enum import Enum
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel


# ── Semantic Layer (input from Schemalytics) ──────────────────────────────────

class SemanticEntity(BaseModel):
    name: str
    type: str
    expr: str

class SemanticDimension(BaseModel):
    name: str
    type: str
    expr: str
    description: str = ""

class SemanticMeasure(BaseModel):
    name: str
    agg: str
    expr: str
    description: str = ""

class SemanticModel(BaseModel):
    name: str
    description: str = ""
    model: str
    entities: list[SemanticEntity] = []
    dimensions: list[SemanticDimension] = []
    measures: list[SemanticMeasure] = []

class SemanticMetric(BaseModel):
    name: str
    label: str = ""
    description: str = ""
    type: str = "simple"
    type_params: dict[str, Any] = {}

class SemanticLayer(BaseModel):
    version: int = 2
    semantic_models: list[SemanticModel] = []
    metrics: list[SemanticMetric] = []

    @classmethod
    def from_yaml_string(cls, content: str) -> "SemanticLayer":
        return cls(**yaml.safe_load(content))

    @classmethod
    def from_yaml_file(cls, path: Path) -> "SemanticLayer":
        return cls.from_yaml_string(path.read_text())


# ── Knowledge Base ────────────────────────────────────────────────────────────

class KPIMaturity(str, Enum):
    proposed = "Proposed"
    directional = "Directional"
    validated = "Validated"

class KPITier(str, Enum):
    l0 = "L0"
    l1 = "L1"
    l2 = "L2"
    l3 = "L3"

class SourceTier(str, Enum):
    t1 = "T1"
    t2 = "T2"
    t3 = "T3"

class KPIEntry(BaseModel):
    id: str
    metric: str
    domain: str
    tier: KPITier = KPITier.l2
    maturity: KPIMaturity = KPIMaturity.directional
    confidence_ceiling: int = 70
    source_table: str = ""
    description: str = ""
    formula: str = ""
    notes: str = ""

class TableSource(BaseModel):
    table_name: str
    tier: SourceTier
    description: str = ""

class KnowledgeBase(BaseModel):
    project_name: str
    kpis: list[KPIEntry] = []
    sources: list[TableSource] = []


# ── LLM Output Models ─────────────────────────────────────────────────────────

class EnrichmentResult(BaseModel):
    metric_id: str
    tier: KPITier
    maturity: KPIMaturity
    confidence_ceiling: int
    description: str
    formula: str = ""
    notes: str = ""

class EnrichmentSummary(BaseModel):
    changes: list[EnrichmentResult]
    gaps: list[str] = []

class OrchestratorDispatch(BaseModel):
    skill: str  # "data-queries" or "product-analyst"
    reasoning: str
    sub_questions: list[str] = []

class SQLGenerationResult(BaseModel):
    sql: str
    source_table: str
    source_tier: SourceTier
    reasoning: str

class DiagnosticQueries(BaseModel):
    queries: list[SQLGenerationResult]
    reasoning: str

class AnalysisResult(BaseModel):
    answer: str
    confidence: int
    confidence_justification: str

class SkillResult(BaseModel):
    answer: str
    sql: str | None = None
    source_table: str | None = None
    source_tier: SourceTier | None = None
    confidence: int
    confidence_justification: str
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_models.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add conan/models.py tests/test_models.py
git commit -m "feat: core Pydantic models"
```

---

## Task 3: LLM Abstraction

**Files:**
- Create: `conan/llm.py`
- Create: `tests/test_llm.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_llm.py
import os
import pytest
from unittest.mock import patch, MagicMock
from pydantic import BaseModel
from conan.llm import query_structured


class _TestModel(BaseModel):
    value: str


def test_query_structured_uses_ollama_by_default(monkeypatch):
    monkeypatch.delenv("CONAN_LLM_PROVIDER", raising=False)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _TestModel(value="ok")

    with patch("conan.llm._get_ollama_client", return_value=mock_client):
        result = query_structured("sys", "usr", _TestModel)

    mock_client.chat.completions.create.assert_called_once()
    assert result.value == "ok"


def test_query_structured_uses_default_model(monkeypatch):
    monkeypatch.delenv("CONAN_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("CONAN_SKILL_MODEL", raising=False)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _TestModel(value="ok")

    with patch("conan.llm._get_ollama_client", return_value=mock_client):
        query_structured("sys", "usr", _TestModel)

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gemma4:e4b"


def test_query_structured_respects_model_override(monkeypatch):
    monkeypatch.delenv("CONAN_LLM_PROVIDER", raising=False)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _TestModel(value="ok")

    with patch("conan.llm._get_ollama_client", return_value=mock_client):
        query_structured("sys", "usr", _TestModel, model="gemma4:26b")

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gemma4:26b"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_llm.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.llm'`

- [ ] **Step 3: Write llm.py (mirrors Schemalytics pattern exactly)**

```python
# conan/llm.py
"""LLM client abstraction — Ollama (default) or Anthropic, via instructor."""
from __future__ import annotations
import os
from typing import TypeVar, Type
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

OLLAMA_DEFAULT_MODEL = os.environ.get("CONAN_SKILL_MODEL", "gemma4:e4b")
ANTHROPIC_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
MAX_RETRIES = 3

_ollama_client: object | None = None


def get_provider() -> str:
    return os.environ.get("CONAN_LLM_PROVIDER", "ollama").lower()


def _get_ollama_client() -> object:
    global _ollama_client
    if _ollama_client is None:
        from openai import OpenAI
        import instructor
        _ollama_client = instructor.from_openai(
            OpenAI(base_url="http://localhost:11434/v1", api_key="ollama", timeout=600),
            mode=instructor.Mode.JSON,
        )
    return _ollama_client


def query_structured(
    system: str,
    user: str,
    response_model: Type[T],
    model: str | None = None,
    max_tokens: int = 2048,
) -> T:
    """Call the LLM and return a validated Pydantic response via instructor."""
    provider = get_provider()

    if model is None:
        model = ANTHROPIC_DEFAULT_MODEL if provider == "anthropic" else OLLAMA_DEFAULT_MODEL

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    if provider == "anthropic":
        import anthropic
        import instructor
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY required when CONAN_LLM_PROVIDER=anthropic")
        client = instructor.from_anthropic(anthropic.Anthropic(api_key=api_key))
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            response_model=response_model,
            max_retries=MAX_RETRIES,
        )

    client = _get_ollama_client()
    return client.chat.completions.create(
        model=model,
        messages=messages,
        response_model=response_model,
        max_retries=MAX_RETRIES,
        temperature=0,
        max_tokens=max_tokens,
        extra_body={"num_ctx": 16384, "num_predict": max_tokens},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_llm.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add conan/llm.py tests/test_llm.py
git commit -m "feat: LLM abstraction (Ollama/Anthropic via instructor)"
```

---

## Task 4: DB Executor

**Files:**
- Create: `conan/executor.py`
- Create: `tests/test_executor.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_executor.py
import pytest
from unittest.mock import patch, MagicMock
from conan.executor import Executor, ExecutorError


def test_executor_returns_list_of_dicts():
    mock_row = MagicMock()
    mock_row._mapping = {"value": 1}
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.return_value = [mock_row]

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn

    with patch("conan.executor.create_engine", return_value=mock_engine):
        executor = Executor("postgresql://localhost/test")
        result = executor.execute("SELECT 1 AS value")

    assert result == [{"value": 1}]


def test_executor_raises_executor_error_on_failure():
    from sqlalchemy.exc import SQLAlchemyError
    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.execute.side_effect = SQLAlchemyError("table not found")

    mock_engine = MagicMock()
    mock_engine.connect.return_value = mock_conn

    with patch("conan.executor.create_engine", return_value=mock_engine):
        executor = Executor("postgresql://localhost/test")
        with pytest.raises(ExecutorError, match="table not found"):
            executor.execute("SELECT * FROM nonexistent")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_executor.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.executor'`

- [ ] **Step 3: Write executor.py**

```python
# conan/executor.py
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


class ExecutorError(Exception):
    pass


class Executor:
    def __init__(self, db_url: str):
        self.engine = create_engine(db_url)

    def execute(self, sql: str) -> list[dict]:
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(sql))
                return [dict(row._mapping) for row in result]
        except SQLAlchemyError as e:
            raise ExecutorError(str(e)) from e
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_executor.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add conan/executor.py tests/test_executor.py
git commit -m "feat: SQLAlchemy executor"
```

---

## Task 5: Bootstrap Mapper

**Files:**
- Create: `conan/bootstrap/mapper.py`
- Create: `tests/test_mapper.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_mapper.py
import pytest
from conan.models import SemanticLayer, KPIMaturity, KPITier, SourceTier
from conan.bootstrap.mapper import map_semantic_layer, map_from_project

SAMPLE_YAML = """
version: 2
semantic_models:
  - name: agg_daily_revenue
    description: Daily revenue aggregate
    model: ref('agg_daily_revenue')
    entities: []
    dimensions: []
    measures:
      - name: total_revenue
        agg: sum
        expr: amount
        description: Revenue
  - name: fct_orders
    description: Orders fact
    model: ref('fct_orders')
    entities: []
    dimensions: []
    measures:
      - name: order_count
        agg: count
        expr: order_id
        description: Order count
  - name: stg_public_orders
    description: Staging orders
    model: ref('stg_public_orders')
    entities: []
    dimensions: []
    measures: []
metrics:
  - name: monthly_revenue
    label: Monthly Revenue
    description: Revenue per month
    type: simple
    type_params:
      measure: total_revenue
  - name: total_orders
    label: Total Orders
    description: Count of orders
    type: simple
    type_params:
      measure: order_count
"""


@pytest.fixture
def sample_layer():
    return SemanticLayer.from_yaml_string(SAMPLE_YAML)


def test_mapper_creates_kpi_entry_per_metric(sample_layer):
    kb = map_semantic_layer(sample_layer, "test_project")
    assert len(kb.kpis) == 2
    assert any(k.metric == "monthly_revenue" for k in kb.kpis)
    assert any(k.metric == "total_orders" for k in kb.kpis)


def test_mapper_sets_directional_maturity_by_default(sample_layer):
    kb = map_semantic_layer(sample_layer, "test_project")
    assert all(k.maturity == KPIMaturity.directional for k in kb.kpis)


def test_mapper_sets_70_confidence_ceiling_by_default(sample_layer):
    kb = map_semantic_layer(sample_layer, "test_project")
    assert all(k.confidence_ceiling == 70 for k in kb.kpis)


def test_mapper_infers_revenue_domain(sample_layer):
    kb = map_semantic_layer(sample_layer, "test_project")
    rev_kpi = next(k for k in kb.kpis if k.metric == "monthly_revenue")
    assert rev_kpi.domain == "revenue"


def test_mapper_assigns_t1_to_gold_models(sample_layer):
    kb = map_semantic_layer(sample_layer, "test_project")
    gold = next(s for s in kb.sources if s.table_name == "agg_daily_revenue")
    assert gold.tier == SourceTier.t1


def test_mapper_assigns_t2_to_silver_models(sample_layer):
    kb = map_semantic_layer(sample_layer, "test_project")
    silver = next(s for s in kb.sources if s.table_name == "fct_orders")
    assert silver.tier == SourceTier.t2


def test_mapper_assigns_t3_to_bronze_models(sample_layer):
    kb = map_semantic_layer(sample_layer, "test_project")
    bronze = next(s for s in kb.sources if s.table_name == "stg_public_orders")
    assert bronze.tier == SourceTier.t3


def test_map_from_project_reads_semantic_layer_yml(tmp_path):
    (tmp_path / "semantic_layer.yml").write_text(SAMPLE_YAML)
    kb = map_from_project(tmp_path, "test_project")
    assert len(kb.kpis) == 2


def test_map_from_project_falls_back_to_semantic_models_yml(tmp_path):
    (tmp_path / "semantic_models.yml").write_text(SAMPLE_YAML)
    kb = map_from_project(tmp_path, "test_project")
    assert len(kb.kpis) == 2


def test_map_from_project_raises_if_no_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        map_from_project(tmp_path, "test_project")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_mapper.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.bootstrap.mapper'`

- [ ] **Step 3: Write mapper.py**

```python
# conan/bootstrap/mapper.py
from pathlib import Path
from conan.models import (
    SemanticLayer, KnowledgeBase, KPIEntry, TableSource,
    KPIMaturity, KPITier, SourceTier,
)

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "revenue": ["revenue", "sales", "mrr", "arr", "gmv", "income", "payment"],
    "users": ["user", "customer", "subscriber", "churn", "retention", "signup"],
    "operations": ["order", "transaction", "purchase", "fulfillment", "delivery"],
    "engagement": ["session", "visit", "engagement", "click", "conversion", "view"],
}


def _infer_domain(name: str) -> str:
    name_lower = name.lower()
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if any(k in name_lower for k in keywords):
            return domain
    return "general"


def _assign_source_tier(model_name: str) -> SourceTier:
    if model_name.startswith("agg_"):
        return SourceTier.t1
    if model_name.startswith(("fct_", "dim_")):
        return SourceTier.t2
    return SourceTier.t3


def _find_source_table(metric: object, layer: SemanticLayer) -> str:
    measure_name = metric.type_params.get("measure", "")
    for sm in layer.semantic_models:
        if any(m.name == measure_name for m in sm.measures):
            return sm.name
    return ""


def map_semantic_layer(layer: SemanticLayer, project_name: str) -> KnowledgeBase:
    domain_counters: dict[str, int] = {}
    kpis = []

    for metric in layer.metrics:
        domain = _infer_domain(metric.name)
        domain_counters[domain] = domain_counters.get(domain, 0) + 1
        prefix = domain[:3].upper()
        metric_id = f"{prefix}-{domain_counters[domain]:03d}"
        source_table = _find_source_table(metric, layer)

        kpis.append(KPIEntry(
            id=metric_id,
            metric=metric.name,
            domain=domain,
            tier=KPITier.l2,
            maturity=KPIMaturity.directional,
            confidence_ceiling=70,
            source_table=source_table,
            description=metric.description or metric.label,
        ))

    sources = [
        TableSource(
            table_name=sm.name,
            tier=_assign_source_tier(sm.name),
            description=sm.description,
        )
        for sm in layer.semantic_models
    ]

    return KnowledgeBase(project_name=project_name, kpis=kpis, sources=sources)


def map_from_project(project_path: Path, project_name: str) -> KnowledgeBase:
    for filename in ["semantic_layer.yml", "semantic_models.yml"]:
        p = project_path / filename
        if p.exists():
            return map_semantic_layer(SemanticLayer.from_yaml_file(p), project_name)
    raise FileNotFoundError(
        f"No semantic_layer.yml or semantic_models.yml found in {project_path}"
    )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_mapper.py -v
```

Expected: 10 passed.

- [ ] **Step 5: Commit**

```bash
git add conan/bootstrap/mapper.py tests/test_mapper.py
git commit -m "feat: bootstrap mapper — semantic layer to KB skeleton"
```

---

## Task 6: KB Writer

**Files:**
- Create: `conan/kb/writer.py`
- Create: `tests/test_kb_writer.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_kb_writer.py
import json
import pytest
from conan.models import KnowledgeBase, KPIEntry, TableSource, KPITier, KPIMaturity, SourceTier
from conan.kb.writer import write_kb, log_session


@pytest.fixture
def sample_kb():
    return KnowledgeBase(
        project_name="test",
        kpis=[
            KPIEntry(
                id="REV-001",
                metric="monthly_revenue",
                domain="revenue",
                tier=KPITier.l0,
                maturity=KPIMaturity.validated,
                confidence_ceiling=90,
                source_table="fct_orders",
                description="Monthly revenue from all orders",
                formula="SUM(amount)",
            )
        ],
        sources=[
            TableSource(table_name="agg_daily_revenue", tier=SourceTier.t1),
            TableSource(table_name="fct_orders", tier=SourceTier.t2),
            TableSource(table_name="stg_public_orders", tier=SourceTier.t3),
        ],
    )


def test_write_kb_creates_kpis_index(tmp_path, sample_kb):
    write_kb(sample_kb, tmp_path)
    content = (tmp_path / "kpis-index.md").read_text()
    assert "REV-001" in content
    assert "monthly_revenue" in content
    assert "revenue" in content


def test_write_kb_creates_domain_file(tmp_path, sample_kb):
    write_kb(sample_kb, tmp_path)
    assert (tmp_path / "kpis-revenue.md").exists()
    content = (tmp_path / "kpis-revenue.md").read_text()
    assert "REV-001" in content
    assert "SUM(amount)" in content


def test_write_kb_creates_source_priority(tmp_path, sample_kb):
    write_kb(sample_kb, tmp_path)
    content = (tmp_path / "source_priority.md").read_text()
    assert "agg_daily_revenue" in content
    assert "fct_orders" in content
    assert "T1" in content
    assert "T2" in content


def test_write_kb_creates_schema_tables(tmp_path, sample_kb):
    write_kb(sample_kb, tmp_path)
    content = (tmp_path / "schema" / "tables.md").read_text()
    assert "fct_orders" in content


def test_write_kb_creates_empty_queries_index(tmp_path, sample_kb):
    write_kb(sample_kb, tmp_path)
    index = json.loads((tmp_path / "queries" / "index.json").read_text())
    assert index == {"queries": []}


def test_write_kb_creates_sessions_directory(tmp_path, sample_kb):
    write_kb(sample_kb, tmp_path)
    assert (tmp_path / "sessions").is_dir()


def test_log_session_writes_file(tmp_path, sample_kb):
    write_kb(sample_kb, tmp_path)
    log_session(tmp_path, "what was revenue?", "Revenue was $100k")
    session_files = list((tmp_path / "sessions").glob("*.md"))
    assert len(session_files) == 1
    assert "what was revenue?" in session_files[0].read_text()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_kb_writer.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.kb.writer'`

- [ ] **Step 3: Write kb/writer.py**

```python
# conan/kb/writer.py
import json
import uuid
from datetime import datetime
from pathlib import Path
from conan.models import KnowledgeBase, SourceTier


def write_kb(kb: KnowledgeBase, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "schema").mkdir(exist_ok=True)
    (output_path / "queries").mkdir(exist_ok=True)
    (output_path / "sessions").mkdir(exist_ok=True)

    _write_kpis_index(kb, output_path)
    _write_domain_files(kb, output_path)
    _write_source_priority(kb, output_path)
    _write_schema_tables(kb, output_path)
    _init_queries_index(output_path)


def _write_kpis_index(kb: KnowledgeBase, path: Path) -> None:
    rows = [
        f"| {k.id} | {k.metric} | {k.domain} | {k.tier.value} | "
        f"{k.maturity.value} | {k.confidence_ceiling}% | {k.source_table} |"
        for k in kb.kpis
    ]
    content = (
        f"# KPI Index — {kb.project_name}\n\n"
        "| ID | Metric | Domain | Tier | Maturity | Confidence Ceiling | Source Table |\n"
        "|---|---|---|---|---|---|---|\n"
        + "\n".join(rows) + "\n"
    )
    (path / "kpis-index.md").write_text(content)


def _write_domain_files(kb: KnowledgeBase, path: Path) -> None:
    domains: dict[str, list] = {}
    for kpi in kb.kpis:
        domains.setdefault(kpi.domain, []).append(kpi)

    for domain, kpis in domains.items():
        lines = [f"# KPIs — {domain.title()}\n"]
        for kpi in kpis:
            lines += [
                f"\n## {kpi.id}: {kpi.metric}\n",
                f"**Tier:** {kpi.tier.value}  \n",
                f"**Maturity:** {kpi.maturity.value}  \n",
                f"**Confidence Ceiling:** {kpi.confidence_ceiling}%  \n",
                f"**Source Table:** {kpi.source_table}  \n",
                f"**Description:** {kpi.description}  \n",
                f"**Formula:** {kpi.formula}  \n",
                f"**Notes:** {kpi.notes}  \n",
            ]
        (path / f"kpis-{domain}.md").write_text("".join(lines))


def _write_source_priority(kb: KnowledgeBase, path: Path) -> None:
    t1 = [s.table_name for s in kb.sources if s.tier == SourceTier.t1]
    t2 = [s.table_name for s in kb.sources if s.tier == SourceTier.t2]
    t3 = [s.table_name for s in kb.sources if s.tier == SourceTier.t3]

    content = (
        "# Source Priority\n\n"
        "## Tier Mapping\n\n"
        f"### T1 — Gold Layer (Pre-aggregated)\nTables: {', '.join(t1) or 'none'}\n\n"
        f"### T2 — Silver Layer (Facts & Dimensions)\nTables: {', '.join(t2) or 'none'}\n\n"
        f"### T3 — Bronze Layer (Staging)\nTables: {', '.join(t3) or 'none'}\n\n"
        "## Routing Rules\n\n"
        "- Always prefer the highest available tier\n"
        "- T1 for metric lookups (pre-aggregated)\n"
        "- T2 for grain-level analysis\n"
        "- T3 for raw data only when T1/T2 lack coverage\n"
    )
    (path / "source_priority.md").write_text(content)


def _write_schema_tables(kb: KnowledgeBase, path: Path) -> None:
    rows = [
        f"| {s.table_name} | {s.tier.value} | {s.description} |"
        for s in kb.sources
    ]
    content = (
        "# Schema Tables\n\n"
        "| Table | Tier | Description |\n"
        "|---|---|---|\n"
        + "\n".join(rows) + "\n"
    )
    (path / "schema" / "tables.md").write_text(content)


def _init_queries_index(path: Path) -> None:
    index_path = path / "queries" / "index.json"
    if not index_path.exists():
        index_path.write_text(json.dumps({"queries": []}, indent=2))


def log_session(kb_path: str | Path, question: str, answer: str) -> None:
    session_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{session_id}.md"
    content = f"# Session {session_id}\n\n**Question:** {question}\n\n**Answer:**\n{answer}\n"
    (Path(kb_path) / "sessions" / filename).write_text(content)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_kb_writer.py -v
```

Expected: 7 passed.

- [ ] **Step 5: Commit**

```bash
git add conan/kb/writer.py tests/test_kb_writer.py
git commit -m "feat: KB writer — markdown files + session log"
```

---

## Task 7: KB Loader

**Files:**
- Create: `conan/kb/loader.py`
- Create: `tests/test_kb_loader.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write conftest.py and failing tests**

```python
# tests/conftest.py
import json
import pytest
from conan.models import (
    KnowledgeBase, KPIEntry, TableSource,
    KPITier, KPIMaturity, SourceTier,
)
from conan.kb.writer import write_kb


@pytest.fixture
def sample_kb():
    return KnowledgeBase(
        project_name="test",
        kpis=[
            KPIEntry(
                id="REV-001", metric="monthly_revenue", domain="revenue",
                tier=KPITier.l0, maturity=KPIMaturity.validated,
                confidence_ceiling=90, source_table="fct_orders",
                description="Monthly revenue", formula="SUM(amount)",
            ),
        ],
        sources=[
            TableSource(table_name="agg_daily_revenue", tier=SourceTier.t1),
            TableSource(table_name="fct_orders", tier=SourceTier.t2),
        ],
    )


@pytest.fixture
def kb_path(tmp_path, sample_kb):
    write_kb(sample_kb, tmp_path)
    return tmp_path
```

```python
# tests/test_kb_loader.py
import json
import pytest
from conan.kb.loader import KBLoader


def test_loader_reads_kpis_index(kb_path):
    loader = KBLoader(kb_path)
    content = loader.load_kpis_index()
    assert "REV-001" in content
    assert "monthly_revenue" in content


def test_loader_reads_source_priority(kb_path):
    loader = KBLoader(kb_path)
    content = loader.load_source_priority()
    assert "T1" in content
    assert "fct_orders" in content


def test_loader_reads_schema(kb_path):
    loader = KBLoader(kb_path)
    content = loader.load_schema()
    assert "fct_orders" in content


def test_loader_loads_domain_file(kb_path):
    loader = KBLoader(kb_path)
    content = loader.load_domain_file("revenue")
    assert content is not None
    assert "REV-001" in content


def test_loader_returns_none_for_missing_domain(kb_path):
    loader = KBLoader(kb_path)
    assert loader.load_domain_file("nonexistent") is None


def test_loader_load_for_skill_includes_core_context(kb_path):
    loader = KBLoader(kb_path)
    context = loader.load_for_skill("what was revenue last month?")
    assert "kpis_index" in context
    assert "source_priority" in context
    assert "schema" in context


def test_loader_load_for_skill_infers_revenue_domain(kb_path):
    loader = KBLoader(kb_path)
    context = loader.load_for_skill("what was revenue last month?")
    assert "kpi_domain" in context
    assert "REV-001" in context["kpi_domain"]


def test_loader_find_saved_query_returns_none_when_empty(kb_path):
    loader = KBLoader(kb_path)
    assert loader.find_saved_query("any question") is None


def test_loader_find_saved_query_matches_by_tag(kb_path):
    # Write a saved query with a tag
    import json
    index = {"queries": [{"id": "Q-001", "tags": ["revenue", "monthly"], "summary": "Monthly revenue"}]}
    (kb_path / "queries" / "index.json").write_text(json.dumps(index))
    (kb_path / "queries" / "Q-001.md").write_text("## Q-001\n\n```sql\nSELECT SUM(amount) FROM fct_orders\n```\n")
    
    loader = KBLoader(kb_path)
    result = loader.find_saved_query("what was revenue last month?")
    assert result is not None
    assert "SELECT SUM" in result
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_kb_loader.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.kb.loader'`

- [ ] **Step 3: Write kb/loader.py**

```python
# conan/kb/loader.py
import json
from pathlib import Path

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "revenue": ["revenue", "sales", "mrr", "arr", "gmv", "income", "payment"],
    "users": ["user", "customer", "subscriber", "churn", "retention"],
    "operations": ["order", "transaction", "purchase", "fulfillment"],
    "engagement": ["session", "visit", "engagement", "click", "conversion"],
}


class KBLoader:
    def __init__(self, kb_path: str | Path):
        self.kb_path = Path(kb_path)

    def load_kpis_index(self) -> str:
        return (self.kb_path / "kpis-index.md").read_text()

    def load_domain_file(self, domain: str) -> str | None:
        path = self.kb_path / f"kpis-{domain}.md"
        return path.read_text() if path.exists() else None

    def load_source_priority(self) -> str:
        return (self.kb_path / "source_priority.md").read_text()

    def load_schema(self) -> str:
        path = self.kb_path / "schema" / "tables.md"
        return path.read_text() if path.exists() else ""

    def find_saved_query(self, question: str) -> str | None:
        index_path = self.kb_path / "queries" / "index.json"
        if not index_path.exists():
            return None
        index = json.loads(index_path.read_text())
        question_lower = question.lower()
        for query in index.get("queries", []):
            if any(tag in question_lower for tag in query.get("tags", [])):
                query_file = self.kb_path / "queries" / f"{query['id']}.md"
                if query_file.exists():
                    return query_file.read_text()
        return None

    def load_for_skill(self, question: str) -> dict[str, str]:
        context: dict[str, str] = {
            "kpis_index": self.load_kpis_index(),
            "source_priority": self.load_source_priority(),
            "schema": self.load_schema(),
        }
        question_lower = question.lower()
        for domain, keywords in _DOMAIN_KEYWORDS.items():
            if any(k in question_lower for k in keywords):
                domain_content = self.load_domain_file(domain)
                if domain_content:
                    context["kpi_domain"] = domain_content
                break
        return context
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_kb_loader.py -v
```

Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add conan/kb/loader.py tests/conftest.py tests/test_kb_loader.py
git commit -m "feat: KB loader — context manifest loading for skills"
```

---

## Task 8: Bootstrap Enricher

**Files:**
- Create: `conan/bootstrap/enricher.py`
- Create: `tests/test_enricher.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_enricher.py
import pytest
from unittest.mock import patch
from conan.models import (
    KnowledgeBase, KPIEntry, TableSource, KPITier, KPIMaturity, SourceTier,
    EnrichmentSummary, EnrichmentResult,
)
from conan.bootstrap.enricher import enrich_kb


@pytest.fixture
def simple_kb():
    return KnowledgeBase(
        project_name="test",
        kpis=[
            KPIEntry(id="REV-001", metric="monthly_revenue", domain="revenue",
                     maturity=KPIMaturity.directional, confidence_ceiling=70,
                     source_table="fct_orders"),
        ],
        sources=[TableSource(table_name="fct_orders", tier=SourceTier.t2)],
    )


def test_enricher_promotes_metric_maturity(tmp_path, simple_kb):
    (tmp_path / "semantic_layer.yml").write_text("version: 2\nsemantic_models: []\nmetrics: []\n")

    mock_result = EnrichmentSummary(
        changes=[EnrichmentResult(
            metric_id="REV-001",
            tier=KPITier.l0,
            maturity=KPIMaturity.validated,
            confidence_ceiling=90,
            description="Total monthly revenue from all orders",
            formula="SUM(amount)",
        )],
        gaps=[],
    )

    with patch("conan.bootstrap.enricher.query_structured", return_value=mock_result), \
         patch("click.confirm", return_value=True):
        enriched = enrich_kb(simple_kb, tmp_path)

    rev = next(k for k in enriched.kpis if k.id == "REV-001")
    assert rev.maturity == KPIMaturity.validated
    assert rev.confidence_ceiling == 90
    assert rev.tier == KPITier.l0


def test_enricher_respects_user_rejection(tmp_path, simple_kb):
    (tmp_path / "semantic_layer.yml").write_text("version: 2\nsemantic_models: []\nmetrics: []\n")

    mock_result = EnrichmentSummary(
        changes=[EnrichmentResult(
            metric_id="REV-001",
            tier=KPITier.l0,
            maturity=KPIMaturity.validated,
            confidence_ceiling=90,
            description="Updated description",
        )],
        gaps=[],
    )

    with patch("conan.bootstrap.enricher.query_structured", return_value=mock_result), \
         patch("click.confirm", return_value=False):
        enriched = enrich_kb(simple_kb, tmp_path)

    # Changes not applied — maturity stays directional
    rev = next(k for k in enriched.kpis if k.id == "REV-001")
    assert rev.maturity == KPIMaturity.directional
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_enricher.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.bootstrap.enricher'`

- [ ] **Step 3: Write bootstrap/enricher.py**

```python
# conan/bootstrap/enricher.py
from pathlib import Path
import click
from conan.models import (
    KnowledgeBase, KPIEntry, EnrichmentSummary, EnrichmentResult,
)
from conan.llm import query_structured

_BATCH_SIZE = 5

_SYSTEM = """You are a data analyst reviewing an auto-generated KPI catalog.
Given KPI stubs and the original semantic layer context, validate and improve them:
- Promote obvious north-star/core metrics (revenue, DAU, MRR) to Validated maturity
- Assign L0 for north-star, L1 for core operational, L2 for supporting, L3 for diagnostic
- Set confidence_ceiling: Validated=85-95, Directional=60-75, Proposed=50
- Write a clear 1-2 sentence description
- Add formula if derivable from the semantic layer
- Mark metrics with no source table as Proposed
Return structured changes for every metric ID provided."""


def enrich_kb(kb: KnowledgeBase, project_path: Path) -> KnowledgeBase:
    semantic_context = _read_semantic_context(project_path)

    domains: dict[str, list[KPIEntry]] = {}
    for kpi in kb.kpis:
        domains.setdefault(kpi.domain, []).append(kpi)

    all_changes: list[EnrichmentResult] = []
    all_gaps: list[str] = []

    for domain_kpis in domains.values():
        for i in range(0, len(domain_kpis), _BATCH_SIZE):
            batch = domain_kpis[i:i + _BATCH_SIZE]
            result = _enrich_batch(batch, semantic_context)
            all_changes.extend(result.changes)
            all_gaps.extend(result.gaps)

    _print_summary(all_changes, all_gaps)
    if not click.confirm("Apply these changes?", default=True):
        return kb

    changes_by_id = {c.metric_id: c for c in all_changes}
    updated_kpis = []
    for kpi in kb.kpis:
        if kpi.id in changes_by_id:
            c = changes_by_id[kpi.id]
            updated_kpis.append(kpi.model_copy(update={
                "tier": c.tier,
                "maturity": c.maturity,
                "confidence_ceiling": c.confidence_ceiling,
                "description": c.description,
                "formula": c.formula,
                "notes": c.notes,
            }))
        else:
            updated_kpis.append(kpi)

    return kb.model_copy(update={"kpis": updated_kpis})


def _read_semantic_context(project_path: Path) -> str:
    for filename in ["semantic_layer.yml", "semantic_models.yml"]:
        p = project_path / filename
        if p.exists():
            return p.read_text()[:4000]
    return ""


def _enrich_batch(kpis: list[KPIEntry], semantic_context: str) -> EnrichmentSummary:
    stubs = "\n".join(
        f"- ID: {k.id}, Metric: {k.metric}, Domain: {k.domain}, "
        f"Source: {k.source_table or 'MISSING'}, Description: {k.description}"
        for k in kpis
    )
    return query_structured(
        system=_SYSTEM,
        user=f"KPI stubs:\n{stubs}\n\nSemantic layer:\n{semantic_context}",
        response_model=EnrichmentSummary,
        max_tokens=2048,
    )


def _print_summary(changes: list[EnrichmentResult], gaps: list[str]) -> None:
    click.echo(f"\nEnrichment: {len(changes)} changes, {len(gaps)} gaps flagged")
    for c in changes:
        click.echo(f"  {c.metric_id}: {c.maturity.value} / {c.tier.value} / {c.confidence_ceiling}% ceiling")
    for g in gaps:
        click.echo(f"  GAP: {g}")
    click.echo()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_enricher.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add conan/bootstrap/enricher.py tests/test_enricher.py
git commit -m "feat: bootstrap enricher — LLM validation pass on KB stubs"
```

---

## Task 9: Skill Base + Data Queries Skill

**Files:**
- Create: `conan/skills/base.py`
- Create: `conan/skills/data_queries.py`
- Create: `tests/test_data_queries.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_data_queries.py
import re
import pytest
from unittest.mock import patch, MagicMock
from conan.models import (
    SQLGenerationResult, AnalysisResult, OrchestratorDispatch, SourceTier,
)
from conan.skills.data_queries import DataQueriesSkill


@pytest.fixture
def skill(kb_path):
    return DataQueriesSkill(kb_path, "postgresql://localhost/test")


@pytest.fixture
def dispatch():
    return OrchestratorDispatch(skill="data-queries", reasoning="metric lookup")


def test_data_queries_generates_sql_and_returns_answer(skill, dispatch):
    mock_sql = SQLGenerationResult(
        sql="SELECT SUM(amount) AS revenue FROM fct_orders",
        source_table="fct_orders",
        source_tier=SourceTier.t2,
        reasoning="Using fct_orders T2",
    )
    mock_analysis = AnalysisResult(
        answer="Revenue last month was $142,340",
        confidence=80,
        confidence_justification="validated metric, T2 source",
    )

    with patch("conan.skills.data_queries.query_structured", side_effect=[mock_sql, mock_analysis]), \
         patch.object(skill.executor, "execute", return_value=[{"revenue": 142340}]):
        result = skill.run("what was revenue last month?", dispatch)

    assert "142,340" in result.answer
    assert result.confidence == 80
    assert result.sql == "SELECT SUM(amount) AS revenue FROM fct_orders"
    assert result.source_tier == SourceTier.t2


def test_data_queries_uses_saved_query_when_available(skill, dispatch, kb_path):
    import json
    index = {"queries": [{"id": "Q-001", "tags": ["revenue"], "summary": "Revenue"}]}
    (kb_path / "queries" / "index.json").write_text(json.dumps(index))
    (kb_path / "queries" / "Q-001.md").write_text(
        "## Q-001\n\n```sql\nSELECT SUM(amount) FROM fct_orders\n```\n"
    )

    mock_analysis = AnalysisResult(
        answer="Revenue was $142,340",
        confidence=85,
        confidence_justification="saved query",
    )

    with patch("conan.skills.data_queries.query_structured", return_value=mock_analysis), \
         patch.object(skill.executor, "execute", return_value=[{"revenue": 142340}]):
        result = skill.run("what was revenue?", dispatch)

    assert result.source_tier == SourceTier.t1  # saved queries are T1-equivalent
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_data_queries.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.skills.base'`

- [ ] **Step 3: Write skills/base.py**

```python
# conan/skills/base.py
import os
from abc import ABC, abstractmethod
from pathlib import Path
from conan.executor import Executor
from conan.kb.loader import KBLoader
from conan.models import SkillResult, OrchestratorDispatch


class SkillBase(ABC):
    name: str
    description: str

    def __init__(self, kb_path: str | Path, db_url: str, model: str | None = None):
        self.kb_loader = KBLoader(kb_path)
        self.executor = Executor(db_url)
        self.model = model or os.getenv("CONAN_SKILL_MODEL", "gemma4:e4b")

    @abstractmethod
    def run(self, question: str, dispatch: OrchestratorDispatch) -> SkillResult:
        pass
```

- [ ] **Step 4: Write skills/data_queries.py**

```python
# conan/skills/data_queries.py
import re
from conan.skills.base import SkillBase
from conan.models import (
    SQLGenerationResult, AnalysisResult, SkillResult, OrchestratorDispatch, SourceTier,
)
from conan.llm import query_structured

_SYSTEM_SQL = (
    "You are a data analyst. Given a question and database context (KPI catalog, "
    "source priority, schema), generate a single SQL query to answer it. "
    "Use only tables and columns that exist in the schema docs. "
    "Prefer T1 (Gold) tables for aggregated metrics, T2 (Silver) for grain-level. "
    "Return structured output."
)

_SYSTEM_ANALYZE = (
    "You are a data analyst. Given a question, the SQL run, and the result set, "
    "provide a clear answer in plain English. Score confidence: start at 50, "
    "+20 if metric in KPI catalog, +20 if T1 source (+10 if T2), "
    "+20 if SQL follows catalog pattern, +15 for live data, +15 for direct lookup. "
    "Cap at the metric's confidence_ceiling from the KPI catalog."
)


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
        domain_section = f"\nDomain KPIs:\n{context['kpi_domain']}" if "kpi_domain" in context else ""
        user = (
            f"Question: {question}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}\n\n"
            f"Source Priority:\n{context.get('source_priority', '')}\n\n"
            f"Schema:\n{context.get('schema', '')}"
            f"{domain_section}"
        )
        return query_structured(_SYSTEM_SQL, user, SQLGenerationResult, model=self.model, max_tokens=512)

    def _analyze(self, question: str, sql_result: SQLGenerationResult, rows: list[dict], context: dict) -> AnalysisResult:
        user = (
            f"Question: {question}\n\n"
            f"SQL: {sql_result.sql}\n"
            f"Source: {sql_result.source_table} ({sql_result.source_tier.value})\n\n"
            f"Result (first 20 rows):\n{rows[:20]}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}"
        )
        return query_structured(_SYSTEM_ANALYZE, user, AnalysisResult, model=self.model, max_tokens=512)


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

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_data_queries.py -v
```

Expected: 2 passed.

- [ ] **Step 6: Commit**

```bash
git add conan/skills/base.py conan/skills/data_queries.py tests/test_data_queries.py
git commit -m "feat: SkillBase + data-queries skill"
```

---

## Task 10: Product Analyst Skill

**Files:**
- Create: `conan/skills/product_analyst.py`
- Create: `tests/test_product_analyst.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_product_analyst.py
import pytest
from unittest.mock import patch
from conan.models import (
    DiagnosticQueries, SQLGenerationResult, AnalysisResult,
    OrchestratorDispatch, SourceTier,
)
from conan.skills.product_analyst import ProductAnalystSkill


@pytest.fixture
def skill(kb_path):
    return ProductAnalystSkill(kb_path, "postgresql://localhost/test")


@pytest.fixture
def dispatch():
    return OrchestratorDispatch(skill="product-analyst", reasoning="root cause question")


def test_product_analyst_decomposes_into_diagnostic_queries(skill, dispatch):
    mock_diagnostic = DiagnosticQueries(
        queries=[
            SQLGenerationResult(
                sql="SELECT date_trunc('week', order_date), SUM(amount) FROM fct_orders GROUP BY 1",
                source_table="fct_orders",
                source_tier=SourceTier.t2,
                reasoning="Check revenue trend",
            ),
            SQLGenerationResult(
                sql="SELECT region, SUM(amount) FROM fct_orders WHERE order_date >= '2026-04-01' GROUP BY 1",
                source_table="fct_orders",
                source_tier=SourceTier.t2,
                reasoning="Check by region",
            ),
        ],
        reasoning="Decomposing revenue drop into trend + regional analysis",
    )
    mock_analysis = AnalysisResult(
        answer="Revenue dropped 12% primarily in the EMEA region due to fewer orders in April.",
        confidence=72,
        confidence_justification="T2 source, multiple queries, directional",
    )

    with patch("conan.skills.product_analyst.query_structured", side_effect=[mock_diagnostic, mock_analysis]), \
         patch.object(skill.executor, "execute", return_value=[{"revenue": 100}]):
        result = skill.run("why did revenue drop last month?", dispatch)

    assert "EMEA" in result.answer
    assert result.confidence == 72
    assert result.sql is not None


def test_product_analyst_handles_failed_sub_query(skill, dispatch):
    from conan.executor import ExecutorError
    mock_diagnostic = DiagnosticQueries(
        queries=[
            SQLGenerationResult(
                sql="SELECT SUM(amount) FROM nonexistent_table",
                source_table="nonexistent_table",
                source_tier=SourceTier.t3,
                reasoning="Try raw data",
            ),
        ],
        reasoning="Try raw data",
    )
    mock_analysis = AnalysisResult(
        answer="Could not fully diagnose — one query failed.",
        confidence=40,
        confidence_justification="query execution error",
    )

    with patch("conan.skills.product_analyst.query_structured", side_effect=[mock_diagnostic, mock_analysis]), \
         patch.object(skill.executor, "execute", side_effect=ExecutorError("table not found")):
        result = skill.run("why did revenue drop?", dispatch)

    assert result.confidence == 40
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_product_analyst.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.skills.product_analyst'`

- [ ] **Step 3: Write skills/product_analyst.py**

```python
# conan/skills/product_analyst.py
from conan.skills.base import SkillBase
from conan.models import (
    DiagnosticQueries, AnalysisResult, SkillResult, OrchestratorDispatch,
)
from conan.executor import ExecutorError
from conan.llm import query_structured

_SYSTEM_DECOMPOSE = (
    "You are a product analyst. Given a question about why a metric changed or what "
    "caused an anomaly, generate 2-3 diagnostic SQL queries that explore different "
    "potential causes (time trend, segmentation, funnel, etc.). "
    "Use only tables and columns from the schema docs. Return structured output."
)

_SYSTEM_SYNTHESIZE = (
    "You are a product analyst. Given a root cause question and results from "
    "multiple diagnostic queries, synthesise a clear root cause analysis. "
    "Be specific about what the data shows. "
    "Score confidence: start at 50, +20 if T1/T2 source, +20 if metrics in catalog, "
    "+15 for live data, +5 per successful diagnostic query. Cap at 85."
)


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
        return query_structured(_SYSTEM_DECOMPOSE, user, DiagnosticQueries, model=self.model, max_tokens=1024)

    def _synthesize(self, question: str, results: list[dict], context: dict) -> AnalysisResult:
        user = (
            f"Question: {question}\n\n"
            f"Diagnostic results:\n{results}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}"
        )
        return query_structured(_SYSTEM_SYNTHESIZE, user, AnalysisResult, model=self.model, max_tokens=512)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_product_analyst.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add conan/skills/product_analyst.py tests/test_product_analyst.py
git commit -m "feat: product-analyst skill — root cause analysis"
```

---

## Task 11: Orchestrator

**Files:**
- Create: `conan/orchestrator.py`
- Create: `tests/test_orchestrator.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_orchestrator.py
import pytest
from unittest.mock import patch, MagicMock
from conan.models import OrchestratorDispatch, SkillResult, SourceTier
from conan.orchestrator import Orchestrator


@pytest.fixture
def orch(kb_path):
    return Orchestrator(kb_path, "postgresql://localhost/test")


def test_orchestrator_dispatches_to_data_queries(orch):
    mock_dispatch = OrchestratorDispatch(skill="data-queries", reasoning="metric lookup")
    mock_result = SkillResult(
        answer="Revenue was $142,340",
        sql="SELECT SUM(amount) FROM fct_orders",
        source_table="fct_orders",
        source_tier=SourceTier.t2,
        confidence=80,
        confidence_justification="T2 source, metric in catalog",
    )

    with patch("conan.orchestrator.query_structured", return_value=mock_dispatch), \
         patch.object(orch.skills["data-queries"], "run", return_value=mock_result):
        answer = orch.run("what was revenue last month?")

    assert "Revenue was $142,340" in answer
    assert "80%" in answer
    assert "fct_orders" in answer


def test_orchestrator_dispatches_to_product_analyst(orch):
    mock_dispatch = OrchestratorDispatch(skill="product-analyst", reasoning="why question")
    mock_result = SkillResult(
        answer="Revenue dropped due to EMEA slowdown",
        confidence=72,
        confidence_justification="T2 source, directional",
    )

    with patch("conan.orchestrator.query_structured", return_value=mock_dispatch), \
         patch.object(orch.skills["product-analyst"], "run", return_value=mock_result):
        answer = orch.run("why did revenue drop?")

    assert "EMEA" in answer
    assert "72%" in answer


def test_orchestrator_falls_back_to_data_queries_for_unknown_skill(orch):
    mock_dispatch = OrchestratorDispatch(skill="unknown-skill", reasoning="unknown")
    mock_result = SkillResult(
        answer="Some answer",
        confidence=60,
        confidence_justification="fallback",
    )

    with patch("conan.orchestrator.query_structured", return_value=mock_dispatch), \
         patch.object(orch.skills["data-queries"], "run", return_value=mock_result):
        answer = orch.run("some question")

    assert "Some answer" in answer


def test_orchestrator_formats_answer_with_source_and_confidence(orch):
    mock_dispatch = OrchestratorDispatch(skill="data-queries", reasoning="lookup")
    mock_result = SkillResult(
        answer="Revenue was $100k",
        sql="SELECT SUM(amount) FROM fct_orders",
        source_table="fct_orders",
        source_tier=SourceTier.t2,
        confidence=84,
        confidence_justification="validated metric, T2 source",
    )

    with patch("conan.orchestrator.query_structured", return_value=mock_dispatch), \
         patch.object(orch.skills["data-queries"], "run", return_value=mock_result):
        answer = orch.run("revenue?")

    assert "── Answer" in answer
    assert "Source: fct_orders" in answer
    assert "Confidence: 84%" in answer
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.orchestrator'`

- [ ] **Step 3: Write orchestrator.py**

```python
# conan/orchestrator.py
import os
from pathlib import Path
from conan.models import OrchestratorDispatch, SkillResult
from conan.llm import query_structured
from conan.skills.data_queries import DataQueriesSkill
from conan.skills.product_analyst import ProductAnalystSkill

_SYSTEM_DISPATCH = (
    "You are an analytics orchestrator. Classify the user question and pick a skill:\n"
    "- 'data-queries': metric values, trends, breakdowns, comparisons, 'what is X'\n"
    "- 'product-analyst': root cause, anomaly, 'why did X change', 'explain the drop'\n"
    "Return the skill name and a one-line reasoning."
)


class Orchestrator:
    def __init__(self, kb_path: str | Path, db_url: str, model: str | None = None):
        self.kb_path = Path(kb_path)
        self.db_url = db_url
        self.model = model or os.getenv("CONAN_ORCHESTRATOR_MODEL", "gemma4:e4b")
        self.skills = {
            "data-queries": DataQueriesSkill(kb_path, db_url),
            "product-analyst": ProductAnalystSkill(kb_path, db_url),
        }

    def run(self, question: str) -> str:
        dispatch = self._dispatch(question)
        skill = self.skills.get(dispatch.skill, self.skills["data-queries"])
        result = skill.run(question, dispatch)
        return self._format_answer(result)

    def _dispatch(self, question: str) -> OrchestratorDispatch:
        return query_structured(
            _SYSTEM_DISPATCH, question, OrchestratorDispatch,
            model=self.model, max_tokens=128,
        )

    def _format_answer(self, result: SkillResult) -> str:
        tier = result.source_tier.value if result.source_tier else "N/A"
        source_line = f"Source: {result.source_table or 'N/A'}  |  {tier}" if result.source_table else ""
        return (
            f"\n── Answer {'─' * 44}\n"
            f"{result.answer}\n\n"
            + (f"{source_line}\n" if source_line else "")
            + f"Confidence: {result.confidence}% — {result.confidence_justification}\n"
            f"{'─' * 52}\n"
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_orchestrator.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add conan/orchestrator.py tests/test_orchestrator.py
git commit -m "feat: orchestrator — LLM dispatch + answer synthesis"
```

---

## Task 12: CLI

**Files:**
- Create: `conan/cli.py`
- Create: `tests/test_cli.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_cli.py
import pytest
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from conan.cli import main


def test_bootstrap_command_exits_zero(tmp_path):
    runner = CliRunner()
    mock_kb = MagicMock()
    mock_kb.kpis = []
    mock_kb.sources = []

    with patch("conan.cli.map_from_project", return_value=mock_kb), \
         patch("conan.cli.enrich_kb", return_value=mock_kb), \
         patch("conan.cli.write_kb"):
        result = runner.invoke(main, [
            "bootstrap",
            "-p", str(tmp_path),
            "-c", "postgresql://localhost/test",
            "-o", str(tmp_path / "conan_kb"),
        ])

    assert result.exit_code == 0


def test_bootstrap_command_requires_project_path():
    runner = CliRunner()
    result = runner.invoke(main, ["bootstrap", "-c", "postgresql://localhost/test", "-o", "/tmp/kb"])
    assert result.exit_code != 0
    assert "Missing option" in result.output


def test_chat_command_runs_one_question_and_exits(tmp_path, kb_path):
    runner = CliRunner()
    mock_orch = MagicMock()
    mock_orch.run.return_value = "\n── Answer ─\nRevenue was $100k\nConfidence: 80%\n"

    with patch("conan.cli.Orchestrator", return_value=mock_orch), \
         patch("conan.cli.log_session"):
        result = runner.invoke(
            main,
            ["chat", "-p", str(kb_path), "-c", "postgresql://localhost/test"],
            input="what was revenue?\n\x03",  # question then Ctrl+C
        )

    assert mock_orch.run.called
    assert result.exit_code == 0
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_cli.py -v
```

Expected: `ModuleNotFoundError: No module named 'conan.cli'`

- [ ] **Step 3: Write cli.py**

```python
# conan/cli.py
import click
from pathlib import Path


@click.group()
def main():
    """ConAn — AI analytics partner for your Schemalytics project."""
    pass


@main.command()
@click.option("-p", "--project", required=True, type=click.Path(exists=True),
              help="Path to Schemalytics dbt project")
@click.option("-c", "--connection", required=True, help="PostgreSQL connection string")
@click.option("-o", "--output", required=True, type=click.Path(),
              help="Output path for ConAn knowledge base")
@click.option("--name", default=None, help="Project name (defaults to output directory name)")
def bootstrap(project, connection, output, name):
    """Bootstrap ConAn knowledge base from a Schemalytics dbt project."""
    from conan.bootstrap.mapper import map_from_project
    from conan.bootstrap.enricher import enrich_kb
    from conan.kb.writer import write_kb

    project_path = Path(project)
    output_path = Path(output)
    project_name = name or output_path.name

    click.echo(f"Reading Schemalytics output from {project_path}...")
    kb = map_from_project(project_path, project_name)
    click.echo(f"Mapped {len(kb.kpis)} metrics, {len(kb.sources)} tables.")

    click.echo("Running LLM enrichment pass...")
    kb = enrich_kb(kb, project_path)

    output_path.mkdir(parents=True, exist_ok=True)
    write_kb(kb, output_path)
    click.echo(f"Knowledge base written to {output_path}")


@main.command()
@click.option("-p", "--kb-path", required=True, type=click.Path(exists=True),
              help="Path to ConAn knowledge base")
@click.option("-c", "--connection", required=True, help="PostgreSQL connection string")
def chat(kb_path, connection):
    """Start an interactive chat session with your data."""
    from conan.orchestrator import Orchestrator
    from conan.kb.writer import log_session

    orch = Orchestrator(kb_path, connection)
    click.echo("ConAn ready. Type your question (Ctrl+C to exit).\n")

    while True:
        try:
            question = click.prompt("You")
            if not question.strip():
                continue
            answer = orch.run(question)
            click.echo(answer)
            log_session(kb_path, question, answer)
        except (KeyboardInterrupt, click.exceptions.Abort):
            click.echo("\nBye.")
            break
```

- [ ] **Step 4: Run all tests to verify everything passes**

```bash
pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 5: Smoke test CLI help**

```bash
conan --help
conan bootstrap --help
conan chat --help
```

Expected: Help text prints for all three, no errors.

- [ ] **Step 6: Final commit**

```bash
git add conan/cli.py tests/test_cli.py
git commit -m "feat: CLI — bootstrap and chat commands"
```

---

## Final Verification

- [ ] **Run full test suite**

```bash
pytest tests/ -v --tb=short
```

Expected: All tests pass, 0 failures.

- [ ] **Verify package installs and CLI entrypoint works**

```bash
pip install -e ".[dev]" && conan --help
```

Expected: `Usage: conan [OPTIONS] COMMAND [ARGS]...`
