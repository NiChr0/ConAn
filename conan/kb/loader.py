import json
from pathlib import Path

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "revenue": ["revenue", "sales", "mrr", "arr", "gmv", "income", "payment"],
    "users": ["user", "customer", "subscriber", "churn", "retention"],
    "operations": ["order", "transaction", "purchase", "fulfillment"],
    "engagement": ["session", "visit", "engagement", "click", "conversion"],
}


class KBLoader:
    def __init__(self, kb_path: str | Path):
        self.kb_path = Path(kb_path)

    def load_kpis_index(self) -> str:
        return (self.kb_path / "kpis-index.md").read_text()

    def load_domain_file(self, domain: str) -> str | None:
        path = self.kb_path / f"kpis-{domain}.md"
        return path.read_text() if path.exists() else None

    def load_source_priority(self) -> str:
        return (self.kb_path / "source_priority.md").read_text()

    def load_schema(self) -> str:
        path = self.kb_path / "schema" / "tables.md"
        return path.read_text() if path.exists() else ""

    def find_saved_query(self, question: str) -> str | None:
        index_path = self.kb_path / "queries" / "index.json"
        if not index_path.exists():
            return None
        index = json.loads(index_path.read_text())
        question_lower = question.lower()
        for query in index.get("queries", []):
            if any(tag in question_lower for tag in query.get("tags", [])):
                query_file = self.kb_path / "queries" / f"{query['id']}.md"
                if query_file.exists():
                    return query_file.read_text()
        return None

    def load_for_skill(self, question: str) -> dict[str, str]:
        context: dict[str, str] = {
            "kpis_index": self.load_kpis_index(),
            "source_priority": self.load_source_priority(),
            "schema": self.load_schema(),
        }
        question_lower = question.lower()
        for domain, keywords in _DOMAIN_KEYWORDS.items():
            if any(k in question_lower for k in keywords):
                domain_content = self.load_domain_file(domain)
                if domain_content:
                    context["kpi_domain"] = domain_content
                break
        return context
