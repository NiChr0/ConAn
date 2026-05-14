-- Fact: fct_orders
{{ config(materialized='incremental', unique_key='fct_orders_sk') }}

select
    {{ dbt_utils.generate_surrogate_key(['o_orderkey']) }} as fct_orders_sk,
    o_orderkey,
    o_custkey,
    o_orderdate,
    o_totalprice
from {{ ref('stg_main_orders') }}
{{ incremental_date_filter('o_orderdate') }}
