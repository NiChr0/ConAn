
  
    
    

    create  table
      "tpch"."main"."dim_partsupp__dbt_tmp"
  
    as (
      -- Dimension: dim_partsupp (SCD Type 1)


select
    md5(cast(coalesce(cast(ps_partkey as TEXT), '_dbt_utils_surrogate_key_null_') as TEXT)) as dim_partsupp_sk,
    ps_partkey,
    ps_suppkey,
    ps_availqty,
    ps_supplycost,
    ps_comment
from "tpch"."main"."stg_main_partsupp"
    );
  
  