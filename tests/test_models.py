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
