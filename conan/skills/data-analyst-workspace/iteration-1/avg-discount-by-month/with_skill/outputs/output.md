## SQL

```sql
SELECT
    CAST(monthly_date AS DATE) AS month,
    ROUND(AVG(avg_discount) * 100, 2) AS avg_discount_pct
FROM agg_monthly_lineitem_revenue
GROUP BY month
ORDER BY month
LIMIT 24;
```

**Source:** `agg_monthly_lineitem_revenue` | **Tier:** T1 (Gold)
**Reasoning:** Monthly granularity maps directly to `agg_monthly_lineitem_revenue`; `avg_discount` is a pre-aggregated column. Multiplied by 100 to express as a percentage.

---

## Analysis

**The average discount rate has been almost perfectly flat at ~5.0% every month, with no meaningful trend or seasonal variation across the full 24-month window.**

| Month | Avg Discount % |
|---|---|
| 1993-03-01 | 5.09% |
| 1993-04-01 | 5.03% |
| 1993-05-01 | 5.01% |
| 1993-06-01 | 5.05% |
| 1993-07-01 | 4.99% |
| 1993-08-01 | 5.00% |
| 1993-09-01 | 4.99% |
| 1993-10-01 | 4.99% |
| 1993-11-01 | 4.99% |
| 1993-12-01 | 5.01% |

*Showing the 10 most recent months of the 24-month window (Jan 1992 – Dec 1993). The full range across all 24 months is 4.97%–5.09% — a spread of only 12 basis points — indicating a fixed or tightly controlled discount policy.*

**Confidence: 90% — Source is T1 Gold table aligned with catalog entry REV-001, query matches the catalog pattern, and result contains 24 months of actual data.**
