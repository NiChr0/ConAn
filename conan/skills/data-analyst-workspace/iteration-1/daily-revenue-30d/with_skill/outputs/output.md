## SQL

```sql
SELECT
    CAST(daily_date AS DATE) AS date,
    SUM(total_price) AS daily_revenue
FROM agg_daily_orders_totalprice
WHERE daily_date >= (
    SELECT MAX(daily_date) FROM agg_daily_orders_totalprice
) - INTERVAL '30 days'
GROUP BY date
ORDER BY date
```

**Source:** `agg_daily_orders_totalprice` — T1 (Gold). Daily question matched to daily pre-aggregated table (OPS-001). `total_price` is the correct revenue column at order grain. Filtered to the last 30 days relative to the latest available date.

---

## Analysis

**Daily revenue over the last 30 days averaged $9.19M, peaking at $10.85M on July 11 and hitting a low of $6.56M on July 30, within a dataset that runs through August 2, 1998.**

| Date | Daily Revenue |
|---|---|
| 1998-07-23 | $7,449,230.94 |
| 1998-07-24 | $9,350,836.96 |
| 1998-07-25 | $10,630,759.94 |
| 1998-07-26 | $9,204,479.39 |
| 1998-07-27 | $9,219,265.89 |
| 1998-07-28 | $8,657,292.91 |
| 1998-07-29 | $8,280,610.35 |
| 1998-07-30 | $6,562,278.59 |
| 1998-07-31 | $9,417,568.68 |
| 1998-08-01 | $8,285,111.86 |
| 1998-08-02 | $10,100,836.05 |

*(Showing 10 most recent of 31 days. Full range: 1998-07-03 to 1998-08-02.)*

**Confidence: 90% — OPS-001 metric from KPI catalog, sourced from T1 Gold table with actual data rows.**
