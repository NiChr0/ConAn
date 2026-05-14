-- Dimension: dim_partsupp (SCD Type 1)
{{ config(materialized='table') }}

select
    {{ dbt_utils.generate_surrogate_key(['ps_partkey']) }} as dim_partsupp_sk,
    ps_partkey,
    ps_suppkey,
    ps_availqty,
    ps_supplycost,
    ps_comment
from {{ ref('stg_main_partsupp') }}
