-- Fact: fct_orders


select
    md5(cast(coalesce(cast(o_orderkey as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as fct_orders_sk,
    o_orderkey,
    o_custkey,
    o_orderdate,
    o_totalprice
from "tpch"."main"."stg_main_orders"

    
