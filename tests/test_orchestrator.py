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
    mock_dispatch = MagicMock()
    mock_dispatch.skill = "unknown-skill"
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
