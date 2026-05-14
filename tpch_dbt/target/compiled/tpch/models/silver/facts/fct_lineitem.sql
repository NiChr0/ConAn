-- Fact: fct_lineitem


select
    md5(cast(coalesce(cast(l_orderkey as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as fct_lineitem_sk,
    l_orderkey,
    l_partkey,
    l_suppkey,
    l_shipdate,
    l_quantity,
    l_extendedprice,
    l_discount,
    l_tax,
    l_extendedprice * (1 - l_discount) as line_total,
    l_extendedprice * (1 - l_discount) * (1 - l_tax) as net_revenue,
    l_commitdate,
    l_receiptdate
from "tpch"."main"."stg_main_lineitem"

    
