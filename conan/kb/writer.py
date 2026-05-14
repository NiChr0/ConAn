import json
import uuid
from datetime import datetime
from pathlib import Path
from conan.models import KnowledgeBase, KPIEntry, SourceTier


def write_kb(kb: KnowledgeBase, output_path: Path, connection: str | None = None) -> None:
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    (output_path / "schema").mkdir(exist_ok=True)
    (output_path / "queries").mkdir(exist_ok=True)
    (output_path / "sessions").mkdir(exist_ok=True)

    _write_kpis_index(kb, output_path)
    _write_domain_files(kb, output_path)
    _write_source_priority(kb, output_path)
    _write_schema_tables(kb, output_path, connection)
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
    domains: dict[str, list[KPIEntry]] = {}
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


def _write_schema_tables(kb: KnowledgeBase, path: Path, connection: str | None = None) -> None:
    live_columns: dict[str, list[tuple[str, str]]] = {}
    if connection:
        live_columns = _fetch_columns(connection, [s.table_name for s in kb.sources])

    lines = ["# Schema Tables\n"]
    for s in kb.sources:
        lines.append(f"\n## {s.table_name} ({s.tier.value})\n")
        if s.description:
            lines.append(f"{s.description}\n")
        cols = live_columns.get(s.table_name, [])
        if cols:
            lines.append("\n| Column | Type |\n|---|---|\n")
            for col_name, col_type in cols:
                lines.append(f"| {col_name} | {col_type} |\n")

    (path / "schema" / "tables.md").write_text("".join(lines))


def _fetch_columns(connection: str, table_names: list[str]) -> dict[str, list[tuple[str, str]]]:
    import re
    result: dict[str, list[tuple[str, str]]] = {}
    if not connection.startswith("duckdb://"):
        return result
    try:
        import duckdb
        match = re.match(r"duckdb:///(.*)$", connection)
        db_path = match.group(1) if match else ":memory:"
        conn = duckdb.connect(db_path)
        target = set(table_names)
        for (table,) in conn.execute("SELECT table_name FROM duckdb_tables()").fetchall():
            if table not in target:
                continue
            cols = conn.execute(f"PRAGMA table_info('{table}')").fetchall()
            result[table] = [(row[1], row[2]) for row in cols]
        conn.close()
    except Exception:
        pass
    return result


def _init_queries_index(path: Path) -> None:
    index_path = path / "queries" / "index.json"
    if not index_path.exists():
        index_path.write_text(json.dumps({"queries": []}, indent=2))


def log_session(kb_path: str | Path, question: str, answer: str) -> None:
    sessions_dir = Path(kb_path) / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    session_id = uuid.uuid4().hex[:8]
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f"{timestamp}-{session_id}.md"
    content = f"# Session {session_id}\n\n**Question:** {question}\n\n**Answer:**\n{answer}\n"
    (sessions_dir / filename).write_text(content)
