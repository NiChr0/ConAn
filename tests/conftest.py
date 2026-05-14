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
