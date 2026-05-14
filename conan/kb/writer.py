import json
import uuid
from datetime import datetime
from pathlib import Path
from conan.models import KnowledgeBase, SourceTier


def write_kb(kb: KnowledgeBase, output_path: Path) -> None:
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "schema").mkdir(exist_ok=True)
    (output_path / "queries").mkdir(exist_ok=True)
    (output_path / "sessions").mkdir(exist_ok=True)

    _write_kpis_index(kb, output_path)
    _write_domain_files(kb, output_path)
    _write_source_priority(kb, output_path)
    _write_schema_tables(kb, output_path)
    _init_queries_index(output_path)


def _write_kpis_index(kb: KnowledgeBase, path: Path) -> None:
    rows = [
        f"| {k.id} | {k.metric} | {k.domain} | {k.tier.value} | "
        f"{k.maturity.value} | {k.confidence_ceiling}% | {k.source_table} |"
        for k in kb.kpis
    ]
    content = (
        f"# KPI Index — {kb.project_name}\n\n"
        "| ID | Metric | Domain | Tier | Maturity | Confidence Ceiling | Source Table |\n"
        "|---|---|---|---|---|---|---|\n"
        + "\n".join(rows) + "\n"
    )
    (path / "kpis-index.md").write_text(content)


def _write_domain_files(kb: KnowledgeBase, path: Path) -> None:
    domains: dict[str, list] = {}
    for kpi in kb.kpis:
        domains.setdefault(kpi.domain, []).append(kpi)

    for domain, kpis in domains.items():
        lines = [f"# KPIs — {domain.title()}\n"]
        for kpi in kpis:
            lines += [
                f"\n## {kpi.id}: {kpi.metric}\n",
                f"**Tier:** {kpi.tier.value}  \n",
                f"**Maturity:** {kpi.maturity.value}  \n",
                f"**Confidence Ceiling:** {kpi.confidence_ceiling}%  \n",
                f"**Source Table:** {kpi.source_table}  \n",
                f"**Description:** {kpi.description}  \n",
                f"**Formula:** {kpi.formula}  \n",
                f"**Notes:** {kpi.notes}  \n",
            ]
        (path / f"kpis-{domain}.md").write_text("".join(lines))


def _write_source_priority(kb: KnowledgeBase, path: Path) -> None:
    t1 = [s.table_name for s in kb.sources if s.tier == SourceTier.t1]
    t2 = [s.table_name for s in kb.sources if s.tier == SourceTier.t2]
    t3 = [s.table_name for s in kb.sources if s.tier == SourceTier.t3]

    content = (
        "# Source Priority\n\n"
        "## Tier Mapping\n\n"
        f"### T1 — Gold Layer (Pre-aggregated)\nTables: {', '.join(t1) or 'none'}\n\n"
        f"### T2 — Silver Layer (Facts & Dimensions)\nTables: {', '.join(t2) or 'none'}\n\n"
        f"### T3 — Bronze Layer (Staging)\nTables: {', '.join(t3) or 'none'}\n\n"
        "## Routing Rules\n\n"
        "- Always prefer the highest available tier\n"
        "- T1 for metric lookups (pre-aggregated)\n"
        "- T2 for grain-level analysis\n"
        "- T3 for raw data only when T1/T2 lack coverage\n"
    )
    (path / "source_priority.md").write_text(content)


def _write_schema_tables(kb: KnowledgeBase, path: Path) -> None:
    rows = [
        f"| {s.table_name} | {s.tier.value} | {s.description} |"
        for s in kb.sources
    ]
    content = (
        "# Schema Tables\n\n"
        "| Table | Tier | Description |\n"
        "|---|---|---|\n"
        + "\n".join(rows) + "\n"
    )
    (path / "schema" / "tables.md").write_text(content)


def _init_queries_index(path: Path) -> None:
    index_path = path / "queries" / "index.json"
    if not index_path.exists():
        index_path.write_text(json.dumps({"queries": []}, indent=2))


def log_session(kb_path: str | Path, question: str, answer: str) -> None:
    session_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{session_id}.md"
    content = f"# Session {session_id}\n\n**Question:** {question}\n\n**Answer:**\n{answer}\n"
    (Path(kb_path) / "sessions" / filename).write_text(content)
