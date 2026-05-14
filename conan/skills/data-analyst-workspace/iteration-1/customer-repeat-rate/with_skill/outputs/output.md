## SQL

```sql
SELECT
    'not_available' AS status,
    'Schema has no customer purchase history — only aggregated order counts per customer per day' AS reason
```

**Source:** `agg_daily_orders_totalprice` — T1 (Gold)
**Reasoning:** Customer repeat order rate requires identifying individual customers who placed more than one order across distinct dates. The available T1 table (`agg_daily_orders_totalprice`) contains `o_custkey` and `order_count`, but these are pre-aggregated per customer per day — individual order-level timestamps needed to distinguish first vs. repeat orders are not available in any schema table.

---

## Analysis

**Data is not available to compute the customer repeat order rate — the schema does not expose the individual order history required to distinguish first-time from returning customers.**

The only customer-level table in the schema is `agg_daily_orders_totalprice`, which provides a daily aggregate of total spend and order count per customer. It does not preserve the timestamps or identifiers of individual orders, so it is not possible to determine whether a customer placed a second order on a different day vs. multiple line items within a single order.

To answer this question, access to `fct_orders` (the underlying Silver/Bronze source) with per-order `o_orderdate` and `o_custkey` would be needed. That table is not currently available in the schema.

**Confidence: 40% — Metric is not in the KPI catalog; the schema lacks the grain required to compute repeat rate; result is effectively unavailable.**
