-- Fact: fct_lineitem
{{ config(materialized='incremental', unique_key='fct_lineitem_sk') }}

select
    {{ dbt_utils.generate_surrogate_key(['l_orderkey']) }} as fct_lineitem_sk,
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
from {{ ref('stg_main_lineitem') }}
{{ incremental_date_filter('l_shipdate') }}
