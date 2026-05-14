-- Gold: agg_monthly_lineitem_revenue
-- Monthly aggregates for line items by part and supplier


select
    date_trunc('month', l_shipdate) as monthly_date,
    l_partkey,
    l_suppkey,
    sum(line_total) as total_revenue,
    sum(net_revenue) as net_revenue,
    count(*) as order_count,
    avg(l_discount) as avg_discount
from "tpch"."main"."fct_lineitem"
group by 1, 2, 3