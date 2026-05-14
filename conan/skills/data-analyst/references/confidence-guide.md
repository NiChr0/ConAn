# Confidence Scoring Guide

## The ceiling-first model

Start at the KPI catalog's `confidence_ceiling` for the metric being answered. If the metric is
not in the KPI catalog, start at 60.

This anchors the score to the known reliability of the metric before considering data quality.

## Penalties

Apply these deductions from the starting ceiling:

| Condition | Penalty |
|---|---|
| Result is empty or all nulls | −20 |
| Source is T3 (Bronze/staging) | −10 |
| SQL doesn't match a catalog-defined pattern | −10 |

## Hard caps

- Never exceed `confidence_ceiling` from the KPI catalog
- Never score above 60 for an empty or null result (regardless of source tier)

## Why ceiling-first?

An additive system (start at 50, add points for quality signals) can reach 95% for a
well-structured query that returns no data — that's misleading. Starting at the catalog ceiling
means the score reflects the metric's inherent reliability first, then degrades for data
quality problems.

## Examples

**Monthly revenue (REV-001, ceiling=90, T1 source, 12 data rows):**
- Start: 90 (catalog ceiling)
- No penalties apply
- Score: **90%**

**Daily revenue "last 30 days" (REV-001, ceiling=90, T1 source, empty result):**
- Start: 90
- −20 for empty result → 70
- Hard cap for empty results → **60%**

**Customer repeat rate (not in catalog, T1 source, not_available literal result):**
- Start: 60 (not in catalog)
- −20 for null/empty result
- Score: **40%**
