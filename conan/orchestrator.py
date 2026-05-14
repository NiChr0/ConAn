# conan/orchestrator.py
import os
from pathlib import Path
from conan.models import OrchestratorDispatch, SkillResult
from conan.llm import query_structured
from conan.skills.data_queries import DataQueriesSkill
from conan.skills.product_analyst import ProductAnalystSkill

_SYSTEM_DISPATCH = (
    "You are an analytics orchestrator. Classify the user question and pick a skill:\n"
    "- 'data-queries': metric values, trends, breakdowns, comparisons, 'what is X'\n"
    "- 'product-analyst': root cause, anomaly, 'why did X change', 'explain the drop'\n"
    "Return the skill name and a one-line reasoning."
)


class Orchestrator:
    def __init__(self, kb_path: str | Path, db_url: str, model: str | None = None):
        self.kb_path = Path(kb_path)
        self.db_url = db_url
        self.model = model or os.getenv("CONAN_ORCHESTRATOR_MODEL", "gemma4:e4b")
        self.skills = {
            "data-queries": DataQueriesSkill(kb_path, db_url),
            "product-analyst": ProductAnalystSkill(kb_path, db_url),
        }

    def run(self, question: str) -> str:
        dispatch = self._dispatch(question)
        skill = self.skills.get(dispatch.skill, self.skills["data-queries"])
        result = skill.run(question, dispatch)
        return self._format_answer(result)

    def _dispatch(self, question: str) -> OrchestratorDispatch:
        return query_structured(
            _SYSTEM_DISPATCH, question, OrchestratorDispatch,
            model=self.model, max_tokens=128,
        )

    def _format_answer(self, result: SkillResult) -> str:
        tier = result.source_tier.value if result.source_tier else "N/A"
        source_line = f"Source: {result.source_table or 'N/A'}  |  {tier}" if result.source_table else ""
        return (
            f"\n── Answer {'─' * 44}\n"
            f"{result.answer}\n\n"
            + (f"{source_line}\n" if source_line else "")
            + f"Confidence: {result.confidence}% — {result.confidence_justification}\n"
            f"{'─' * 52}\n"
        )
