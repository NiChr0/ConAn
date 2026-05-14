## SQL

```sql
SELECT
    CAST(monthly_date AS DATE) AS month,
    ROUND(SUM(total_revenue) / SUM(order_count), 2) AS revenue_per_order
FROM agg_monthly_lineitem_revenue
GROUP BY month
ORDER BY month
LIMIT 24
```

**Source:** `agg_monthly_lineitem_revenue` — T1 (Gold)
**Reasoning:** Revenue per order is derived from `total_revenue` and `order_count`, both available in the T1 monthly aggregate. No lower-tier tables are needed.

---

## Analysis

**Revenue per order has been remarkably stable, holding between $33,754 and $34,648 across the first 24 months of data (Jan 1992 – Dec 1993), with no meaningful trend up or down.**

| Month | Revenue per Order |
|---|---|
| 1992-01 | $33,845.56 |
| 1992-02 | $34,105.32 |
| 1992-03 | $34,169.42 |
| 1992-04 | $33,933.48 |
| 1992-05 | $34,055.47 |
| 1992-06 | $34,381.90 |
| 1992-07 | $33,796.88 |
| 1992-08 | $34,030.43 |
| 1992-09 | $34,342.64 |
| 1992-10 | $34,648.78 |

*(Showing 10 of 24 rows — full range Jan 1992 – Dec 1993)*

**Confidence: 90% — Metric derived from validated T1 source (REV-001); SQL pattern matches catalog definition; result contains 24 data rows.**
