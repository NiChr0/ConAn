# SQL Edge Cases Reference

## Weighted averages on pre-aggregated columns

The most common silent error in this schema. Pre-aggregated tables store one row per time period
(day/month), where each row already summarises many underlying records. When you aggregate further
across rows, you must account for the different weights.

**Rule:** If a column name starts with `avg_` and the table has a `*_count` column, always use a
weighted average.

Pattern:
```sql
SUM(avg_column * count_column) / SUM(count_column)
```

Example — `agg_monthly_lineitem_revenue` has `avg_discount` and `order_count`:
```sql
-- Wrong: treats March (1,000 orders) the same as January (10,000 orders)
SELECT AVG(avg_discount) FROM agg_monthly_lineitem_revenue

-- Right: weights each month's average by its volume
SELECT SUM(avg_discount * order_count) / SUM(order_count) FROM agg_monthly_lineitem_revenue
```

## Empty results and date range mismatches

If a query returns no rows, the most likely cause is a date filter outside the dataset's range.
This dataset covers historical data (ending 1998). Queries filtering for "last 30 days" or
"this year" will always return empty.

When this happens, do not try a different table — tell the user the data isn't available for
that period and suggest a historical equivalent.

## Schema miss (metric not in any table)

If the user asks for a metric that requires data not present in the schema, return a literal
SELECT explaining this rather than guessing. Do not join tables hoping to reconstruct missing
data — the result will be wrong.

Example — customer repeat rate requires individual order-level data:
```sql
SELECT
    'not_available' AS status,
    'Schema has no individual order history per customer' AS reason
```

## Date granularity mismatch

Use the right table for the right granularity:
- Daily question → `agg_daily_*` tables
- Monthly question → `agg_monthly_*` tables

Joining a daily question to a monthly table loses intra-month variation and vice versa.
