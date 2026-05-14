
  
    
    

    create  table
      "tpch"."main"."dim_supplier__dbt_tmp"
  
    as (
      -- Dimension: dim_supplier (SCD Type 2)
-- History tracked by snapshot: snap_supplier
-- Run `dbt snapshot` before `dbt run` to populate historical records.


select
    dbt_scd_id as dim_supplier_sk,
    s_suppkey,
    s_name,
    s_address,
    s_nationkey,
    s_phone,
    s_acctbal,
    s_comment,
    dbt_valid_from as valid_from,
    dbt_valid_to as valid_to,
    (dbt_valid_to is null) as is_current
from "tpch"."snapshots"."snap_supplier"
    );
  
  