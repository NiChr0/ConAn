-- Dimension: dim_region (SCD Type 1)
{{ config(materialized='table') }}

select
    {{ dbt_utils.generate_surrogate_key(['r_regionkey']) }} as dim_region_sk,
    r_regionkey,
    r_name,
    r_comment
from {{ ref('stg_main_region') }}
