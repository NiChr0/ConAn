-- Gold: agg_daily_orders_totalprice
-- Daily aggregates for orders by customer
{{ config(materialized='table') }}

select
    date_trunc('day', o_orderdate) as daily_date,
    o_custkey,
    sum(o_totalprice) as total_price,
    count(*) as order_count,
    avg(o_totalprice) as avg_order_price
from {{ ref('fct_orders') }}
group by 1, 2
