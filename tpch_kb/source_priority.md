# Source Priority

## Tier Mapping

### T1 — Gold Layer (Pre-aggregated)
Tables: agg_daily_lineitem_quantity, agg_monthly_lineitem_revenue, agg_daily_orders_totalprice

### T2 — Silver Layer (Facts & Dimensions)
Tables: none

### T3 — Bronze Layer (Staging)
Tables: none

## Routing Rules

- Always prefer the highest available tier
- T1 for metric lookups (pre-aggregated)
- T2 for grain-level analysis
- T3 for raw data only when T1/T2 lack coverage
