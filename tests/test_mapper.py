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
