-- Gold: agg_daily_lineitem_quantity
-- Daily aggregates for line items by part and supplier
{{ config(materialized='table') }}

select
    date_trunc('day', l_shipdate) as daily_date,
    l_partkey,
    l_suppkey,
    sum(l_quantity) as total_quantity,
    avg(l_quantity) as avg_quantity,
    min(l_quantity) as min_quantity,
    max(l_quantity) as max_quantity,
    count(*) as line_count,
    count(distinct l_partkey) as distinct_part_count,
    count(distinct l_suppkey) as distinct_supp_count
from {{ ref('fct_lineitem') }}
group by 1, 2, 3
