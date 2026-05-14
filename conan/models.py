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
