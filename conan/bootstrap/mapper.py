from pathlib import Path
from conan.models import (
    SemanticLayer, SemanticMetric, KnowledgeBase, KPIEntry, TableSource,
    KPIMaturity, KPITier, SourceTier,
)

_DEFAULT_CONFIDENCE_CEILING = 70

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "revenue": ["revenue", "sales", "mrr", "arr", "gmv", "income", "payment"],
    "users": ["user", "customer", "subscriber", "churn", "retention", "signup"],
    "operations": ["order", "transaction", "purchase", "fulfillment", "delivery"],
    "engagement": ["session", "visit", "engagement", "click", "conversion", "view"],
}

_DOMAIN_PREFIX: dict[str, str] = {
    "revenue": "REV",
    "users": "USR",
    "operations": "OPS",
    "engagement": "ENG",
    "general": "GEN",
}


def _infer_domain(name: str) -> str:
    name_lower = name.lower()
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        if any(k in name_lower for k in keywords):
            return domain
    return "general"


def _assign_source_tier(model_name: str) -> SourceTier:
    if model_name.startswith("agg_"):
        return SourceTier.t1
    if model_name.startswith(("fct_", "dim_")):
        return SourceTier.t2
    return SourceTier.t3


def _find_source_table(metric: SemanticMetric, layer: SemanticLayer) -> str:
    measure_name = metric.type_params.get("measure", "")
    for sm in layer.semantic_models:
        if any(m.name == measure_name for m in sm.measures):
            return sm.name
    return ""


def map_semantic_layer(layer: SemanticLayer, project_name: str) -> KnowledgeBase:
    domain_counters: dict[str, int] = {}
    kpis = []

    for metric in layer.metrics:
        domain = _infer_domain(metric.name)
        domain_counters[domain] = domain_counters.get(domain, 0) + 1
        prefix = _DOMAIN_PREFIX[domain]
        metric_id = f"{prefix}-{domain_counters[domain]:03d}"
        source_table = _find_source_table(metric, layer)

        kpis.append(KPIEntry(
            id=metric_id,
            metric=metric.name,
            domain=domain,
            tier=KPITier.l2,
            maturity=KPIMaturity.directional,
            confidence_ceiling=_DEFAULT_CONFIDENCE_CEILING,
            source_table=source_table,
            description=metric.description or metric.label,
        ))

    sources = [
        TableSource(
            table_name=sm.name,
            tier=_assign_source_tier(sm.name),
            description=sm.description,
        )
        for sm in layer.semantic_models
    ]

    return KnowledgeBase(project_name=project_name, kpis=kpis, sources=sources)


def map_from_project(project_path: Path, project_name: str) -> KnowledgeBase:
    for filename in ["semantic_layer.yml", "semantic_models.yml"]:
        p = project_path / filename
        if p.exists():
            return map_semantic_layer(SemanticLayer.from_yaml_file(p), project_name)
    raise FileNotFoundError(
        f"No semantic_layer.yml or semantic_models.yml found in {project_path}"
    )
