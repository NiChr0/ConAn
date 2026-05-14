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
                sql="SELECT date_trunc('week', order_date), SUM(amount) FROM fct_orders GROUP BY 1",
                source_table="fct_orders",
                source_tier=SourceTier.t2,
                reasoning="Check revenue trend",
            ),
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

    execute_calls = {"n": 0}

    def execute_side_effect(sql):
        execute_calls["n"] += 1
        if execute_calls["n"] == 1:
            return [{"revenue": 100}]
        raise ExecutorError("table not found")

    with patch("conan.skills.product_analyst.query_structured", side_effect=[mock_diagnostic, mock_analysis]), \
         patch.object(skill.executor, "execute", side_effect=execute_side_effect):
        result = skill.run("why did revenue drop?", dispatch)

    assert result.confidence == 40


def test_product_analyst_returns_early_when_all_queries_fail(skill, dispatch):
    """When every diagnostic query fails, return a SkillResult without calling synthesize."""
    from conan.executor import ExecutorError
    mock_diagnostic = DiagnosticQueries(
        queries=[
            SQLGenerationResult(
                sql="SELECT SUM(amount) FROM nonexistent_a",
                source_table="nonexistent_a",
                source_tier=SourceTier.t3,
                reasoning="Try source A",
            ),
            SQLGenerationResult(
                sql="SELECT SUM(amount) FROM nonexistent_b",
                source_table="nonexistent_b",
                source_tier=SourceTier.t3,
                reasoning="Try source B",
            ),
        ],
        reasoning="Diagnostic attempt",
    )

    call_count = {"n": 0}

    def side_effect(system, user, model_cls, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return mock_diagnostic
        raise AssertionError("synthesize should not be called when all queries fail")

    with patch("conan.skills.product_analyst.query_structured", side_effect=side_effect), \
         patch.object(skill.executor, "execute", side_effect=ExecutorError("table not found")):
        result = skill.run("why did revenue drop?", dispatch)

    assert result.confidence <= 30
    assert "not" in result.answer.lower() or "unavailable" in result.answer.lower() or "failed" in result.answer.lower()
