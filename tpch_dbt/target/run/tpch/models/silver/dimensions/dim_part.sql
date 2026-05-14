
  
    
    

    create  table
      "tpch"."main"."dim_part__dbt_tmp"
  
    as (
      -- Dimension: dim_part (SCD Type 1)


select
    md5(cast(coalesce(cast(p_partkey as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as dim_part_sk,
    p_partkey,
    p_name,
    p_mfgr,
    p_brand,
    p_type,
    p_size,
    p_container,
    p_retailprice,
    p_comment
from "tpch"."main"."stg_main_part"
    );
  
  