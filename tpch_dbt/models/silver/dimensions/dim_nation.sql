-- Dimension: dim_nation (SCD Type 1)
{{ config(materialized='table') }}

select
    {{ dbt_utils.generate_surrogate_key(['n_nationkey']) }} as dim_nation_sk,
    n_nationkey,
    n_name,
    n_regionkey,
    n_comment
from {{ ref('stg_main_nation') }}
