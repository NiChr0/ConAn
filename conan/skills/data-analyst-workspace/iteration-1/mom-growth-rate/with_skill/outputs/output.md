## SQL

```sql
WITH monthly AS (
    SELECT
        CAST(monthly_date AS DATE) AS month,
        SUM(total_revenue) AS revenue
    FROM agg_monthly_lineitem_revenue
    GROUP BY month
),
with_prev AS (
    SELECT
        month,
        revenue,
        LAG(revenue) OVER (ORDER BY month) AS prev_revenue
    FROM monthly
)
SELECT
    month,
    ROUND(revenue, 2) AS revenue,
    ROUND((revenue - prev_revenue) / prev_revenue * 100, 2) AS mom_growth_pct
FROM with_prev
WHERE prev_revenue IS NOT NULL
ORDER BY month
LIMIT 24
```

**Source:** `agg_monthly_lineitem_revenue` — T1 (Gold)
**Reasoning:** Month-over-month growth requires monthly revenue totals with a lagged comparison. The T1 monthly aggregate provides `total_revenue` at the right granularity; a window function computes the rate.

---

## Analysis

**After a sharp ramp-up in early 1992 (dataset start), month-over-month revenue growth stabilized into a narrow oscillating band of roughly −10% to +10%, with no sustained directional trend through early 1994.**

| Month | Revenue | MoM Growth % |
|---|---|---|
| 1992-02 | $91,504,579.04 | +179.30% |
| 1992-03 | $169,856,168.69 | +85.63% |
| 1992-04 | $225,555,869.65 | +32.79% |
| 1992-05 | $264,883,459.28 | +17.44% |
| 1992-06 | $261,061,789.94 | −1.44% |
| 1992-07 | $270,172,232.84 | +3.49% |
| 1992-08 | $266,764,570.65 | −1.26% |
| 1992-09 | $255,474,884.16 | −4.23% |
| 1992-10 | $265,478,927.34 | +3.92% |
| 1992-11 | $254,985,758.79 | −3.95% |

*(Showing 10 of 24 rows — full range Feb 1992 – Jan 1994)*

> Note: The Feb 1992 (+179%) and Mar 1992 (+86%) figures reflect the dataset ramping up from a partial first month, not genuine business growth. The signal stabilises from mid-1992 onward.

**Confidence: 90% — Metric derived from validated T1 source (REV-001); LAG-based MoM pattern matches catalog definition; result contains 24 data rows.**
