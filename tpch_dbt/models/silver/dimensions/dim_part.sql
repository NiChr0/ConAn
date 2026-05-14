-- Dimension: dim_part (SCD Type 1)
{{ config(materialized='table') }}

select
    {{ dbt_utils.generate_surrogate_key(['p_partkey']) }} as dim_part_sk,
    p_partkey,
    p_name,
    p_mfgr,
    p_brand,
    p_type,
    p_size,
    p_container,
    p_retailprice,
    p_comment
from {{ ref('stg_main_part') }}
