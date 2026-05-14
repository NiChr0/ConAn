## SQL

```sql
SELECT
    CAST(monthly_date AS DATE) AS month,
    SUM(total_revenue) AS gross_revenue,
    SUM(net_revenue) AS net_revenue,
    ROUND(SUM(net_revenue) / SUM(total_revenue) * 100, 2) AS net_pct
FROM agg_monthly_lineitem_revenue
WHERE monthly_date >= (
    SELECT MAX(monthly_date) FROM agg_monthly_lineitem_revenue
) - INTERVAL '3 months'
GROUP BY month
ORDER BY month;
```

**Source:** `agg_monthly_lineitem_revenue` | **Tier:** T1 (Gold)
**Reasoning:** Both `total_revenue` (gross) and `net_revenue` are pre-aggregated in the T1 monthly table. The WHERE clause anchors to the latest available month to define "last quarter." No lower-tier table needed.

---

## Analysis

**Net revenue was consistently ~96% of gross revenue across the last quarter, reflecting a stable ~4% discount rate with no meaningful month-to-month variation.**

| Month | Gross Revenue | Net Revenue | Net % of Gross |
|---|---|---|---|
| 1998-09-01 | $164,877,975.44 | $158,223,197.44 | 95.96% |
| 1998-10-01 | $107,210,377.91 | $102,968,607.94 | 96.04% |
| 1998-11-01 | $36,169,008.95 | $34,747,059.31 | 96.07% |
| 1998-12-01 | $91,593.37 | $87,969.19 | 96.04% |

> **Note:** December 1998 shows only $91,593 in gross revenue — roughly 1/1,800th of September's volume — indicating this is a partial month at the trailing edge of the dataset, not a full month of trading. The three complete months (Sep–Nov 1998) are the reliable basis for the ~96% net-to-gross ratio. The sharp revenue decline from Sep → Oct → Nov also suggests the dataset ends within Q4 1998, so "last quarter" here is effectively Sep–Nov 1998.

**Confidence: 90% — Both gross and net revenue are catalog-defined metrics (REV-001) from a T1 Gold table, the query matches the catalog pattern, and three of the four result rows contain full-month data.**
