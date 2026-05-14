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
