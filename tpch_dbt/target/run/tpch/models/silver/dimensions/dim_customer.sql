
  
    
    

    create  table
      "tpch"."main"."dim_customer__dbt_tmp"
  
    as (
      -- Dimension: dim_customer (SCD Type 2)
-- History tracked by snapshot: snap_customer
-- Run `dbt snapshot` before `dbt run` to populate historical records.


select
    dbt_scd_id as dim_customer_sk,
    c_custkey,
    c_name,
    c_address,
    c_nationkey,
    c_phone,
    c_acctbal,
    c_mktsegment,
    c_comment,
    dbt_valid_from as valid_from,
    dbt_valid_to as valid_to,
    (dbt_valid_to is null) as is_current
from "tpch"."snapshots"."snap_customer"
    );
  
  