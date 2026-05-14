
  
    
    

    create  table
      "tpch"."main"."dim_region__dbt_tmp"
  
    as (
      -- Dimension: dim_region (SCD Type 1)


select
    md5(cast(coalesce(cast(r_regionkey as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as dim_region_sk,
    r_regionkey,
    r_name,
    r_comment
from "tpch"."main"."stg_main_region"
    );
  
  