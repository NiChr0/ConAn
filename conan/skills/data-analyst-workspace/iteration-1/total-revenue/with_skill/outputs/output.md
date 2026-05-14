## SQL

```sql
SELECT
    SUM(total_revenue) AS total_revenue,
    SUM(net_revenue)   AS total_net_revenue
FROM agg_monthly_lineitem_revenue
```

**Source:** `agg_monthly_lineitem_revenue` — T1 (Gold). Total revenue question matched to the monthly pre-aggregated revenue table (REV-001), which covers all time. Both gross and net revenue columns are surfaced for completeness.

---

## Analysis

**Total gross revenue across the full dataset is $20.54B, with net revenue (after discounts) at $19.71B — a discount impact of roughly $821M (4.0%).**

| Metric | Value |
|---|---|
| Total Gross Revenue | $20,535,072,231.42 |
| Total Net Revenue | $19,713,543,289.75 |

**Confidence: 90% — REV-001 metric from KPI catalog, sourced from T1 Gold table with actual data rows.**
