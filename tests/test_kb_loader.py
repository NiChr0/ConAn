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
    index = {"queries": [{"id": "Q-001", "tags": ["revenue", "monthly"], "summary": "Monthly revenue"}]}
    (kb_path / "queries" / "index.json").write_text(json.dumps(index))
    (kb_path / "queries" / "Q-001.md").write_text("## Q-001\n\n```sql\nSELECT SUM(amount) FROM fct_orders\n```\n")

    loader = KBLoader(kb_path)
    result = loader.find_saved_query("what was revenue last month?")
    assert result is not None
    assert "SELECT SUM" in result
