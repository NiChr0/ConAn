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
