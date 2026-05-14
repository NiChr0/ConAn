# conan/bootstrap/enricher.py
from pathlib import Path
import click
from conan.models import (
    KnowledgeBase, KPIEntry, EnrichmentSummary, EnrichmentResult,
)
from conan.llm import query_structured

_BATCH_SIZE = 5

_SYSTEM = """You are a data analyst reviewing an auto-generated KPI catalog.
Given KPI stubs and the original semantic layer context, validate and improve them:
- Promote obvious north-star/core metrics (revenue, DAU, MRR) to Validated maturity
- Assign L0 for north-star, L1 for core operational, L2 for supporting, L3 for diagnostic
- Set confidence_ceiling: Validated=85-95, Directional=60-75, Proposed=50
- Write a clear 1-2 sentence description
- Add formula if derivable from the semantic layer
- Mark metrics with no source table as Proposed
Return structured changes for every metric ID provided."""


def enrich_kb(kb: KnowledgeBase, project_path: Path) -> KnowledgeBase:
    semantic_context = _read_semantic_context(project_path)

    domains: dict[str, list[KPIEntry]] = {}
    for kpi in kb.kpis:
        domains.setdefault(kpi.domain, []).append(kpi)

    all_changes: list[EnrichmentResult] = []
    all_gaps: list[str] = []

    for domain_kpis in domains.values():
        for i in range(0, len(domain_kpis), _BATCH_SIZE):
            batch = domain_kpis[i:i + _BATCH_SIZE]
            result = _enrich_batch(batch, semantic_context)
            all_changes.extend(result.changes)
            all_gaps.extend(result.gaps)

    _print_summary(all_changes, all_gaps)
    if not click.confirm("Apply these changes?", default=True):
        return kb

    changes_by_id = {c.metric_id: c for c in all_changes}
    updated_kpis = []
    for kpi in kb.kpis:
        if kpi.id in changes_by_id:
            c = changes_by_id[kpi.id]
            updated_kpis.append(kpi.model_copy(update={
                "tier": c.tier,
                "maturity": c.maturity,
                "confidence_ceiling": c.confidence_ceiling,
                "description": c.description,
                "formula": c.formula,
                "notes": c.notes,
            }))
        else:
            updated_kpis.append(kpi)

    return kb.model_copy(update={"kpis": updated_kpis})


def _read_semantic_context(project_path: Path) -> str:
    for filename in ["semantic_layer.yml", "semantic_models.yml"]:
        p = project_path / filename
        if p.exists():
            return p.read_text()[:4000]
    return ""


def _enrich_batch(kpis: list[KPIEntry], semantic_context: str) -> EnrichmentSummary:
    stubs = "\n".join(
        f"- ID: {k.id}, Metric: {k.metric}, Domain: {k.domain}, "
        f"Source: {k.source_table or 'MISSING'}, Description: {k.description}"
        for k in kpis
    )
    return query_structured(
        system=_SYSTEM,
        user=f"KPI stubs:\n{stubs}\n\nSemantic layer:\n{semantic_context}",
        response_model=EnrichmentSummary,
        max_tokens=2048,
    )


def _print_summary(changes: list[EnrichmentResult], gaps: list[str]) -> None:
    click.echo(f"\nEnrichment: {len(changes)} changes, {len(gaps)} gaps flagged")
    for c in changes:
        click.echo(f"  {c.metric_id}: {c.maturity.value} / {c.tier.value} / {c.confidence_ceiling}% ceiling")
    for g in gaps:
        click.echo(f"  GAP: {g}")
    click.echo()
