# conan/skills/data_queries.py
import re
from pathlib import Path
from conan.skills.base import SkillBase
from conan.models import (
    SQLGenerationResult, AnalysisResult, SkillResult, OrchestratorDispatch, SourceTier,
)
from conan.llm import query_structured

_SKILL_DIR = Path(__file__).parent / "data-analyst"
_SYSTEM_SQL     = (_SKILL_DIR / "sql.md").read_text()
_SYSTEM_ANALYZE = (_SKILL_DIR / "analysis.md").read_text()
_EDGE_CASES     = (_SKILL_DIR / "references" / "edge-cases.md").read_text()
_CONF_GUIDE     = (_SKILL_DIR / "references" / "confidence-guide.md").read_text()

_PREAGG_PATTERN = re.compile(r"\bavg_\w+|\bagg_\w+", re.IGNORECASE)


class DataQueriesSkill(SkillBase):
    name = "data-queries"
    description = "Metric lookups, time-series, breakdowns, comparisons"

    def run(self, question: str, dispatch: OrchestratorDispatch) -> SkillResult:
        context = self.kb_loader.load_for_skill(question)
        saved = self.kb_loader.find_saved_query(question)

        if saved:
            sql_result = _sql_from_saved(saved)
        else:
            sql_result = self._generate_sql(question, context)

        rows = self.executor.execute(sql_result.sql)
        analysis = self._analyze(question, sql_result, rows, context)

        return SkillResult(
            answer=analysis.answer,
            sql=sql_result.sql,
            source_table=sql_result.source_table,
            source_tier=sql_result.source_tier,
            confidence=analysis.confidence,
            confidence_justification=analysis.confidence_justification,
        )

    def _generate_sql(self, question: str, context: dict) -> SQLGenerationResult:
        schema = context.get("schema", "")
        domain_section = f"\nDomain KPIs:\n{context['kpi_domain']}" if "kpi_domain" in context else ""
        edge_cases_section = f"\n\n---\n\n{_EDGE_CASES}" if _PREAGG_PATTERN.search(schema) else ""
        user = (
            f"Question: {question}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}\n\n"
            f"Source Priority:\n{context.get('source_priority', '')}\n\n"
            f"Schema:\n{schema}"
            f"{domain_section}"
            f"{edge_cases_section}"
        )
        return query_structured(_SYSTEM_SQL, user, SQLGenerationResult, model=self.model, max_tokens=4096)

    def _analyze(self, question: str, sql_result: SQLGenerationResult, rows: list[dict], context: dict) -> AnalysisResult:
        user = (
            f"Question: {question}\n\n"
            f"SQL: {sql_result.sql}\n"
            f"Source: {sql_result.source_table} ({sql_result.source_tier.value})\n\n"
            f"Result (first 20 rows):\n{rows[:20]}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}\n\n"
            f"---\n\n{_CONF_GUIDE}"
        )
        return query_structured(_SYSTEM_ANALYZE, user, AnalysisResult, model=self.model, max_tokens=4096)


def _sql_from_saved(saved_content: str) -> SQLGenerationResult:
    match = re.search(r"```sql\n(.*?)```", saved_content, re.DOTALL)
    sql = match.group(1).strip() if match else saved_content
    return SQLGenerationResult(
        sql=sql,
        source_table="saved_query",
        source_tier=SourceTier.t1,
        reasoning="Using saved (vetted) query",
    )
