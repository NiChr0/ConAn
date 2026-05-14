from pathlib import Path
import yaml
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
            data = next(yaml.safe_load_all(p.read_text(encoding="utf-8")), None)
            if not isinstance(data, dict):
                continue
            if "semantic_models" in data or "metrics" in data:
                if _is_schemalytics_format(data):
                    return _map_from_schemalytics(data, project_name)
                return map_semantic_layer(SemanticLayer(**data), project_name)
    raise FileNotFoundError(
        f"No semantic_layer.yml or semantic_models.yml found in {project_path}"
    )


def _is_schemalytics_format(data: dict) -> bool:
    metrics = data.get("metrics", [])
    if not metrics:
        return False
    first = metrics[0] if isinstance(metrics, list) else {}
    return isinstance(first, dict) and "layer" in first


def _map_from_schemalytics(data: dict, project_name: str) -> KnowledgeBase:
    """Parse Schemalytics' rich semantic_layer.yml format into a KnowledgeBase."""
    _LAYER_TIER = {"gold": SourceTier.t1, "silver": SourceTier.t2, "facts": SourceTier.t2,
                   "dimensions": SourceTier.t2, "bronze": SourceTier.t3}

    domain_counters: dict[str, int] = {}
    kpis: list[KPIEntry] = []
    sources: list[TableSource] = []

    for entry in data.get("metrics", []):
        if not isinstance(entry, dict) or not entry.get("name"):
            continue
        name = entry["name"]
        layer = entry.get("layer", "")
        tier = _LAYER_TIER.get(layer, SourceTier.t3)
        description = entry.get("display_name") or entry.get("description") or ""
        sources.append(TableSource(table_name=name, tier=tier, description=description))

        if layer == "gold" and entry.get("source_fact"):
            domain = _infer_domain(name)
            domain_counters[domain] = domain_counters.get(domain, 0) + 1
            prefix = _DOMAIN_PREFIX.get(domain, domain[:3].upper())
            kpis.append(KPIEntry(
                id=f"{prefix}-{domain_counters[domain]:03d}",
                metric=name,
                domain=domain,
                tier=KPITier.l2,
                maturity=KPIMaturity.directional,
                confidence_ceiling=_DEFAULT_CONFIDENCE_CEILING,
                source_table=entry["source_fact"],
                description=description,
            ))

    return KnowledgeBase(project_name=project_name, kpis=kpis, sources=sources)
