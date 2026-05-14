## SQL

```sql
SELECT
    l_suppkey,
    SUM(order_count)   AS total_orders,
    SUM(total_revenue) AS total_revenue
FROM agg_monthly_lineitem_revenue
GROUP BY l_suppkey
ORDER BY total_orders DESC
LIMIT 5
```

**Source:** `agg_monthly_lineitem_revenue` — T1 (Gold). Supplier order count is available via `order_count` in this monthly pre-aggregated table (REV-001). Grouped by `l_suppkey` and ranked by total orders descending, limited to 5.

---

## Analysis

**Supplier #74 leads all suppliers with 702 total orders, generating $23.1M in revenue, with the top 5 suppliers ranging from 667 to 702 orders and $23M to $25.2M in revenue each.**

| Supplier Key | Total Orders | Total Revenue |
|---|---|---|
| 74 | 702 | $23,100,579.16 |
| 347 | 677 | $23,028,853.93 |
| 755 | 675 | $25,232,923.66 |
| 756 | 670 | $24,455,811.00 |
| 451 | 667 | $23,175,084.45 |

**Confidence: 90% — REV-001 metric from KPI catalog, sourced from T1 Gold table with actual data rows.**
