# conan/skills/product_analyst.py
from pathlib import Path
from conan.skills.base import SkillBase
from conan.models import (
    DiagnosticQueries, AnalysisResult, SkillResult, OrchestratorDispatch,
)
from conan.executor import ExecutorError
from conan.llm import query_structured

_SKILL_DIR = Path(__file__).parent / "product-analyst"
_SYSTEM_DECOMPOSE = (_SKILL_DIR / "decompose.md").read_text()
_SYSTEM_SYNTHESIZE = (_SKILL_DIR / "synthesize.md").read_text()


class ProductAnalystSkill(SkillBase):
    name = "product-analyst"
    description = "Root cause analysis, anomaly diagnosis, why-did-X-change questions"

    def run(self, question: str, dispatch: OrchestratorDispatch) -> SkillResult:
        context = self.kb_loader.load_for_skill(question)
        diagnostic = self._decompose(question, context)

        results = []
        for q in diagnostic.queries:
            try:
                rows = self.executor.execute(q.sql)
                results.append({"sql": q.sql, "source": q.source_table, "rows": rows[:20]})
            except ExecutorError as e:
                results.append({"sql": q.sql, "error": str(e)})

        if all("error" in r for r in results):
            return SkillResult(
                answer=(
                    "Could not diagnose — all diagnostic queries failed due to data access errors. "
                    "Check that the required tables are available in the schema."
                ),
                sql=diagnostic.queries[0].sql if diagnostic.queries else None,
                source_table=None,
                source_tier=None,
                confidence=20,
                confidence_justification="All diagnostic queries failed; no data available.",
            )

        analysis = self._synthesize(question, results, context)
        primary = diagnostic.queries[0] if diagnostic.queries else None

        return SkillResult(
            answer=analysis.answer,
            sql=primary.sql if primary else None,
            source_table=primary.source_table if primary else None,
            source_tier=primary.source_tier if primary else None,
            confidence=analysis.confidence,
            confidence_justification=analysis.confidence_justification,
        )

    def _decompose(self, question: str, context: dict) -> DiagnosticQueries:
        domain_section = f"\nDomain KPIs:\n{context['kpi_domain']}" if "kpi_domain" in context else ""
        user = (
            f"Question: {question}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}\n\n"
            f"Source Priority:\n{context.get('source_priority', '')}\n\n"
            f"Schema:\n{context.get('schema', '')}"
            f"{domain_section}\n\n"
            "Generate 2-3 diagnostic SQL queries to investigate this question."
        )
        return query_structured(_SYSTEM_DECOMPOSE, user, DiagnosticQueries, model=self.model, max_tokens=2048)

    def _synthesize(self, question: str, results: list[dict], context: dict) -> AnalysisResult:
        user = (
            f"Question: {question}\n\n"
            f"Diagnostic results:\n{results}\n\n"
            f"KPI Index:\n{context.get('kpis_index', '')}"
        )
        return query_structured(_SYSTEM_SYNTHESIZE, user, AnalysisResult, model=self.model, max_tokens=2048)
