# Schema Tables

## agg_daily_lineitem_quantity (T1)
Daily aggregates for line items by part and supplier

| Column | Type |
|---|---|
| daily_date | TIMESTAMP |
| l_partkey | BIGINT |
| l_suppkey | BIGINT |
| total_quantity | DECIMAL(38,2) |
| avg_quantity | DOUBLE |
| min_quantity | DECIMAL(15,2) |
| max_quantity | DECIMAL(15,2) |
| line_count | BIGINT |
| distinct_part_count | BIGINT |
| distinct_supp_count | BIGINT |

## agg_monthly_lineitem_revenue (T1)
Monthly aggregates for line items by part and supplier

| Column | Type |
|---|---|
| monthly_date | TIMESTAMP |
| l_partkey | BIGINT |
| l_suppkey | BIGINT |
| total_revenue | DECIMAL(38,4) |
| net_revenue | DECIMAL(38,6) |
| order_count | BIGINT |
| avg_discount | DOUBLE |

## agg_daily_orders_totalprice (T1)
Daily aggregates for orders by customer

| Column | Type |
|---|---|
| daily_date | TIMESTAMP |
| o_custkey | BIGINT |
| total_price | DECIMAL(38,2) |
| order_count | BIGINT |
| avg_order_price | DOUBLE |
