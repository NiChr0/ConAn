## SQL

```sql
SELECT
    CAST(monthly_date AS DATE) AS month,
    SUM(total_revenue) AS revenue,
    SUM(order_count) AS orders
FROM agg_monthly_lineitem_revenue
GROUP BY month
ORDER BY month
LIMIT 24;
```

**Source:** `agg_monthly_lineitem_revenue` | **Tier:** T1 (Gold)
**Reasoning:** Monthly granularity matches the `agg_monthly_lineitem_revenue` T1 table directly; `total_revenue` and `order_count` are pre-aggregated columns. No lower-tier table needed.

---

## Analysis

**Revenue has been broadly stable at ~$250–270M/month since mid-1992, after ramping up sharply through the first five months of the dataset.**

| Month | Revenue | Orders |
|---|---|---|
| 1993-03-01 | $256,662,903.16 | 7,499 |
| 1993-04-01 | $254,501,820.37 | 7,444 |
| 1993-05-01 | $258,300,206.02 | 7,473 |
| 1993-06-01 | $253,769,752.21 | 7,433 |
| 1993-07-01 | $265,967,862.39 | 7,714 |
| 1993-08-01 | $260,310,126.27 | 7,648 |
| 1993-09-01 | $246,740,202.53 | 7,310 |
| 1993-10-01 | $262,763,957.88 | 7,677 |
| 1993-11-01 | $243,869,264.84 | 7,106 |
| 1993-12-01 | $262,367,547.95 | 7,653 |

*Showing the 10 most recent months of the 24-month window (Jan 1992 – Dec 1993). Jan 1992 ($32.8M) and Feb 1992 ($91.5M) are partial-ramp months as the dataset begins; from May 1992 onward revenue stabilises in the $245–270M band.*

**Confidence: 90% — Metric is catalog-defined (REV-001), sourced from T1 Gold table, and the query matches the catalog pattern exactly.**
