# conan/skills/data_queries.py
import re
from conan.skills.base import SkillBase
from conan.models import (
    SQLGenerationResult, AnalysisResult, SkillResult, OrchestratorDispatch, SourceTier,
)
from conan.llm import query_structured

_SYSTEM_SQL = (
    "You are a senior data analyst with access to a DuckDB database. "
    "Write a single SQL query to answer the question using only the tables and columns "
    "listed in the Schema — no other tables or columns exist. "
    "Select the table whose granularity matches the question (daily tables for daily "
    "questions, monthly tables for monthly questions). "
    "Prefer T1 (Gold) tables. Return structured output."
)

_SYSTEM_ANALYZE = (
    "You are a data analyst. Answer the question based on the SQL result using this exact structure:\n"
    "1. One sentence stating the key figure and what it means.\n"
    "2. A markdown table of the result data. If the result is empty or null, write "
    "'No data available for this period' and explain the likely reason (e.g. the dataset "
    "predates the requested date range).\n"
    "3. Confidence: [score]% — [one-line justification].\n\n"
    "Confidence: start at 50. +20 if metric is in the KPI catalog. +20 if T1 source, "
    "+10 if T2. +20 if SQL matches the catalog pattern. +15 if result has data rows. "
    "-30 if result is empty or null. Cap at the metric's confidence_ceiling. "
    "Never score above 60 for an empty or null result."
)


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
        domain_section = f"\nDomain KPIs:\n{context['kpi_domain']}" if "kpi_domain" in context else ""
        user = (
            f"Question: {question}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}\n\n"
            f"Source Priority:\n{context.get('source_priority', '')}\n\n"
            f"Schema:\n{context.get('schema', '')}"
            f"{domain_section}"
        )
        return query_structured(_SYSTEM_SQL, user, SQLGenerationResult, model=self.model, max_tokens=4096)

    def _analyze(self, question: str, sql_result: SQLGenerationResult, rows: list[dict], context: dict) -> AnalysisResult:
        user = (
            f"Question: {question}\n\n"
            f"SQL: {sql_result.sql}\n"
            f"Source: {sql_result.source_table} ({sql_result.source_tier.value})\n\n"
            f"Result (first 20 rows):\n{rows[:20]}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}"
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
