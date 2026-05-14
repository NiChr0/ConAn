
  
    
    

    create  table
      "tpch"."main"."dim_nation__dbt_tmp"
  
    as (
      -- Dimension: dim_nation (SCD Type 1)


select
    md5(cast(coalesce(cast(n_nationkey as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as dim_nation_sk,
    n_nationkey,
    n_name,
    n_regionkey,
    n_comment
from "tpch"."main"."stg_main_nation"
    );
  
  