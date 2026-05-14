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
